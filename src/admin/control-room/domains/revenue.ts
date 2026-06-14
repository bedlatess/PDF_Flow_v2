import { formatAdminDate, formatAdminMoney } from '../formatters'
import type { ControlRoomDomainDeps } from './types'

export const createRevenueDomain = ({ ctx, actions, clipboard }: ControlRoomDomainDeps) => ({
  state: {
    paymentSummary: ctx.paymentSummary,
    paymentProviderFilter: ctx.paymentProviderFilter,
    paymentStatusFilter: ctx.paymentStatusFilter,
    reconciliationCopied: ctx.reconciliationCopied,
    evidenceCopied: ctx.evidenceCopied,
    savingKey: ctx.savingKey,
  },
  actions: {
    loadPayments: actions.loadPayments,
    copyReconciliationSummary: clipboard.copyReconciliationSummary,
    copyPaymentEvidencePacket: clipboard.copyPaymentEvidencePacket,
  },
  helpers: {
    formatDate: formatAdminDate,
    formatMoney: formatAdminMoney,
  },
})
