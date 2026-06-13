import { adminAPI, type AdminFeedback } from '@/admin/api'
import type { ControlRoomContext } from './context'

export const createControlRoomFeedbackActions = (ctx: ControlRoomContext) => {
  const loadFeedback = async () => {
    ctx.savingKey.value = 'feedback:refresh'
    ctx.error.value = ''

    try {
      ctx.feedbackReports.value = await adminAPI.listFeedback({
        status_filter: ctx.feedbackStatusFilter.value || undefined,
      })
      ctx.overview.value = await adminAPI.getOverview()
    } catch {
      ctx.error.value = 'Feedback failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const saveFeedback = async (report: AdminFeedback) => {
    ctx.savingKey.value = `feedback:${report.id}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateFeedback(report.id, {
        status: report.status,
        admin_note: report.admin_note,
      })
      const index = ctx.feedbackReports.value.findIndex((item) => item.id === updated.id)
      if (index >= 0) ctx.feedbackReports.value[index] = updated
      const [overviewData, diagnosticsData, auditData] = await Promise.all([
        adminAPI.getOverview(),
        adminAPI.getDiagnostics(),
        adminAPI.listAuditLogs(),
      ])
      ctx.overview.value = overviewData
      ctx.diagnostics.value = diagnosticsData
      ctx.apiErrors.value = diagnosticsData.recent_errors
      ctx.auditLogs.value = auditData
      ctx.setMessage(`Updated feedback #${updated.id}`)
    } catch {
      ctx.error.value = 'Feedback status save failed. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const cleanupLiveAcceptanceFeedback = async () => {
    ctx.savingKey.value = 'feedback:cleanup-live'
    ctx.error.value = ''

    try {
      const result = await adminAPI.cleanupLiveAcceptanceFeedback()
      const [
        feedbackData,
        overviewData,
        diagnosticsData,
        healthReportData,
        maintenanceData,
        auditData,
      ] = await Promise.all([
        adminAPI.listFeedback({
          status_filter: ctx.feedbackStatusFilter.value || undefined,
        }),
        adminAPI.getOverview(),
        adminAPI.getDiagnostics(),
        adminAPI.getHealthReport(),
        adminAPI.getMaintenance(),
        adminAPI.listAuditLogs(),
      ])
      ctx.feedbackReports.value = feedbackData
      ctx.overview.value = overviewData
      ctx.diagnostics.value = diagnosticsData
      ctx.apiErrors.value = diagnosticsData.recent_errors
      ctx.healthReport.value = healthReportData
      ctx.maintenance.value = maintenanceData
      ctx.auditLogs.value = auditData
      ctx.setMessage(
        `已关闭 ${result.closed_count} 条验收反馈，剩余待处理 ${result.remaining_open_count} 条`,
      )
    } catch {
      ctx.error.value = 'Acceptance feedback cleanup failed. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    loadFeedback,
    saveFeedback,
    cleanupLiveAcceptanceFeedback,
  }
}
