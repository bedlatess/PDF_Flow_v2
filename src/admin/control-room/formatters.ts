import type { AdminHealthReport } from '@/admin/api'

export const formatAdminDate = (value: string) =>
  new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))

export const formatAdminBytes = (value: number) => {
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

export const formatAdminMoney = (amountCents: number, currency: string) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency || 'USD',
  }).format((amountCents || 0) / 100)

export const parseAdminDiagnostics = (value: string | null) => {
  if (!value) return ''
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}

export const serviceStatusText = (report: AdminHealthReport | null) => {
  if (!report) return 'unknown'
  return Object.entries(report.services)
    .map(([name, service]) => `${name}=${service.status}`)
    .join(', ')
}
