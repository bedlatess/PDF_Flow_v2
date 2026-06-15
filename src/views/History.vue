<script setup lang="ts">
import {
  ArrowDownToLine,
  ArrowLeft,
  Check,
  Clock3,
  Copy,
  FileClock,
  FileWarning,
  Loader2,
  RefreshCw,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import { useLocalePath } from '@/composables/useLocalePath'
import { fileAPI, type JobHistoryItem, type JobHistoryStatus } from '@/services/api/files'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { shortFailureMessage } from '@/utils/release-polish'

const router = useRouter()
const { t } = useI18n()
const { localePath } = useLocalePath()
const userStore = useUserStore()

const jobs = ref<JobHistoryItem[]>([])
const total = ref(0)
const loading = ref(false)
const downloadingJobId = ref<string | null>(null)
const error = ref<FormattedUserError | null>(null)
const selectedStatus = ref<JobHistoryStatus | ''>('')
const selectedJobType = ref('')
const expandedJobId = ref<string | null>(null)
const copiedJobId = ref<string | null>(null)

const statusOptions: Array<{ value: JobHistoryStatus | ''; labelKey: string }> = [
  { value: '', labelKey: 'history.filters.allStatuses' },
  { value: 'processing', labelKey: 'history.status.processing' },
  { value: 'pending', labelKey: 'history.status.pending' },
  { value: 'completed', labelKey: 'history.status.completed' },
  { value: 'failed', labelKey: 'history.status.failed' },
  { value: 'cancelled', labelKey: 'history.status.cancelled' },
]

const jobTypeOptions = [
  'merge_pdf',
  'split_pdf',
  'compress_pdf',
  'rotate_pdf',
  'image_to_pdf',
  'pdf_to_image',
  'pdf_to_word',
  'pdf_to_excel',
  'html_to_pdf',
  'ocr_pdf',
  'office_to_pdf',
]

const completedCount = computed(() => jobs.value.filter((job) => job.status === 'completed').length)
const failedCount = computed(() => jobs.value.filter((job) => job.status === 'failed').length)
const availableCount = computed(() => jobs.value.filter((job) => job.download_available).length)

const goHome = () => {
  router.push(localePath('/'))
}

const goLogin = () => {
  router.push({
    path: localePath('/auth/login'),
    query: { redirect: router.currentRoute.value.fullPath },
  })
}

const loadHistory = async () => {
  if (!userStore.isAuthenticated) {
    const authenticated = await userStore.checkAuth()
    if (!authenticated) return
  }

  loading.value = true
  error.value = null
  try {
    const response = await fileAPI.getHistory({
      status: selectedStatus.value,
      job_type: selectedJobType.value || undefined,
      limit: 60,
      offset: 0,
    })
    jobs.value = response.items
    total.value = response.total
  } catch (err) {
    error.value = formatUserFacingError(err, {
      area: 'GENERAL',
      fallbackTitle: t('history.errors.loadTitle'),
      fallbackMessage: t('history.errors.loadMessage'),
    })
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  void loadHistory()
}

const toggleDetails = (jobId: string) => {
  expandedJobId.value = expandedJobId.value === jobId ? null : jobId
}

const downloadJob = async (job: JobHistoryItem) => {
  if (!job.download_available) return

  downloadingJobId.value = job.job_id
  error.value = null
  try {
    const blob = await fileAPI.downloadHistoryResult(job.job_id)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = resultFileName(job)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = formatUserFacingError(err, {
      area: 'GENERAL',
      fallbackTitle: t('history.errors.downloadTitle'),
      fallbackMessage: t('history.errors.downloadMessage'),
    })
    await loadHistory()
  } finally {
    downloadingJobId.value = null
  }
}

const copyJobId = async (jobId: string) => {
  try {
    await navigator.clipboard.writeText(jobId)
    copiedJobId.value = jobId
    window.setTimeout(() => {
      if (copiedJobId.value === jobId) copiedJobId.value = null
    }, 1800)
  } catch {
    copiedJobId.value = null
  }
}

const jobErrorSummary = (job: JobHistoryItem) => {
  if (!job.error_message) return ''
  return shortFailureMessage(formatUserFacingError(job.error_message, {
    area: 'GENERAL',
    fallbackTitle: t('history.errors.jobFailedTitle'),
    fallbackMessage: t('history.errors.jobFailedMessage'),
  }).message)
}

const resultFileName = (job: JobHistoryItem) => {
  const base = job.input_file_name?.replace(/\.[^.]+$/, '') || job.job_type || 'result'
  if (job.job_type === 'ocr_pdf') return `${base}-ocr.txt`
  if (job.job_type === 'pdf_to_image' || job.job_type === 'split_pdf') return `${base}-results.zip`
  if (job.job_type === 'office_to_pdf') return `${base}.pdf`
  if (job.job_type === 'pdf_to_word') return `${base}.docx`
  if (job.job_type === 'pdf_to_excel') return `${base}.xlsx`
  return `${base}-result.pdf`
}

const statusTone = (status: JobHistoryStatus) => {
  if (status === 'completed') return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
  if (status === 'failed') return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200'
  if (status === 'cancelled') return 'border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
  return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200'
}

const downloadTone = (state: JobHistoryItem['download_state']) => {
  if (state === 'available') return 'text-emerald-700 dark:text-emerald-300'
  if (state === 'expired') return 'text-amber-700 dark:text-amber-300'
  return 'text-slate-500 dark:text-slate-400'
}

const formatDate = (value?: string | null) => {
  if (!value) return t('history.common.none')
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return t('history.common.unknownSize')
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${size.toFixed(size >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`
}

const jobLabel = (jobType: string) => t(`history.jobTypes.${jobType}`, jobType.replace(/_/g, ' '))

onMounted(() => {
  void loadHistory()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950">
    <section class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <button
          class="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
          @click="goHome"
        >
          <ArrowLeft class="h-4 w-4" />
          {{ t('history.page.backHome') }}
        </button>
        <Button
          v-if="userStore.isAuthenticated"
          variant="outline"
          class="rounded-md"
          :disabled="loading"
          @click="loadHistory"
        >
          <RefreshCw class="mr-2 h-4 w-4" :class="{ 'animate-spin': loading }" />
          {{ t('history.actions.refresh') }}
        </Button>
      </div>

      <div class="mt-8 grid min-w-0 gap-6 lg:grid-cols-[1fr_360px] lg:items-end">
        <div>
          <div class="inline-flex items-center gap-2 rounded-md border border-sky-200 bg-white px-4 py-2 text-sm font-semibold text-sky-700 shadow-sm dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200">
            <Clock3 class="h-4 w-4" />
            {{ t('history.page.badge') }}
          </div>
          <h1 class="mt-5 text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            {{ t('history.page.title') }}
          </h1>
          <p class="mt-4 max-w-2xl text-base leading-8 text-slate-600 dark:text-slate-300">
            {{ t('history.page.description') }}
          </p>
        </div>

        <div class="grid min-w-0 grid-cols-3 gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.stats.total') }}</p>
            <p class="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{{ total }}</p>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.stats.completed') }}</p>
            <p class="mt-2 text-2xl font-semibold text-emerald-600 dark:text-emerald-300">{{ completedCount }}</p>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.stats.available') }}</p>
            <p class="mt-2 text-2xl font-semibold text-sky-600 dark:text-sky-300">{{ availableCount }}</p>
          </div>
        </div>
      </div>

      <div v-if="!userStore.isAuthenticated && !userStore.loading" class="mt-8 rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <FileClock class="mx-auto h-10 w-10 text-sky-500" />
        <h2 class="mt-4 text-xl font-semibold text-slate-950 dark:text-white">{{ t('history.auth.title') }}</h2>
        <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ t('history.auth.description') }}
        </p>
        <Button class="mt-5 rounded-md" @click="goLogin">
          {{ t('history.auth.action') }}
        </Button>
      </div>

      <div v-else class="mt-8 space-y-4">
        <DiagnosticAlert
          v-if="error"
          :title="error.title"
          :message="error.message"
          :diagnostic-code="error.diagnosticCode"
          :support-hint="error.supportHint"
        />

        <div class="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:grid-cols-[220px_1fr_auto]">
          <label class="block">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.filters.status') }}</span>
            <select
              v-model="selectedStatus"
              class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-500/20"
              @change="applyFilters"
            >
              <option v-for="option in statusOptions" :key="option.value || 'all'" :value="option.value">
                {{ t(option.labelKey) }}
              </option>
            </select>
          </label>
          <label class="block">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.filters.tool') }}</span>
            <select
              v-model="selectedJobType"
              class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-sky-500/20"
              @change="applyFilters"
            >
              <option value="">{{ t('history.filters.allTools') }}</option>
              <option v-for="jobType in jobTypeOptions" :key="jobType" :value="jobType">
                {{ jobLabel(jobType) }}
              </option>
            </select>
          </label>
          <div class="flex items-end">
            <Button variant="outline" class="w-full rounded-md sm:w-auto" :disabled="loading" @click="loadHistory">
              {{ t('history.actions.apply') }}
            </Button>
          </div>
        </div>

        <div v-if="loading" class="rounded-lg border border-slate-200 bg-white p-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <Loader2 class="mx-auto h-8 w-8 animate-spin text-sky-500" />
          <p class="mt-3 text-sm font-medium text-slate-600 dark:text-slate-300">{{ t('history.loading') }}</p>
        </div>

        <div v-else-if="jobs.length === 0" class="rounded-lg border border-slate-200 bg-white p-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <FileWarning class="mx-auto h-9 w-9 text-slate-400" />
          <h2 class="mt-4 text-lg font-semibold text-slate-950 dark:text-white">{{ t('history.empty.title') }}</h2>
          <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ t('history.empty.description') }}
          </p>
        </div>

        <div v-else class="min-w-0 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div class="hidden grid-cols-[1.2fr_140px_140px_150px_170px] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400 lg:grid">
            <span>{{ t('history.table.task') }}</span>
            <span>{{ t('history.table.status') }}</span>
            <span>{{ t('history.table.download') }}</span>
            <span>{{ t('history.table.created') }}</span>
            <span class="text-right">{{ t('history.table.action') }}</span>
          </div>

          <div
            v-for="job in jobs"
            :key="job.job_id"
            class="min-w-0 border-b border-slate-100 px-4 py-4 last:border-b-0 dark:border-slate-800 lg:px-5"
          >
            <div class="grid min-w-0 gap-4 lg:grid-cols-[minmax(0,1.2fr)_140px_140px_150px_170px] lg:items-center">
              <button class="min-w-0 text-left" @click="toggleDetails(job.job_id)">
                <p class="truncate text-sm font-semibold text-slate-950 dark:text-white">{{ job.input_file_name }}</p>
                <p
                  v-if="job.status === 'failed' && jobErrorSummary(job)"
                  class="mt-2 line-clamp-2 text-xs leading-5 text-rose-600 dark:text-rose-300"
                >
                  {{ jobErrorSummary(job) }}
                </p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ jobLabel(job.job_type) }} · {{ formatFileSize(job.input_file_size) }}</p>
              </button>

              <div>
                <span class="inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold" :class="statusTone(job.status)">
                  {{ t(`history.status.${job.status}`) }}
                </span>
                <div v-if="job.status === 'processing' || job.status === 'pending'" class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <div class="h-full rounded-full bg-sky-500" :style="{ width: `${job.progress || 0}%` }" />
                </div>
              </div>

              <p class="text-sm font-medium" :class="downloadTone(job.download_state)">
                {{ t(`history.downloadStates.${job.download_state}`) }}
              </p>

              <div class="text-sm text-slate-600 dark:text-slate-300">
                <p>{{ formatDate(job.created_at) }}</p>
                <p v-if="job.completed_at" class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {{ t('history.table.finished') }} {{ formatDate(job.completed_at) }}
                </p>
              </div>

              <div class="flex flex-wrap justify-start gap-2 lg:justify-end">
                <Button
                  v-if="job.download_available"
                  size="sm"
                  class="rounded-md"
                  :disabled="downloadingJobId === job.job_id"
                  @click="downloadJob(job)"
                >
                  <Loader2 v-if="downloadingJobId === job.job_id" class="mr-2 h-4 w-4 animate-spin" />
                  <ArrowDownToLine v-else class="mr-2 h-4 w-4" />
                  {{ t('history.actions.download') }}
                </Button>
                <Button variant="outline" size="sm" class="rounded-md" @click="toggleDetails(job.job_id)">
                  {{ expandedJobId === job.job_id ? t('history.actions.hideDetails') : t('history.actions.details') }}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  class="rounded-md"
                  :title="t('history.actions.copyJobId')"
                  @click="copyJobId(job.job_id)"
                >
                  <Check v-if="copiedJobId === job.job_id" class="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
                  <Copy v-else class="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div v-if="expandedJobId === job.job_id" class="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
              <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.details.referenceId') }}</p>
                  <button
                    class="mt-1 inline-flex max-w-full items-center gap-2 rounded-md border border-slate-200 bg-white px-2 py-1 text-left text-xs font-semibold text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                    @click="copyJobId(job.job_id)"
                  >
                    <span class="truncate">{{ job.job_id }}</span>
                    <Check v-if="copiedJobId === job.job_id" class="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-300" />
                    <Copy v-else class="h-3.5 w-3.5 shrink-0" />
                  </button>
                </div>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.details.started') }}</p>
                  <p class="mt-1 text-slate-800 dark:text-slate-200">{{ formatDate(job.started_at) }}</p>
                </div>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.details.completed') }}</p>
                  <p class="mt-1 text-slate-800 dark:text-slate-200">{{ formatDate(job.completed_at) }}</p>
                </div>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('history.details.progress') }}</p>
                  <p class="mt-1 text-slate-800 dark:text-slate-200">{{ job.progress }}%</p>
                </div>
              </div>
              <p v-if="job.error_message" class="mt-4 rounded-md border border-rose-200 bg-rose-50 p-3 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
                {{ jobErrorSummary(job) }}
              </p>
            </div>
          </div>
        </div>

        <p v-if="failedCount" class="text-sm text-slate-500 dark:text-slate-400">
          {{ t('history.failedHint', { count: failedCount }) }}
        </p>
      </div>
    </section>
  </div>
</template>
