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
      ctx.setMessage(`Copied feedback #${report.id} summary`)
      window.setTimeout(() => {
        if (ctx.copiedFeedbackId.value === report.id) {
          ctx.copiedFeedbackId.value = null
        }
      }, copiedDelayMs)
    } catch {
      ctx.error.value = 'Copy failed. Select the feedback content manually and copy it.'
    }
  }

  const copyHealthReport = () =>
    copyWithState(
      buildHealthReportSummary(),
      ctx.healthReportCopied,
      'Copied health report',
      'Health report has not loaded yet. Refresh first.',
      'Health report copy failed. Select the report content manually and copy it.',
    )

  const copyDiagnosticSummary = () =>
    copyWithState(
      ctx.diagnostics.value?.diagnostic_summary,
      ctx.diagnosticSummaryCopied,
      'Copied diagnostic packet',
      'Diagnostic summary has not loaded yet. Refresh first.',
      'Diagnostic packet copy failed. Select the summary content manually and copy it.',
    )

  const copyReconciliationSummary = () =>
    copyWithState(
      ctx.paymentSummary.value?.reconciliation_summary,
      ctx.reconciliationCopied,
      'Copied reconciliation packet',
      'Payment reconciliation summary has not loaded yet. Refresh first.',
      'Reconciliation packet copy failed. Select the summary content manually and copy it.',
    )

  const copyPaymentEvidencePacket = () =>
    copyWithState(
      ctx.paymentSummary.value?.integration_evidence_packet,
      ctx.evidenceCopied,
      'Copied payment evidence packet',
      'Payment evidence packet has not loaded yet. Refresh first.',
      'Payment evidence packet copy failed. Select the summary content manually and copy it.',
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
