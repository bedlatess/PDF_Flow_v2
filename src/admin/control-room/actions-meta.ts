import { adminAPI } from '@/admin/api'
import type { ControlRoomContext } from './context'

export const createControlRoomMetaActions = (ctx: ControlRoomContext) => {
  const refreshAdminMeta = async () => {
    const [overviewData, operationsData, healthReportData, maintenanceData, auditData] =
      await Promise.all([
        adminAPI.getOverview(),
        adminAPI.getOperations(),
        adminAPI.getHealthReport(),
        adminAPI.getMaintenance(),
        adminAPI.listAuditLogs(),
      ])
    ctx.overview.value = overviewData
    ctx.operations.value = operationsData
    ctx.healthReport.value = healthReportData
    ctx.maintenance.value = maintenanceData
    ctx.auditLogs.value = auditData
  }

  const loadHealthReport = async () => {
    ctx.savingKey.value = 'health-report:refresh'
    ctx.error.value = ''

    try {
      ctx.healthReport.value = await adminAPI.getHealthReport()
    } catch {
      ctx.error.value = 'Health report failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const loadAdminData = async () => {
    ctx.loading.value = true
    ctx.error.value = ''

    try {
      const [
        overviewData,
        operationsData,
        settingsData,
        flagsData,
        contentData,
        usersData,
        jobsData,
        feedbackData,
        paymentData,
        pricingPlansData,
        ocrProviderData,
        officeProviderData,
        aiProviderData,
        diagnosticsData,
        healthReportData,
        maintenanceData,
        auditData,
      ] = await Promise.all([
        adminAPI.getOverview(),
        adminAPI.getOperations(),
        adminAPI.listSettings(),
        adminAPI.listFeatureFlags(),
        adminAPI.listContentBlocks(),
        adminAPI.listUsers(),
        adminAPI.listJobs(),
        adminAPI.listFeedback(),
        adminAPI.getPaymentSummary(),
        adminAPI.listPricingPlans(),
        adminAPI.listServiceProviderConfigs('ocr'),
        adminAPI.listServiceProviderConfigs('office'),
        adminAPI.listServiceProviderConfigs('ai'),
        adminAPI.getDiagnostics(),
        adminAPI.getHealthReport(),
        adminAPI.getMaintenance(),
        adminAPI.listAuditLogs(),
      ])

      ctx.overview.value = overviewData
      ctx.operations.value = operationsData
      ctx.settings.value = settingsData
      ctx.flags.value = flagsData
      ctx.contentBlocks.value = contentData
      ctx.users.value = usersData
      ctx.jobs.value = jobsData
      ctx.feedbackReports.value = feedbackData
      ctx.paymentSummary.value = paymentData
      ctx.pricingPlans.value = pricingPlansData
      ctx.serviceProviderConfigs.value = [...ocrProviderData, ...officeProviderData, ...aiProviderData]
      ctx.diagnostics.value = diagnosticsData
      ctx.healthReport.value = healthReportData
      ctx.maintenance.value = maintenanceData
      ctx.apiErrors.value = diagnosticsData.recent_errors
      ctx.auditLogs.value = auditData
      ctx.selectedContent.value = contentData[0] ?? null
    } catch (err: any) {
      ctx.error.value =
        err?.response?.status === 403
          ? 'Current account does not have admin access.'
          : 'Admin data failed to load. Please retry later or check backend logs.'
    } finally {
      ctx.loading.value = false
    }
  }

  return {
    refreshAdminMeta,
    loadHealthReport,
    loadAdminData,
  }
}
