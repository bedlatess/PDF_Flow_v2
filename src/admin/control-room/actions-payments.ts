import { adminAPI } from '@/admin/api'
import type { AdminPricingPlan } from '@/admin/api'
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

  const savePricingPlan = async (plan: AdminPricingPlan) => {
    ctx.savingKey.value = `pricing:${plan.plan_key}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updatePricingPlan(plan.plan_key, {
        plan_key: plan.plan_key,
        display_name: plan.display_name,
        is_public: plan.is_public,
        price_amount_cents: Number(plan.price_amount_cents || 0),
        display_price: plan.display_price,
        currency: plan.currency,
        billing_interval: plan.billing_interval,
        description: plan.description,
        provider_mappings: {
          stripe: {
            price_id: plan.provider_mappings.stripe.price_id || '',
          },
          paypal: {
            plan_id: plan.provider_mappings.paypal.plan_id || '',
            product_id: plan.provider_mappings.paypal.product_id || '',
          },
          gmpay: {
            amount_cents: Number(plan.provider_mappings.gmpay.amount_cents || 0),
            currency: plan.provider_mappings.gmpay.currency || 'CNY',
            token: plan.provider_mappings.gmpay.token || 'usdt',
            network: plan.provider_mappings.gmpay.network || 'tron',
          },
        },
        sort_order: Number(plan.sort_order || 0),
        highlighted: plan.highlighted,
      })
      const index = ctx.pricingPlans.value.findIndex((item) => item.plan_key === updated.plan_key)
      if (index >= 0) ctx.pricingPlans.value[index] = updated
      ctx.auditLogs.value = await adminAPI.listAuditLogs()
      ctx.setMessage(`Saved pricing plan: ${updated.display_name}`)
    } catch {
      ctx.error.value = 'Pricing plan save failed. Check price, currency, and provider mapping before retrying.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    loadPayments,
    savePricingPlan,
  }
}
