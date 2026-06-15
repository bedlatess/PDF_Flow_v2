<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  ChevronDown,
  ChevronUp,
  ClipboardCopy,
  Clock3,
  FileText,
  RefreshCw,
  Search,
} from 'lucide-vue-next'
import type { AdminJob } from '@/admin/api'
import { formatAdminBytes } from '@/admin/control-room/formatters'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  filteredJobs: AdminJob[]
  jobSearch: string
  jobStatusFilter: string
  savingKey: string | null
  formatDate: (value: string) => string
}>()

const emit = defineEmits<{
  'update:jobSearch': [value: string]
  'update:jobStatusFilter': [value: string]
  refresh: []
}>()

const sourceFilter = ref('')
const jobTypeFilter = ref('')
const expandedJobIds = ref<Set<string>>(new Set())
const copiedJobId = ref<string | null>(null)

const updateJobSearch = (event: Event) => {
  emit('update:jobSearch', (event.target as HTMLInputElement).value)
}

const updateJobStatusFilter = (event: Event) => {
  emit('update:jobStatusFilter', (event.target as HTMLSelectElement).value)
}

const updateSourceFilter = (event: Event) => {
  sourceFilter.value = (event.target as HTMLSelectElement).value
}

const updateJobTypeFilter = (event: Event) => {
  jobTypeFilter.value = (event.target as HTMLSelectElement).value
}

const statusTone = (status: string) => {
  if (status === 'failed') return 'danger'
  if (status === 'completed') return 'success'
  if (status === 'processing') return 'info'
  return 'warning'
}

const statusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: 'Queued',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
    cancelled: 'Cancelled',
  }
  return labels[status] || status
}

const statusDescription = (job: AdminJob) => {
  if (job.status === 'pending') return 'Waiting for a worker.'
  if (job.status === 'processing') return 'Worker is processing the file.'
  if (job.status === 'completed') return job.output_file_url ? 'Result is available.' : 'Completed without a result link.'
  if (job.status === 'failed') return readableError(job)
  return 'No extra status detail.'
}

const jobTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    compress_pdf: 'Compress PDF',
    merge_pdf: 'Merge PDF',
    merge_pdfs: 'Merge PDF',
    split_pdf: 'Split PDF',
    rotate_pdf: 'Rotate PDF',
    image_to_pdf: 'Image to PDF',
    convert_images_to_pdf: 'Image to PDF',
    pdf_to_image: 'PDF to Image',
    pdf_to_images: 'PDF to Image',
    convert_pdf_to_images: 'PDF to Image',
    ocr_pdf: 'OCR PDF',
    extract_text: 'Extract Text',
    office_to_pdf: 'Office to PDF',
    html_to_pdf: 'HTML to PDF',
    processing_job: 'Compatibility Job',
  }
  return labels[type] || type.replace(/_/g, ' ')
}

const jobSources = (job: AdminJob) => job.sources?.length ? job.sources : [job.source].filter(Boolean)

const sourceKind = (job: AdminJob) => {
  const sources = jobSources(job)
  if (sources.includes('db') && sources.includes('redis')) return 'mixed'
  if (sources.includes('db')) return 'db'
  if (sources.includes('redis')) return 'redis'
  return 'unknown'
}

const sourceLabel = (job: AdminJob) => {
  const kind = sourceKind(job)
  if (kind === 'mixed') return 'Mixed'
  if (kind === 'db') return 'DB history'
  if (kind === 'redis') return 'Redis active'
  return job.source || 'Unknown'
}

const sourceDescription = (job: AdminJob) => {
  const kind = sourceKind(job)
  if (kind === 'mixed') return 'Active state plus durable record.'
  if (kind === 'db') return 'Durable history record.'
  if (kind === 'redis') return 'Current activity state.'
  return 'Source is not recognized.'
}

const sourceTone = (job: AdminJob) => {
  const kind = sourceKind(job)
  if (kind === 'mixed') return 'success'
  if (kind === 'db') return 'info'
  if (kind === 'redis') return 'warning'
  return 'neutral'
}

const parseTime = (value: string | null) => {
  if (!value) return null
  const time = new Date(value).getTime()
  return Number.isFinite(time) ? time : null
}

const finishedAt = (job: AdminJob) => job.completed_at || job.started_at || job.created_at

const durationText = (job: AdminJob) => {
  const start = parseTime(job.started_at) ?? parseTime(job.created_at)
  const end = parseTime(job.completed_at) ?? (['pending', 'processing'].includes(job.status) ? Date.now() : parseTime(finishedAt(job)))
  if (!start || !end || end < start) return 'Unknown'
  const seconds = Math.max(0, Math.round((end - start) / 1000))
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remaining = seconds % 60
  if (minutes < 60) return `${minutes}m ${remaining}s`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ${minutes % 60}m`
}

const readableError = (job: AdminJob) => {
  const raw = (job.error_message || '').trim()
  if (!raw) return 'No error message was recorded.'
  const firstLine = raw.split(/\r?\n/)[0] || raw
  return firstLine.length > 140 ? `${firstLine.slice(0, 137)}...` : firstLine
}

const hasResult = (job: AdminJob) => job.status === 'completed' && Boolean(job.output_file_url)

const toggleDetails = (jobId: string) => {
  const next = new Set(expandedJobIds.value)
  if (next.has(jobId)) {
    next.delete(jobId)
  } else {
    next.add(jobId)
  }
  expandedJobIds.value = next
}

const copyJobId = async (jobId: string) => {
  await navigator.clipboard?.writeText(jobId)
  copiedJobId.value = jobId
  window.setTimeout(() => {
    if (copiedJobId.value === jobId) copiedJobId.value = null
  }, 1600)
}

const jobTypeOptions = computed(() =>
  Array.from(new Set(props.filteredJobs.map((job) => job.job_type)))
    .sort((a, b) => jobTypeLabel(a).localeCompare(jobTypeLabel(b))),
)

const displayedJobs = computed(() =>
  props.filteredJobs
    .filter((job) => !jobTypeFilter.value || job.job_type === jobTypeFilter.value)
    .filter((job) => !sourceFilter.value || sourceKind(job) === sourceFilter.value)
    .slice()
    .sort((a, b) => (parseTime(b.created_at) ?? 0) - (parseTime(a.created_at) ?? 0)),
)

const last24hCutoff = computed(() => Date.now() - 24 * 60 * 60 * 1000)

const isRecent = (value: string | null) => {
  const time = parseTime(value)
  return Boolean(time && time >= last24hCutoff.value)
}

const mostFailingJobType = computed(() => {
  const counts = new Map<string, number>()
  for (const job of props.filteredJobs) {
    if (job.status !== 'failed') continue
    counts.set(job.job_type, (counts.get(job.job_type) ?? 0) + 1)
  }
  const [type, count] = Array.from(counts.entries()).sort((a, b) => b[1] - a[1])[0] ?? []
  return type ? `${jobTypeLabel(type)} (${count})` : 'None'
})

const summary = computed(() => ({
  running: props.filteredJobs.filter((job) => ['pending', 'processing'].includes(job.status)).length,
  failed24h: props.filteredJobs.filter((job) => job.status === 'failed' && isRecent(job.completed_at || job.created_at)).length,
  completed24h: props.filteredJobs.filter((job) => job.status === 'completed' && isRecent(job.completed_at || job.created_at)).length,
  durable: props.filteredJobs.filter((job) => job.is_durable).length,
  redisOnly: props.filteredJobs.filter((job) => sourceKind(job) === 'redis').length,
  mostFailing: mostFailingJobType.value,
}))
</script>

<template>
  <div class="contents">
    <AdminPanel as="section" padding="lg">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div class="max-w-3xl">
          <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            <Clock3 class="h-4 w-4" />
            Job Center
          </div>
          <h3 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">Readable task operations</h3>
          <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Review recent file tasks by human outcome first: what ran, who started it, whether a result exists, and what failed.
            Technical source fields stay folded until you need deeper debugging.
          </p>
        </div>
        <AdminActionButton
          tone="neutral"
          :disabled="savingKey === 'jobs:refresh'"
          :loading="savingKey === 'jobs:refresh'"
          @click="emit('refresh')"
        >
          <template #icon>
            <RefreshCw class="h-4 w-4" />
          </template>
          Refresh jobs
        </AdminActionButton>
      </div>

      <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Running now</p>
          <p class="mt-2 text-3xl font-semibold text-slate-950 dark:text-white">{{ summary.running }}</p>
        </div>
        <div class="rounded-md border border-rose-200 bg-rose-50 p-4 dark:border-rose-500/30 dark:bg-rose-500/10">
          <p class="text-xs font-semibold uppercase text-rose-700 dark:text-rose-200/75">Failed 24h</p>
          <p class="mt-2 text-3xl font-semibold text-rose-800 dark:text-rose-100">{{ summary.failed24h }}</p>
        </div>
        <div class="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-200/75">Completed 24h</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">{{ summary.completed24h }}</p>
        </div>
        <div class="rounded-md border border-sky-200 bg-sky-50 p-4 dark:border-sky-500/30 dark:bg-sky-500/10">
          <p class="text-xs font-semibold uppercase text-sky-700 dark:text-sky-200/75">Durable jobs</p>
          <p class="mt-2 text-3xl font-semibold text-sky-800 dark:text-sky-100">{{ summary.durable }}</p>
        </div>
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-xs font-semibold uppercase text-amber-700 dark:text-amber-200/75">Redis-only</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">{{ summary.redisOnly }}</p>
        </div>
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Most failing</p>
          <p class="mt-2 text-sm font-semibold leading-6 text-slate-950 dark:text-white">{{ summary.mostFailing }}</p>
        </div>
      </div>

      <div class="mt-6 grid gap-3 lg:grid-cols-[minmax(240px,1fr)_180px_220px_180px]">
        <label class="relative block">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            :value="jobSearch"
            type="search"
            placeholder="Search job ID, user, file, type, or error"
            class="min-h-11 w-full rounded-md border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
            @input="updateJobSearch"
          >
        </label>
        <select
          :value="jobStatusFilter"
          class="min-h-11 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
          @change="updateJobStatusFilter"
        >
          <option value="">All statuses</option>
          <option value="pending">Queued</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          :value="jobTypeFilter"
          class="min-h-11 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
          @change="updateJobTypeFilter"
        >
          <option value="">All task types</option>
          <option v-for="type in jobTypeOptions" :key="type" :value="type">
            {{ jobTypeLabel(type) }}
          </option>
        </select>
        <select
          :value="sourceFilter"
          class="min-h-11 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
          @change="updateSourceFilter"
        >
          <option value="">All sources</option>
          <option value="mixed">Mixed</option>
          <option value="redis">Redis-only</option>
          <option value="db">DB-only</option>
        </select>
      </div>

      <div v-if="displayedJobs.length" class="mt-5 space-y-3">
        <article
          v-for="job in displayedJobs"
          :key="job.job_id"
          class="overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950/30"
        >
          <div class="grid gap-4 p-4 xl:grid-cols-[minmax(220px,1.1fr)_minmax(180px,0.8fr)_minmax(180px,0.8fr)_minmax(180px,0.8fr)_auto] xl:items-start">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <StatusPill tone="info">{{ jobTypeLabel(job.job_type) }}</StatusPill>
                <StatusPill :tone="statusTone(job.status)">{{ statusLabel(job.status) }}</StatusPill>
              </div>
              <p class="mt-3 truncate text-sm font-semibold text-slate-950 dark:text-white">
                {{ job.input_file_name || 'No input file name' }}
              </p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {{ job.user_email || (job.user_id ? `User #${job.user_id}` : 'Anonymous user') }}
              </p>
            </div>

            <div>
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Progress</p>
              <div class="mt-2 flex items-center gap-3">
                <div class="h-2 min-w-0 flex-1 rounded-full bg-slate-100 dark:bg-slate-800">
                  <div
                    class="h-2 rounded-full"
                    :class="job.status === 'failed' ? 'bg-rose-500' : job.status === 'completed' ? 'bg-emerald-500' : 'bg-sky-500'"
                    :style="{ width: `${Math.min(Math.max(job.progress, 0), 100)}%` }"
                  />
                </div>
                <span class="w-10 text-right text-xs font-semibold text-slate-600 dark:text-slate-300">{{ job.progress }}%</span>
              </div>
              <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ statusDescription(job) }}</p>
            </div>

            <div class="text-sm">
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Timing</p>
              <p class="mt-2 text-slate-950 dark:text-white">{{ formatDate(job.created_at) }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {{ job.completed_at ? `Completed ${formatDate(job.completed_at)}` : `Elapsed ${durationText(job)}` }}
              </p>
            </div>

            <div>
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Result</p>
              <div class="mt-2 flex flex-wrap gap-2">
                <StatusPill :tone="hasResult(job) ? 'success' : job.status === 'failed' ? 'danger' : 'neutral'">
                  {{ hasResult(job) ? 'Result available' : job.status === 'failed' ? 'No result' : 'Waiting' }}
                </StatusPill>
                <StatusPill :tone="sourceTone(job)">{{ sourceLabel(job) }}</StatusPill>
              </div>
              <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ sourceDescription(job) }}</p>
            </div>

            <div class="flex flex-col gap-2 sm:flex-row xl:flex-col">
              <AdminActionButton
                tone="neutral"
                class="min-h-10 whitespace-nowrap px-3"
                @click="copyJobId(job.job_id)"
              >
                <template #icon>
                  <ClipboardCopy class="h-4 w-4" />
                </template>
                {{ copiedJobId === job.job_id ? 'Copied' : 'Copy ID' }}
              </AdminActionButton>
              <AdminActionButton
                tone="neutral"
                class="min-h-10 whitespace-nowrap px-3"
                @click="toggleDetails(job.job_id)"
              >
                <template #icon>
                  <ChevronUp v-if="expandedJobIds.has(job.job_id)" class="h-4 w-4" />
                  <ChevronDown v-else class="h-4 w-4" />
                </template>
                Details
              </AdminActionButton>
            </div>
          </div>

          <div
            v-if="job.error_message"
            class="mx-4 mb-4 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100"
          >
            <p class="font-semibold">Failure summary</p>
            <p class="mt-1 leading-6">{{ readableError(job) }}</p>
          </div>

          <div
            v-if="expandedJobIds.has(job.job_id)"
            data-testid="job-technical-details"
            class="border-t border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/60"
          >
            <div class="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              <FileText class="h-4 w-4" />
              Technical details
            </div>
            <dl class="mt-4 grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-3">
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">job_id</dt>
                <dd class="mt-1 break-all font-mono text-xs text-slate-700 dark:text-slate-200">{{ job.job_id }}</dd>
              </div>
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">source / sources / durable</dt>
                <dd class="mt-1 text-slate-700 dark:text-slate-200">
                  {{ job.source || 'unknown' }} / {{ jobSources(job).join(', ') || 'unknown' }} / {{ job.is_durable ? 'yes' : 'no' }}
                </dd>
              </div>
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">DB / Redis mode</dt>
                <dd class="mt-1 text-slate-700 dark:text-slate-200">{{ sourceLabel(job) }}</dd>
              </div>
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">output_file_url</dt>
                <dd class="mt-1 break-all font-mono text-xs text-slate-700 dark:text-slate-200">{{ job.output_file_url || 'none' }}</dd>
              </div>
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">user_id / input size</dt>
                <dd class="mt-1 text-slate-700 dark:text-slate-200">
                  {{ job.user_id ?? 'anonymous' }} / {{ formatAdminBytes(job.input_file_size) }}
                </dd>
              </div>
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">started / completed</dt>
                <dd class="mt-1 text-slate-700 dark:text-slate-200">
                  {{ job.started_at ? formatDate(job.started_at) : 'not started' }} / {{ job.completed_at ? formatDate(job.completed_at) : 'not completed' }}
                </dd>
              </div>
              <div class="min-w-0 rounded-md border border-slate-200 bg-white p-3 md:col-span-2 xl:col-span-3 dark:border-slate-800 dark:bg-slate-900">
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">raw error</dt>
                <dd class="mt-1 whitespace-pre-wrap break-words font-mono text-xs leading-5 text-slate-700 dark:text-slate-200">{{ job.error_message || 'none' }}</dd>
              </div>
            </dl>
          </div>
        </article>
      </div>

      <div
        v-else
        class="mt-5 rounded-lg border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
      >
        No jobs match the current filters. Try clearing the search, status, type, or source filter.
      </div>
    </AdminPanel>
  </div>
</template>
