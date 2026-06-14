import { createControlRoomDiagnosticsActions } from './actions-diagnostics'
import { createControlRoomFeedbackActions } from './actions-feedback'
import { createControlRoomJobsActions } from './actions-jobs'
import { createControlRoomMaintenanceActions } from './actions-maintenance'
import { createControlRoomMetaActions } from './actions-meta'
import { createControlRoomPaymentsActions } from './actions-payments'
import { createControlRoomSettingsActions } from './actions-settings'
import { createControlRoomUsersActions } from './actions-users'
import type { ControlRoomContext } from './context'

export const createControlRoomActions = (ctx: ControlRoomContext) => {
  const meta = createControlRoomMetaActions(ctx)
  const settings = createControlRoomSettingsActions(ctx)
  const users = createControlRoomUsersActions(ctx, {
    refreshAdminMeta: meta.refreshAdminMeta,
  })
  const jobs = createControlRoomJobsActions(ctx)
  const payments = createControlRoomPaymentsActions(ctx)
  const feedback = createControlRoomFeedbackActions(ctx)
  const maintenance = createControlRoomMaintenanceActions(ctx, {
    refreshAdminMeta: meta.refreshAdminMeta,
  })
  const diagnostics = createControlRoomDiagnosticsActions(ctx, {
    loadFeedback: feedback.loadFeedback,
  })

  return {
    loadHealthReport: meta.loadHealthReport,
    loadAdminData: meta.loadAdminData,
    saveFlag: settings.saveFlag,
    saveSetting: settings.saveSetting,
    saveContentBlock: settings.saveContentBlock,
    searchUsers: users.searchUsers,
    saveUser: users.saveUser,
    toggleUserBan: users.toggleUserBan,
    createPasswordResetLink: users.createPasswordResetLink,
    deleteUser: users.deleteUser,
    loadJobs: jobs.loadJobs,
    loadPayments: payments.loadPayments,
    savePricingPlan: payments.savePricingPlan,
    loadFeedback: feedback.loadFeedback,
    saveFeedback: feedback.saveFeedback,
    cleanupLiveAcceptanceFeedback: feedback.cleanupLiveAcceptanceFeedback,
    refreshMaintenance: maintenance.refreshMaintenance,
    cleanupTestUsers: maintenance.cleanupTestUsers,
    cleanupExpiredFiles: maintenance.cleanupExpiredFiles,
    openFeedbackFromDiagnostics: diagnostics.openFeedbackFromDiagnostics,
    loadDiagnostics: diagnostics.loadDiagnostics,
  }
}
