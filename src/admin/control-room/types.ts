export type ControlRoomTabId =
  | 'overview'
  | 'flags'
  | 'settings'
  | 'content'
  | 'users'
  | 'jobs'
  | 'payments'
  | 'feedback'
  | 'errors'
  | 'maintenance'
  | 'audit'

export type AdminConfirmation = {
  title: string
  summary: string
  details: string[]
  confirmLabel: string
  savingKey: string
  tone: 'danger' | 'warning'
  run: () => Promise<void>
}
