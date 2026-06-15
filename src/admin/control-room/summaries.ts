import type { AdminFeedback, AdminHealthReport } from '@/admin/api'
import { formatAdminDate, parseAdminDiagnostics, serviceStatusText } from './formatters'

export const buildFeedbackSummary = (report: AdminFeedback) => {
  const lines = [
    `PDF-Flow feedback #${report.id}`,
    `Status: ${report.status}`,
    `Category: ${report.category}`,
    `Severity: ${report.severity}`,
    `Title: ${report.title}`,
    `Page: ${report.page_url || 'not recorded'}`,
    `Diagnostic code: ${report.diagnostic_code || 'not recorded'}`,
    `Contact: ${report.email || 'not provided'}`,
    `Submitted: ${formatAdminDate(report.created_at)}`,
    '',
    'User message:',
    report.message,
  ]

  const diagnostics = parseAdminDiagnostics(report.diagnostics)
  if (diagnostics) {
    lines.push('', 'Diagnostics:', diagnostics)
  }

  if (report.user_agent) {
    lines.push('', `User agent: ${report.user_agent}`)
  }

  if (report.admin_note) {
    lines.push('', 'Admin note:', report.admin_note)
  }

  return lines.join('\n')
}

export const buildHealthReportSummary = (
  report: AdminHealthReport | null,
  options: {
    appVersion: string
    pageUrl: string
  },
) => {
  if (!report) return ''

  return [
    'PDF-Flow health report',
    `Generated: ${formatAdminDate(report.generated_at)}`,
    `Frontend version: ${options.appVersion}`,
    `Backend version: ${report.app_version}`,
    `Environment: ${report.environment}`,
    `Database migration: ${report.migration_version || 'not available'}`,
    `Service status: ${serviceStatusText(report)}`,
    `Users: ${report.active_users_count}/${report.users_count} active`,
    `Jobs: ${report.failed_jobs_count} failed, ${report.running_jobs_count} running`,
    `Feedback: ${report.open_feedback_count} open`,
    `API errors: ${report.api_error_count}`,
    `Recent error path: ${report.recent_error_path || 'none'}`,
    `Recent feedback: ${report.recent_feedback_title || 'none'}`,
    `Page: ${options.pageUrl}`,
  ].join('\n')
}
