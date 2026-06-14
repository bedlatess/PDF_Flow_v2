import { computed, ref } from 'vue'
import {
  type AdminApiError,
  type AdminAuditLog,
  type AdminDiagnostics,
  type AdminFeedback,
  type AdminHealthReport,
  type AdminJob,
  type AdminMaintenance,
  type AdminOperations,
  type AdminPasswordResetLink,
  type AdminOverview,
  type AdminPaymentSummary,
  type AdminPricingPlan,
  type AdminUser,
  type ContentBlock,
  type FeatureFlag,
  type SiteSetting,
} from '@/admin/api'
import { useSiteConfigStore } from '@/stores/siteConfig'
import type { AdminConfirmation, ControlRoomTabId } from './types'

const flashDelayMs = 2200

export const createControlRoomContext = () => {
  const siteConfigStore = useSiteConfigStore()
  const loading = ref(true)
  const savingKey = ref<string | null>(null)
  const activeTab = ref<ControlRoomTabId>('overview')
  const error = ref('')
  const success = ref('')

  const overview = ref<AdminOverview | null>(null)
  const operations = ref<AdminOperations | null>(null)
  const settings = ref<SiteSetting[]>([])
  const flags = ref<FeatureFlag[]>([])
  const contentBlocks = ref<ContentBlock[]>([])
  const auditLogs = ref<AdminAuditLog[]>([])
  const users = ref<AdminUser[]>([])
  const userPasswordResetLinks = ref<Record<number, AdminPasswordResetLink>>({})
  const jobs = ref<AdminJob[]>([])
  const feedbackReports = ref<AdminFeedback[]>([])
  const apiErrors = ref<AdminApiError[]>([])
  const diagnostics = ref<AdminDiagnostics | null>(null)
  const healthReport = ref<AdminHealthReport | null>(null)
  const maintenance = ref<AdminMaintenance | null>(null)
  const paymentSummary = ref<AdminPaymentSummary | null>(null)
  const pricingPlans = ref<AdminPricingPlan[]>([])
  const userSearch = ref('')
  const jobStatusFilter = ref('')
  const jobSearch = ref('')
  const paymentProviderFilter = ref('')
  const paymentStatusFilter = ref('')
  const feedbackStatusFilter = ref('')
  const highlightedFeedbackId = ref<number | null>(null)
  const copiedFeedbackId = ref<number | null>(null)
  const healthReportCopied = ref(false)
  const diagnosticSummaryCopied = ref(false)
  const reconciliationCopied = ref(false)
  const evidenceCopied = ref(false)
  const selectedContent = ref<ContentBlock | null>(null)
  const pendingConfirmation = ref<AdminConfirmation | null>(null)

  const enabledFlagCount = computed(() => flags.value.filter((flag) => flag.enabled).length)
  const lockedFlagCount = computed(
    () => flags.value.filter((flag) => flag.requires_login || flag.requires_pro).length,
  )
  const filteredJobs = computed(() => {
    const keyword = jobSearch.value.trim().toLowerCase()
    if (!keyword) return jobs.value
    return jobs.value.filter((job) =>
      [
        job.job_id,
        job.job_type,
        job.status,
        job.user_email || '',
        job.input_file_name,
        job.error_message || '',
      ].some((value) => value.toLowerCase().includes(keyword)),
    )
  })

  const setMessage = (message: string) => {
    success.value = message
    window.setTimeout(() => {
      if (success.value === message) {
        success.value = ''
      }
    }, flashDelayMs)
  }

  const openAdminConfirmation = (confirmation: AdminConfirmation) => {
    error.value = ''
    pendingConfirmation.value = confirmation
  }

  const closeAdminConfirmation = () => {
    if (pendingConfirmation.value && savingKey.value === pendingConfirmation.value.savingKey) {
      return
    }
    pendingConfirmation.value = null
  }

  const confirmAdminAction = async () => {
    const confirmation = pendingConfirmation.value
    if (!confirmation) return

    try {
      await confirmation.run()
      pendingConfirmation.value = null
    } catch {
      // Action handlers own their user-facing error copy.
    }
  }

  return {
    siteConfigStore,
    loading,
    savingKey,
    activeTab,
    error,
    success,
    overview,
    operations,
    settings,
    flags,
    contentBlocks,
    auditLogs,
    users,
    userPasswordResetLinks,
    jobs,
    feedbackReports,
    apiErrors,
    diagnostics,
    healthReport,
    maintenance,
    paymentSummary,
    pricingPlans,
    userSearch,
    jobStatusFilter,
    jobSearch,
    paymentProviderFilter,
    paymentStatusFilter,
    feedbackStatusFilter,
    highlightedFeedbackId,
    copiedFeedbackId,
    healthReportCopied,
    diagnosticSummaryCopied,
    reconciliationCopied,
    evidenceCopied,
    selectedContent,
    pendingConfirmation,
    enabledFlagCount,
    lockedFlagCount,
    filteredJobs,
    setMessage,
    openAdminConfirmation,
    closeAdminConfirmation,
    confirmAdminAction,
  }
}

export type ControlRoomContext = ReturnType<typeof createControlRoomContext>
