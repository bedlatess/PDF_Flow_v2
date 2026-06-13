import type { AdminFeedback } from '@/admin/api'
import { buildFeedbackSummary, buildHealthReportSummary as buildHealthSummary } from './summaries'
import type { ControlRoomContext } from './context'

const copiedDelayMs = 1800

export const createControlRoomClipboard = (ctx: ControlRoomContext) => {
  const buildHealthReportSummary = () =>
    buildHealthSummary(ctx.healthReport.value, {
      appVersion: import.meta.env.VITE_APP_VERSION || 'frontend-build',
      pageUrl: window.location.href,
    })

  const copyWithState = async (
    text: string | undefined,
    copiedState: { value: boolean },
    successMessage: string,
    emptyMessage: string,
    failureMessage: string,
  ) => {
    if (!text) {
      ctx.error.value = emptyMessage
      return
    }

    try {
      await navigator.clipboard?.writeText(text)
      copiedState.value = true
      ctx.setMessage(successMessage)
      window.setTimeout(() => {
        copiedState.value = false
      }, copiedDelayMs)
    } catch {
      ctx.error.value = failureMessage
    }
  }

  const copyFeedbackSummary = async (report: AdminFeedback) => {
    try {
      await navigator.clipboard?.writeText(buildFeedbackSummary(report))
      ctx.copiedFeedbackId.value = report.id
      ctx.setMessage(`已复制反馈 #${report.id} 摘要`)
      window.setTimeout(() => {
        if (ctx.copiedFeedbackId.value === report.id) {
          ctx.copiedFeedbackId.value = null
        }
      }, copiedDelayMs)
    } catch {
      ctx.error.value = '复制失败，请手动选中反馈内容复制。'
    }
  }

  const copyHealthReport = () =>
    copyWithState(
      buildHealthReportSummary(),
      ctx.healthReportCopied,
      '已复制上线健康报告',
      '健康报告还没有加载完成，请先刷新。',
      '复制健康报告失败，请手动选中报告内容复制。',
    )

  const copyDiagnosticSummary = () =>
    copyWithState(
      ctx.diagnostics.value?.diagnostic_summary,
      ctx.diagnosticSummaryCopied,
      '已复制诊断排障包',
      '诊断摘要还没有加载完成，请先刷新。',
      '复制诊断排障包失败，请手动选中摘要内容复制。',
    )

  const copyReconciliationSummary = () =>
    copyWithState(
      ctx.paymentSummary.value?.reconciliation_summary,
      ctx.reconciliationCopied,
      '已复制支付对账包',
      '支付对账摘要还没有加载完成，请先刷新。',
      '复制支付对账包失败，请手动选中摘要内容复制。',
    )

  const copyPaymentEvidencePacket = () =>
    copyWithState(
      ctx.paymentSummary.value?.integration_evidence_packet,
      ctx.evidenceCopied,
      '已复制支付联调证据包',
      '支付联调证据包还没有加载完成，请先刷新。',
      '复制支付联调证据包失败，请手动选中摘要内容复制。',
    )

  return {
    buildHealthReportSummary,
    copyFeedbackSummary,
    copyHealthReport,
    copyDiagnosticSummary,
    copyReconciliationSummary,
    copyPaymentEvidencePacket,
  }
}
