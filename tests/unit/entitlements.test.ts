import { describe, expect, it } from 'vitest'
import { getEntitlementSummary } from '@/utils/entitlements'

describe('entitlement summaries', () => {
  it('marks manual pro access active before expiry', () => {
    const summary = getEntitlementSummary({
      role: 'pro',
      subscription_status: 'manual',
      subscription_end_date: new Date(Date.now() + 86400_000).toISOString(),
    })

    expect(summary.label).toBe('Pro')
    expect(summary.statusLabel).toBe('Manual')
    expect(summary.tone).toBe('success')
    expect(summary.isActive).toBe(true)
  })

  it('marks expired pro access inactive', () => {
    const summary = getEntitlementSummary({
      role: 'pro',
      subscription_status: 'manual',
      subscription_end_date: new Date(Date.now() - 86400_000).toISOString(),
    })

    expect(summary.label).toBe('Pro')
    expect(summary.tone).toBe('danger')
    expect(summary.isActive).toBe(false)
    expect(summary.isExpired).toBe(true)
  })

  it('treats admin as active without subscription fields', () => {
    const summary = getEntitlementSummary({ role: 'admin' })

    expect(summary.label).toBe('Admin')
    expect(summary.statusLabel).toBe('Active')
    expect(summary.isActive).toBe(true)
  })
})
