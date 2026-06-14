import { formatAdminDate } from '../formatters'
import type { ControlRoomDomainDeps } from './types'

export const createSecurityDomain = ({ ctx }: ControlRoomDomainDeps) => ({
  state: {
    auditLogs: ctx.auditLogs,
    pendingConfirmation: ctx.pendingConfirmation,
    savingKey: ctx.savingKey,
  },
  actions: {
    closeAdminConfirmation: ctx.closeAdminConfirmation,
    confirmAdminAction: ctx.confirmAdminAction,
  },
  helpers: {
    formatDate: formatAdminDate,
  },
})
