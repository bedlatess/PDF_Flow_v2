import { adminAPI } from '@/admin/api'
import { formatAdminBytes } from './formatters'
import type { ControlRoomContext } from './context'

type MaintenanceActionDeps = {
  refreshAdminMeta: () => Promise<void>
}

export const createControlRoomMaintenanceActions = (
  ctx: ControlRoomContext,
  { refreshAdminMeta }: MaintenanceActionDeps,
) => {
  const refreshMaintenance = async () => {
    ctx.savingKey.value = 'maintenance:refresh'
    ctx.error.value = ''

    try {
      await refreshAdminMeta()
      ctx.diagnostics.value = await adminAPI.getDiagnostics()
      ctx.apiErrors.value = ctx.diagnostics.value.recent_errors
      ctx.setMessage('已重新统计维护数据，未执行任何删除操作')
    } catch {
      ctx.error.value = 'Maintenance data refresh failed. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const cleanupTestUsers = async () => {
    const count = ctx.maintenance.value?.test_users_count ?? 0
    ctx.openAdminConfirmation({
      title: '确认删除测试账号',
      summary: `将删除 ${count} 个测试账号。`,
      details: [
        '这会真正删除数据；重新统计数量不会删除任何内容。',
        '仅匹配 smoke-、ocr-、office- 和 @example.com 测试账号。',
        '不会删除管理员或真实用户，后端会按同一规则再次校验。',
      ],
      confirmLabel: '确认删除测试账号',
      savingKey: 'maintenance:cleanup-users',
      tone: 'danger',
      run: async () => {
        ctx.savingKey.value = 'maintenance:cleanup-users'
        ctx.error.value = ''

        try {
          const result = await adminAPI.cleanupTestUsers()
          const [usersData, jobsData, feedbackData, diagnosticsData] = await Promise.all([
            adminAPI.listUsers({
              search: ctx.userSearch.value.trim() || undefined,
            }),
            adminAPI.listJobs({
              status_filter: ctx.jobStatusFilter.value || undefined,
            }),
            adminAPI.listFeedback({
              status_filter: ctx.feedbackStatusFilter.value || undefined,
            }),
            adminAPI.getDiagnostics(),
          ])
          ctx.users.value = usersData
          ctx.jobs.value = jobsData
          ctx.feedbackReports.value = feedbackData
          ctx.diagnostics.value = diagnosticsData
          ctx.apiErrors.value = diagnosticsData.recent_errors
          await refreshAdminMeta()
          ctx.setMessage(
            `已删除 ${result.deleted_count} 个测试账号，剩余 ${result.remaining_test_users_count} 个`,
          )
        } catch (err: any) {
          ctx.error.value =
            err?.response?.data?.detail || 'Test account cleanup failed. Please try again later.'
          throw err
        } finally {
          ctx.savingKey.value = null
        }
      },
    })
  }

  const cleanupExpiredFiles = async () => {
    const count = ctx.maintenance.value?.file_retention?.removable_count ?? 0
    ctx.openAdminConfirmation({
      title: '确认清理过期临时文件',
      summary: `将清理 ${count} 个过期临时文件目录。`,
      details: [
        `扫描目录：${
          ctx.maintenance.value?.file_retention?.upload_dir || '未读取到上传目录'
        }`,
        '只会删除 PDF-Flow 生成的过期临时上传、转换结果和下载包。',
        '不会删除用户账号、反馈、审计日志或数据库记录。',
      ],
      confirmLabel: '确认清理临时文件',
      savingKey: 'maintenance:cleanup-files',
      tone: 'warning',
      run: async () => {
        ctx.savingKey.value = 'maintenance:cleanup-files'
        ctx.error.value = ''

        try {
          const result = await adminAPI.cleanupExpiredFiles()
          await refreshAdminMeta()
          ctx.setMessage(
            `已清理 ${result.removed_count} 个过期临时目录，释放 ${formatAdminBytes(result.removed_bytes)}`,
          )
        } catch (err: any) {
          ctx.error.value =
            err?.response?.data?.detail ||
            'Temporary file cleanup failed. Please try again later.'
          throw err
        } finally {
          ctx.savingKey.value = null
        }
      },
    })
  }

  return {
    refreshMaintenance,
    cleanupTestUsers,
    cleanupExpiredFiles,
  }
}
