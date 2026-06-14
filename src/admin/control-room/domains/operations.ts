import { formatAdminDate, parseAdminDiagnostics } from '../formatters'
import type { ControlRoomDomainDeps } from './types'

export const createOperationsDomain = ({ ctx, actions, clipboard }: ControlRoomDomainDeps) => ({
  state: {
    operations: ctx.operations,
    jobs: ctx.jobs,
    filteredJobs: ctx.filteredJobs,
    jobSearch: ctx.jobSearch,
    jobStatusFilter: ctx.jobStatusFilter,
    feedbackReports: ctx.feedbackReports,
    feedbackStatusFilter: ctx.feedbackStatusFilter,
    highlightedFeedbackId: ctx.highlightedFeedbackId,
    copiedFeedbackId: ctx.copiedFeedbackId,
    apiErrors: ctx.apiErrors,
    diagnostics: ctx.diagnostics,
    diagnosticSummaryCopied: ctx.diagnosticSummaryCopied,
    maintenance: ctx.maintenance,
    savingKey: ctx.savingKey,
  },
  actions: {
    loadJobs: actions.loadJobs,
    loadFeedback: actions.loadFeedback,
    saveFeedback: actions.saveFeedback,
    cleanupLiveAcceptanceFeedback: actions.cleanupLiveAcceptanceFeedback,
    loadDiagnostics: actions.loadDiagnostics,
    openFeedbackFromDiagnostics: actions.openFeedbackFromDiagnostics,
    refreshMaintenance: actions.refreshMaintenance,
    cleanupTestUsers: actions.cleanupTestUsers,
    cleanupExpiredFiles: actions.cleanupExpiredFiles,
    copyFeedbackSummary: clipboard.copyFeedbackSummary,
    copyDiagnosticSummary: clipboard.copyDiagnosticSummary,
  },
  helpers: {
    formatDate: formatAdminDate,
    parseDiagnostics: parseAdminDiagnostics,
  },
})
