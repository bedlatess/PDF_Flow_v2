export type ControlRoomTabId =
  | 'overview'
  | 'users'
  | 'plans'
  | 'paymentSetup'
  | 'payments'
  | 'flags'
  | 'serviceProviders'
  | 'settings'
  | 'content'
  | 'jobs'
  | 'feedback'
  | 'errors'
  | 'maintenance'
  | 'security'
  | 'audit'

export type ControlRoomTabGroup =
  | 'Command'
  | 'Operate'
  | 'Product'
  | 'Revenue'
  | 'System'

export type AdminDomainKey =
  | 'overview'
  | 'users'
  | 'revenue'
  | 'productConfig'
  | 'operations'
  | 'security'

export type AdminModuleCapability =
  | 'admin:overview:read'
  | 'admin:users:manage'
  | 'admin:revenue:configure'
  | 'admin:revenue:reconcile'
  | 'admin:product:configure'
  | 'admin:operations:observe'
  | 'admin:operations:maintain'
  | 'admin:security:manage'
  | 'admin:audit:read'

export type AdminModuleStatusSource =
  | 'systemHealth'
  | 'serviceRisk'
  | 'serviceProviderReadiness'
  | 'paymentReadiness'
  | 'paymentRisk'
  | 'lockedFlags'
  | 'failedJobs'
  | 'openFeedback'
  | 'apiErrors'
  | 'maintenanceRisk'
  | 'auditRecent'

export type AdminModuleRiskLevel = 'low' | 'medium' | 'high' | 'critical'

export type AdminConfirmation = {
  title: string
  summary: string
  details: string[]
  confirmLabel: string
  savingKey: string
  tone: 'danger' | 'warning'
  run: () => Promise<void>
}
