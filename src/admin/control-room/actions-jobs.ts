import { adminAPI } from '@/admin/api'
import type { ControlRoomContext } from './context'

export const createControlRoomJobsActions = (ctx: ControlRoomContext) => {
  const loadJobs = async () => {
    ctx.savingKey.value = 'jobs:refresh'
    ctx.error.value = ''

    try {
      ctx.jobs.value = await adminAPI.listJobs({
        status_filter: ctx.jobStatusFilter.value || undefined,
      })
      ctx.operations.value = await adminAPI.getOperations()
    } catch {
      ctx.error.value = 'Job list failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    loadJobs,
  }
}
