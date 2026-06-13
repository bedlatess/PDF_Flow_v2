export type EntitlementRole = 'free' | 'pro' | 'enterprise' | 'admin' | string
export type EntitlementTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

const ACTIVE_STATUSES = new Set(['active', 'manual', 'trialing', 'cancel_at_period_end'])

type EntitlementAccount = {
  role?: EntitlementRole | null
  subscription_status?: string | null
  subscription_end_date?: string | null
}

export type EntitlementSummary = {
  label: string
  detail: string
  statusLabel: string
  tone: EntitlementTone
  isActive: boolean
  isExpired: boolean
}

const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))

const normalizeStatus = (value?: string | null) => value?.trim().toLowerCase() || ''

const statusLabel = (status: string) => {
  if (status === 'manual') return 'Manual'
  if (status === 'active') return 'Active'
  if (status === 'trialing') return 'Trial'
  if (status === 'cancel_at_period_end') return 'Canceling'
  if (status === 'expired') return 'Expired'
  if (status === 'canceled') return 'Canceled'
  return 'No subscription'
}

export const getEntitlementSummary = (account: EntitlementAccount): EntitlementSummary => {
  const role = account.role || 'free'
  const status = normalizeStatus(account.subscription_status)
  const endDate = account.subscription_end_date || ''
  const endTime = endDate ? new Date(endDate).getTime() : Number.NaN
  const hasEndDate = endDate && !Number.isNaN(endTime)
  const isPastEndDate = hasEndDate ? endTime <= Date.now() : false

  if (role === 'admin') {
    return {
      label: 'Admin',
      detail: 'Administrator access',
      statusLabel: 'Active',
      tone: 'success',
      isActive: true,
      isExpired: false,
    }
  }

  if (role === 'free') {
    return {
      label: 'Free',
      detail: 'Free plan',
      statusLabel: statusLabel(status),
      tone: 'neutral',
      isActive: false,
      isExpired: false,
    }
  }

  const paidRole = role === 'enterprise' ? 'Enterprise' : 'Pro'
  const statusIsActive = !status || ACTIVE_STATUSES.has(status)
  const isActive = statusIsActive && !isPastEndDate
  const isExpired = !isActive

  if (!isActive) {
    return {
      label: paidRole,
      detail: hasEndDate ? `Expired ${formatDateTime(endDate)}` : 'Not active',
      statusLabel: statusLabel(status || 'expired'),
      tone: 'danger',
      isActive: false,
      isExpired,
    }
  }

  return {
    label: paidRole,
    detail: hasEndDate ? `Ends ${formatDateTime(endDate)}` : 'No expiry set',
    statusLabel: statusLabel(status || 'active'),
    tone: status === 'cancel_at_period_end' ? 'warning' : 'success',
    isActive,
    isExpired,
  }
}
