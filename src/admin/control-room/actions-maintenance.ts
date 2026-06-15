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
      ctx.setMessage('Maintenance counts refreshed. No cleanup action was executed.')
    } catch {
      ctx.error.value = 'Maintenance data refresh failed. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const cleanupTestUsers = async () => {
    const count = ctx.maintenance.value?.test_users_count ?? 0
    ctx.openAdminConfirmation({
      title: 'Confirm test account deletion',
      summary: `This will delete ${count} test account${count === 1 ? '' : 's'}.`,
      details: [
        'This deletes data. Refreshing counts does not delete anything.',
        'Only smoke-, ocr-, office-, and @example.com test accounts are matched.',
        'Admins and real users are protected by backend checks.',
      ],
      confirmLabel: 'Delete test accounts',
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
            `Deleted ${result.deleted_count} test account${result.deleted_count === 1 ? '' : 's'}; ${result.remaining_test_users_count} remain.`,
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
      title: 'Confirm expired temporary file cleanup',
      summary: `This will clean ${count} expired temporary path${count === 1 ? '' : 's'}.`,
      details: [
        `Scanned directory: ${
          ctx.maintenance.value?.file_retention?.upload_dir || 'upload directory unavailable'
        }`,
        'Only expired PDF-Flow uploads, conversion results, and download packages are removed.',
        'User accounts, feedback, audit logs, and database records are not deleted.',
      ],
      confirmLabel: 'Clean temporary files',
      savingKey: 'maintenance:cleanup-files',
      tone: 'warning',
      run: async () => {
        ctx.savingKey.value = 'maintenance:cleanup-files'
        ctx.error.value = ''

        try {
          const result = await adminAPI.cleanupExpiredFiles()
          await refreshAdminMeta()
          ctx.setMessage(
            `Cleaned ${result.removed_count} expired temporary path${result.removed_count === 1 ? '' : 's'} and freed ${formatAdminBytes(result.removed_bytes)}.`,
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
