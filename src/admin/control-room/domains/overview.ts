import { formatAdminDate } from '../formatters'
import type { ControlRoomDomainDeps } from './types'

export const createOverviewDomain = ({ ctx, actions, clipboard }: ControlRoomDomainDeps) => ({
  state: {
    overview: ctx.overview,
    operations: ctx.operations,
    jobs: ctx.jobs,
    healthReport: ctx.healthReport,
    healthReportCopied: ctx.healthReportCopied,
    savingKey: ctx.savingKey,
  },
  actions: {
    loadAdminData: actions.loadAdminData,
    loadHealthReport: actions.loadHealthReport,
    copyHealthReport: clipboard.copyHealthReport,
  },
  helpers: {
    formatDate: formatAdminDate,
    buildHealthReportSummary: clipboard.buildHealthReportSummary,
  },
})
