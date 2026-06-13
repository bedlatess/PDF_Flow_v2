import { nextTick } from 'vue'
import { adminAPI } from '@/admin/api'
import type { ControlRoomContext } from './context'

type DiagnosticsActionDeps = {
  loadFeedback: () => Promise<void>
}

export const createControlRoomDiagnosticsActions = (
  ctx: ControlRoomContext,
  { loadFeedback }: DiagnosticsActionDeps,
) => {
  const openFeedbackFromDiagnostics = async (feedbackId: number) => {
    ctx.activeTab.value = 'feedback'
    ctx.feedbackStatusFilter.value = ''
    ctx.highlightedFeedbackId.value = feedbackId
    await loadFeedback()
    await nextTick()

    document.getElementById(`feedback-${feedbackId}`)?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  }

  const loadDiagnostics = async () => {
    ctx.savingKey.value = 'errors:refresh'
    ctx.error.value = ''

    try {
      const data = await adminAPI.getDiagnostics()
      ctx.diagnostics.value = data
      ctx.apiErrors.value = data.recent_errors
      ctx.overview.value = await adminAPI.getOverview()
    } catch {
      ctx.error.value = 'Diagnostic data failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    openFeedbackFromDiagnostics,
    loadDiagnostics,
  }
}
