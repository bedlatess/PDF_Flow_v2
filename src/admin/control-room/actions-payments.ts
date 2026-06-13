import { adminAPI } from '@/admin/api'
import type { ControlRoomContext } from './context'

export const createControlRoomPaymentsActions = (ctx: ControlRoomContext) => {
  const loadPayments = async () => {
    ctx.savingKey.value = 'payments:refresh'
    ctx.error.value = ''

    try {
      ctx.paymentSummary.value = await adminAPI.getPaymentSummary({
        provider: ctx.paymentProviderFilter.value || undefined,
        status_filter: ctx.paymentStatusFilter.value || undefined,
      })
    } catch {
      ctx.error.value = 'Payment reconciliation data failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    loadPayments,
  }
}
