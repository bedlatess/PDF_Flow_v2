export type ControlRoomTabId =
  | 'overview'
  | 'users'
  | 'paymentSetup'
  | 'payments'
  | 'flags'
  | 'settings'
  | 'content'
  | 'jobs'
  | 'feedback'
  | 'errors'
  | 'maintenance'
  | 'security'
  | 'audit'

export type ControlRoomTabGroup =
  | '概览'
  | '客户与收入'
  | '产品配置'
  | '运营支持'
  | '安全'

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
  | 'serviceRisk'
  | 'paymentReadiness'
  | 'paymentRisk'
  | 'lockedFlags'
  | 'failedJobs'
  | 'openFeedback'
  | 'apiErrors'
  | 'maintenanceRisk'
  | 'auditRecent'

export type AdminConfirmation = {
  title: string
  summary: string
  details: string[]
  confirmLabel: string
  savingKey: string
  tone: 'danger' | 'warning'
  run: () => Promise<void>
}
