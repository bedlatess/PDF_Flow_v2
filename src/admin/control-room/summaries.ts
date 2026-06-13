import type { AdminFeedback, AdminHealthReport } from '@/admin/api'
import { formatAdminDate, parseAdminDiagnostics, serviceStatusText } from './formatters'

export const buildFeedbackSummary = (report: AdminFeedback) => {
  const lines = [
    `PDF-Flow 反馈 #${report.id}`,
    `状态：${report.status}`,
    `类型：${report.category}`,
    `影响程度：${report.severity}`,
    `标题：${report.title}`,
    `页面：${report.page_url || '未记录'}`,
    `诊断码：${report.diagnostic_code || '未记录'}`,
    `联系：${report.email || '未提供'}`,
    `提交时间：${formatAdminDate(report.created_at)}`,
    '',
    '用户描述：',
    report.message,
  ]

  const diagnostics = parseAdminDiagnostics(report.diagnostics)
  if (diagnostics) {
    lines.push('', '诊断信息：', diagnostics)
  }

  if (report.user_agent) {
    lines.push('', `浏览器：${report.user_agent}`)
  }

  if (report.admin_note) {
    lines.push('', '管理员备注：', report.admin_note)
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
    'PDF-Flow 上线健康报告',
    `生成时间：${formatAdminDate(report.generated_at)}`,
    `前端版本：${options.appVersion}`,
    `后端版本：${report.app_version}`,
    `环境：${report.environment}`,
    `数据库迁移：${report.migration_version || '未读取到'}`,
    `服务状态：${serviceStatusText(report)}`,
    `用户：${report.active_users_count}/${report.users_count} 活跃`,
    `任务：失败 ${report.failed_jobs_count}，处理中 ${report.running_jobs_count}`,
    `反馈：待处理 ${report.open_feedback_count}`,
    `API 错误：${report.api_error_count}`,
    `最近错误路径：${report.recent_error_path || '无'}`,
    `最近反馈：${report.recent_feedback_title || '无'}`,
    `页面：${options.pageUrl}`,
  ].join('\n')
}
