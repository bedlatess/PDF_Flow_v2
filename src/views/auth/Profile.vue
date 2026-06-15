<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowDownToLine,
  Clock3,
  FileClock,
  Gauge,
  History,
  Loader2,
  Pencil,
  RefreshCw,
  ShieldCheck,
  Trash2,
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import Button from '@/components/common/Button.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import { useLocalePath } from '@/composables/useLocalePath'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { useUserStore } from '@/stores/user'
import { fileAPI, type JobHistoryItem } from '@/services/api/files'
import { getEntitlementSummary } from '@/utils/entitlements'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { quotaSummary, shortFailureMessage } from '@/utils/release-polish'

const router = useRouter()
const userStore = useUserStore()
const siteConfigStore = useSiteConfigStore()
const { t } = useI18n()
const { localePath } = useLocalePath()

const editing = ref(false)
const updateMessage = ref('')
const accountError = ref<FormattedUserError | null>(null)
const showDeleteConfirmation = ref(false)
const recentJobs = ref<JobHistoryItem[]>([])
const historyLoading = ref(false)
const editForm = reactive({ full_name: '' })

const initialLoading = computed(() => userStore.loading && !userStore.user)
const displayName = computed(() => userStore.user?.full_name || userStore.user?.email || t('account.notSet'))
const initials = computed(() => displayName.value.charAt(0).toUpperCase())
const entitlement = computed(() =>
  getEntitlementSummary({
    role: userStore.user?.role,
    subscription_status: userStore.user?.subscription_status,
    subscription_end_date: userStore.user?.subscription_end_date,
  })
)

const isProLike = computed(() => userStore.isProTier || userStore.isEnterpriseTier || userStore.isAdmin)

const planLabel = computed(() => {
  const role = entitlement.value.isActive ? userStore.user?.role || 'free' : 'free'
  return t(`account.plans.${role}`)
})

const planBadgeClass = computed(() => {
  if (entitlement.value.isExpired) return 'bg-rose-400/15 text-rose-700 dark:text-rose-200'
  if (userStore.isEnterpriseTier || userStore.isAdmin) return 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
  if (userStore.isProTier) return 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-200'
  return 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
})

const quotaDisplay = computed(() => {
  const remaining = userStore.stats?.quota_remaining
  if (remaining === -1 || remaining === undefined) return t('account.unlimited')
  return String(remaining)
})

const usageItems = computed(() => [
  { label: t('account.totalRequests'), value: userStore.stats?.total_requests ?? 0, icon: Gauge },
  { label: t('account.requestsToday'), value: userStore.stats?.requests_today ?? 0, icon: Clock3 },
  { label: t('account.quotaRemaining'), value: quotaDisplay.value, icon: ShieldCheck },
])

const importantToolLimits = computed(() => {
  const keys = [
    ['pdf_to_word', 'PDF to Word'],
    ['pdf_to_excel', 'PDF to Excel'],
    ['html_to_pdf', 'HTML to PDF'],
    ['ocr_pdf', 'OCR PDF'],
    ['office_to_pdf', 'Office to PDF'],
    ['batch_convert', 'Batch Convert'],
  ] as const
  return keys.map(([key, label]) => ({
    key,
    label,
    flag: siteConfigStore.getFeatureFlag(key, label),
    summary: quotaSummary(siteConfigStore.getFeatureFlag(key, label), isProLike.value),
  }))
})

const availableDownloads = computed(() => recentJobs.value.filter((job) => job.download_available).length)
const failedJobs = computed(() => recentJobs.value.filter((job) => job.status === 'failed').length)
const deleteDialogDetails = computed(() => [
  t('account.deleteDialog.detailAccess'),
  t('account.deleteDialog.detailRetention'),
  t('account.deleteDialog.detailSignIn'),
])

const formatDate = (value?: string | null) => {
  if (!value) return 'Not finished'
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

const loadRecentHistory = async () => {
  if (!userStore.isAuthenticated) return
  historyLoading.value = true
  try {
    const response = await fileAPI.getHistory({ limit: 5, offset: 0 })
    recentJobs.value = response.items
  } catch {
    recentJobs.value = []
  } finally {
    historyLoading.value = false
  }
}

const refreshAccount = async () => {
  accountError.value = null
  await siteConfigStore.fetchPublicConfig()
  await userStore.checkAuth()
  await loadRecentHistory()
}

const startEdit = () => {
  editForm.full_name = userStore.user?.full_name || ''
  editing.value = true
  updateMessage.value = ''
  accountError.value = null
}

const cancelEdit = () => {
  editing.value = false
  userStore.error = null
  accountError.value = null
}

const saveProfile = async () => {
  accountError.value = null
  try {
    await userStore.updateProfile({ full_name: editForm.full_name.trim() })
    updateMessage.value = t('account.updateSuccess')
    editing.value = false
  } catch (error) {
    accountError.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackTitle: t('account.updateFailedTitle'),
      fallbackMessage: t('account.updateFailedMessage'),
    })
  }
}

const confirmDelete = async () => {
  accountError.value = null
  showDeleteConfirmation.value = true
}

const deleteAccount = async () => {
  try {
    await userStore.deleteAccount()
    showDeleteConfirmation.value = false
    router.push(localePath('/'))
  } catch (error) {
    accountError.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackTitle: t('account.deleteFailedTitle'),
      fallbackMessage: t('account.deleteFailedMessage'),
    })
  }
}

const openPricing = () => router.push(localePath('/pricing'))
const openHistory = () => router.push(localePath('/history'))

const downloadJob = async (job: JobHistoryItem) => {
  if (!job.download_available) return
  const blob = await fileAPI.downloadHistoryResult(job.job_id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = job.input_file_name?.replace(/\.[^.]+$/, '-result') || 'pdf-flow-result'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(refreshAccount)
</script>

<template>
  <div class="pf-app-surface min-h-screen px-4 py-8 text-slate-950 dark:text-white sm:px-6 lg:px-8">
    <div class="mx-auto max-w-7xl">
      <header class="mb-6 flex min-w-0 flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div class="min-w-0">
          <p class="pf-eyebrow text-sky-700 dark:text-sky-300">PDF-Flow Account</p>
          <h1 class="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            {{ t('account.myAccount') }}
          </h1>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Account, plan access, usage limits, recent results, and downloads are collected here so you can see what is available before starting another task.
          </p>
        </div>
        <button
          class="inline-flex min-h-10 items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
          @click="refreshAccount"
        >
          <RefreshCw class="mr-2 h-4 w-4" :class="{ 'animate-spin': userStore.loading || userStore.statsLoading || historyLoading }" />
          {{ t('account.refresh') }}
        </button>
      </header>

      <section v-if="initialLoading" class="pf-panel p-10 text-center">
        <Loader2 class="mx-auto h-8 w-8 animate-spin text-sky-600" />
        <p class="mt-4 text-sm font-medium text-slate-600 dark:text-slate-300">
          {{ t('account.loading') }}
        </p>
      </section>

      <DiagnosticAlert
        v-else-if="!userStore.user"
        :title="t('account.emptyTitle')"
        :message="t('account.emptyMessage')"
        :support-hint="t('account.emptyHint')"
        tone="warning"
      />

      <template v-else>
        <DiagnosticAlert
          v-if="accountError"
          class="mb-6"
          :title="accountError.title"
          :message="accountError.message"
          :diagnostic-code="accountError.diagnosticCode"
          :support-hint="accountError.supportHint"
        />

        <section class="mb-6 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <article class="pf-panel p-5 sm:p-6">
            <div class="flex min-w-0 flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
              <div class="flex min-w-0 items-center gap-4">
                <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-2xl font-semibold text-white dark:bg-sky-500">
                  {{ initials }}
                </div>
                <div class="min-w-0">
                  <p class="truncate text-lg font-semibold">{{ displayName }}</p>
                  <p class="mt-1 break-all text-sm text-slate-500 dark:text-slate-400">{{ userStore.user.email }}</p>
                  <span class="mt-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold" :class="planBadgeClass">
                    {{ planLabel }}
                  </span>
                </div>
              </div>
              <Button v-if="!editing" variant="outline" class="rounded-md" @click="startEdit">
                <Pencil class="mr-2 h-4 w-4" />
                {{ t('account.editProfile') }}
              </Button>
            </div>

            <div class="mt-5 grid gap-3 sm:grid-cols-3">
              <div class="pf-panel-muted p-4">
                <p class="pf-eyebrow text-slate-500 dark:text-slate-400">Plan</p>
                <p class="mt-2 text-sm font-semibold">{{ entitlement.label }}</p>
              </div>
              <div class="pf-panel-muted p-4">
                <p class="pf-eyebrow text-slate-500 dark:text-slate-400">Status</p>
                <p class="mt-2 text-sm font-semibold">{{ entitlement.statusLabel }}</p>
              </div>
              <div class="pf-panel-muted p-4">
                <p class="pf-eyebrow text-slate-500 dark:text-slate-400">Access</p>
                <p class="mt-2 text-sm font-semibold" :class="entitlement.isActive ? 'text-emerald-700 dark:text-emerald-200' : 'text-amber-700 dark:text-amber-200'">
                  {{ entitlement.detail }}
                </p>
              </div>
            </div>

            <form v-if="editing" class="mt-5 space-y-4" @submit.prevent="saveProfile">
              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200">
                  {{ t('auth.fullName') }}
                </span>
                <input
                  v-model="editForm.full_name"
                  type="text"
                  class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                >
              </label>
              <div class="flex flex-col gap-3 sm:flex-row">
                <Button type="submit" class="rounded-md" :disabled="userStore.loading">
                  <Loader2 v-if="userStore.loading" class="mr-2 h-4 w-4 animate-spin" />
                  {{ t('account.save') }}
                </Button>
                <Button type="button" variant="outline" class="rounded-md" @click="cancelEdit">
                  {{ t('account.cancel') }}
                </Button>
              </div>
            </form>

            <div v-if="updateMessage" class="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200">
              {{ updateMessage }}
            </div>
          </article>

          <article class="pf-panel p-5 sm:p-6">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 class="text-lg font-semibold">{{ t('account.usage') }}</h2>
                <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  Today's usage and the limits that explain why a tool may stop accepting new jobs.
                </p>
              </div>
              <Button v-if="userStore.isFreeTier" class="rounded-md" @click="openPricing">
                {{ t('account.upgradeToPro') }}
              </Button>
            </div>

            <div v-if="userStore.statsLoading" class="mt-5 pf-panel-muted p-5 text-center">
              <Loader2 class="mx-auto h-6 w-6 animate-spin text-sky-600" />
              <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">{{ t('account.usageLoading') }}</p>
            </div>
            <DiagnosticAlert
              v-else-if="userStore.statsError"
              class="mt-5"
              :title="userStore.statsError.title"
              :message="userStore.statsError.message"
              :diagnostic-code="userStore.statsError.diagnosticCode"
              :support-hint="userStore.statsError.supportHint"
              tone="warning"
            />
            <template v-else>
              <div class="mt-5 grid gap-3 sm:grid-cols-3">
                <div v-for="item in usageItems" :key="item.label" class="pf-panel-muted p-4">
                  <component :is="item.icon" class="h-5 w-5 text-sky-600 dark:text-sky-300" />
                  <p class="mt-3 text-2xl font-semibold">{{ item.value }}</p>
                  <p class="mt-1 text-xs font-medium uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">{{ item.label }}</p>
                </div>
              </div>
              <div v-if="userStore.isFreeTier" class="mt-5">
                <div class="mb-2 flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
                  <span>{{ t('account.todayQuota') }}</span>
                  <span>{{ userStore.quotaUsagePercentage }}%</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div class="h-full bg-sky-600 transition-all dark:bg-sky-400" :style="{ width: `${userStore.quotaUsagePercentage}%` }" />
                </div>
              </div>
            </template>
          </article>
        </section>

        <section class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <article class="pf-panel p-5 sm:p-6">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h2 class="text-lg font-semibold">Tool limits</h2>
                <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  Configured limits are applied before new conversion jobs start. Completed downloads stay available until the result expires.
                </p>
              </div>
              <ShieldCheck class="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
            </div>
            <div class="mt-5 space-y-3">
              <div
                v-for="item in importantToolLimits"
                :key="item.key"
                class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
              >
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <p class="font-semibold">{{ item.label }}</p>
                  <span
                    class="rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="item.flag.enabled ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200' : 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200'"
                  >
                    {{ item.flag.enabled ? 'Available' : 'Maintenance' }}
                  </span>
                </div>
                <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">{{ item.summary }}</p>
              </div>
            </div>
          </article>

          <article class="pf-panel p-5 sm:p-6">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 class="text-lg font-semibold">Recent results</h2>
                <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {{ availableDownloads }} downloadable result{{ availableDownloads === 1 ? '' : 's' }} and {{ failedJobs }} failed task{{ failedJobs === 1 ? '' : 's' }} in the latest account history.
                </p>
              </div>
              <Button variant="outline" class="rounded-md" @click="openHistory">
                <History class="mr-2 h-4 w-4" />
                Open history
              </Button>
            </div>
            <div class="mt-5 space-y-3">
              <div v-if="historyLoading" class="pf-panel-muted p-5 text-center">
                <Loader2 class="mx-auto h-6 w-6 animate-spin text-sky-600" />
                <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">Loading recent results</p>
              </div>
              <div v-else-if="!recentJobs.length" class="pf-panel-muted p-5 text-center">
                <FileClock class="mx-auto h-8 w-8 text-slate-400" />
                <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">No account-owned jobs yet. Start a cloud tool to see results here.</p>
              </div>
              <div
                v-for="job in recentJobs"
                v-else
                :key="job.job_id"
                class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
              >
                <div class="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div class="min-w-0">
                    <p class="truncate font-semibold">{{ job.input_file_name || job.job_type }}</p>
                    <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ job.job_type.replace(/_/g, ' ') }} · {{ formatDate(job.created_at) }}</p>
                    <p v-if="job.status === 'failed'" class="mt-2 line-clamp-2 text-xs leading-5 text-rose-600 dark:text-rose-300">
                      {{ shortFailureMessage(job.error_message) }}
                    </p>
                  </div>
                  <div class="flex shrink-0 flex-wrap items-center gap-2">
                    <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="job.status === 'completed' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200' : job.status === 'failed' ? 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200' : 'bg-sky-50 text-sky-700 dark:bg-sky-500/10 dark:text-sky-200'">
                      {{ job.status }}
                    </span>
                    <Button v-if="job.download_available" size="sm" class="rounded-md" @click="downloadJob(job)">
                      <ArrowDownToLine class="mr-2 h-4 w-4" />
                      Download
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section class="mt-6 rounded-lg border border-red-100 bg-white p-6 shadow-sm dark:border-red-900/30 dark:bg-slate-900">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
                {{ t('account.dangerZone') }}
              </h2>
              <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                {{ t('account.deleteDescription') }}
              </p>
            </div>
            <button
              class="inline-flex items-center justify-center rounded-md border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition hover:border-red-300 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900/50 dark:text-red-300 dark:hover:bg-red-950/30 dark:hover:text-red-200"
              :disabled="userStore.loading"
              @click="confirmDelete"
            >
              <Trash2 class="mr-2 h-4 w-4" />
              {{ t('account.deleteAccount') }}
            </button>
          </div>
        </section>

        <ConfirmationDialog
          v-model="showDeleteConfirmation"
          :title="t('account.deleteDialog.title')"
          :summary="t('account.deleteDialog.summary', { email: userStore.user.email })"
          :details="deleteDialogDetails"
          :confirm-label="t('account.deleteDialog.confirm')"
          :cancel-label="t('account.cancel')"
          :loading="userStore.loading"
          @confirm="deleteAccount"
        />
      </template>
    </div>
  </div>
</template>
