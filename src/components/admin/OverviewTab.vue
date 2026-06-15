<script setup lang="ts">
import { computed } from 'vue'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ClipboardCopy,
  CreditCard,
  Network,
  RefreshCw,
  Server,
  AlertTriangle,
} from 'lucide-vue-next'
import type {
  AdminDiagnostics,
  AdminHealthReport,
  AdminJob,
  AdminMaintenance,
  AdminOperations,
  AdminOverview,
  AdminPaymentSummary,
  AdminServiceProviderConfig,
} from '@/admin/api'
import type { ControlRoomTabId } from '@/admin/control-room/types'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  overview: AdminOverview | null
  operations: AdminOperations | null
  jobs: AdminJob[]
  healthReport: AdminHealthReport | null
  healthReportSummary: string
  healthReportCopied: boolean
  savingKey: string | null
  paymentSummary: AdminPaymentSummary | null
  serviceProviderConfigs: AdminServiceProviderConfig[]
  diagnostics: AdminDiagnostics | null
  maintenance: AdminMaintenance | null
  formatDate: (value: string) => string
}>()

const emit = defineEmits<{
  refreshAll: []
  refreshHealthReport: []
  copyHealthReport: []
  navigate: [tabId: ControlRoomTabId]
}>()

type AttentionItem = {
  key: string
  title: string
  detail: string
  tone: 'warning' | 'danger' | 'info'
  target: ControlRoomTabId
}

const services = computed(() => props.operations?.services ?? {})
const unhealthyServices = computed(() =>
  Object.entries(services.value).filter(([, service]) => service.status !== 'healthy'),
)
const paymentProviders = computed(() => props.paymentSummary?.providers ?? [])
const paymentReviewProviders = computed(() =>
  paymentProviders.value.filter(
    (provider) =>
      provider.missing_config_keys.length > 0 ||
      provider.acceptance_status === 'needs_review' ||
      provider.acceptance_status === 'missing_config',
  ),
)
const readyPaymentCount = computed(
  () => paymentProviders.value.filter((provider) => provider.configured).length,
)
const enabledPaymentCount = computed(
  () => paymentProviders.value.filter((provider) => provider.enabled).length,
)
const enabledServiceProviders = computed(() =>
  props.serviceProviderConfigs.filter((provider) => provider.enabled),
)
const serviceProviderReview = computed(
  () => enabledServiceProviders.value.filter((provider) => provider.readiness.status !== 'ready'),
)
const failedJobCount = computed(
  () => props.operations?.failed_jobs ?? props.overview?.failed_jobs_count ?? 0,
)
const runningJobCount = computed(() => props.operations?.running_jobs ?? 0)
const openFeedbackCount = computed(
  () => props.diagnostics?.open_feedback_count ?? props.overview?.open_feedback_count ?? 0,
)
const apiErrorCount = computed(
  () => props.diagnostics?.api_error_count ?? props.overview?.api_error_count ?? 0,
)
const cleanupCount = computed(
  () =>
    (props.maintenance?.test_users_count ?? 0) +
    (props.maintenance?.live_acceptance_feedback_count ?? 0) +
    (props.maintenance?.file_retention?.removable_count ?? 0),
)

const attentionItems = computed<AttentionItem[]>(() => {
  const items: AttentionItem[] = []
  if (unhealthyServices.value.length) {
    items.push({
      key: 'services',
      title: `${unhealthyServices.value.length} service issue${unhealthyServices.value.length > 1 ? 's' : ''}`,
      detail: unhealthyServices.value.map(([name]) => name).join(', '),
      tone: 'danger',
      target: 'errors',
    })
  }
  if (paymentReviewProviders.value.length) {
    items.push({
      key: 'payments',
      title: `${paymentReviewProviders.value.length} payment provider${paymentReviewProviders.value.length > 1 ? 's' : ''} need review`,
      detail: paymentReviewProviders.value.map((provider) => provider.display_name).join(', '),
      tone: 'warning',
      target: 'paymentSetup',
    })
  }
  if (serviceProviderReview.value.length) {
    items.push({
      key: 'providers',
      title: `${serviceProviderReview.value.length} service provider${serviceProviderReview.value.length > 1 ? 's' : ''} not ready`,
      detail: serviceProviderReview.value.map((provider) => provider.display_name).join(', '),
      tone: 'warning',
      target: 'serviceProviders',
    })
  }
  if (failedJobCount.value) {
    items.push({
      key: 'failed-jobs',
      title: `${failedJobCount.value} failed job${failedJobCount.value > 1 ? 's' : ''}`,
      detail: 'Review recent failures and customer-facing conversion impact.',
      tone: 'warning',
      target: 'jobs',
    })
  }
  if (apiErrorCount.value) {
    items.push({
      key: 'api-errors',
      title: `${apiErrorCount.value} recent API error${apiErrorCount.value > 1 ? 's' : ''}`,
      detail: props.diagnostics?.recent_errors?.[0]?.path || 'Open diagnostics for the latest error paths.',
      tone: 'danger',
      target: 'errors',
    })
  }
  if (openFeedbackCount.value) {
    items.push({
      key: 'feedback',
      title: `${openFeedbackCount.value} open feedback report${openFeedbackCount.value > 1 ? 's' : ''}`,
      detail: props.diagnostics?.recent_feedback?.[0]?.title || 'Triage new user feedback.',
      tone: 'info',
      target: 'feedback',
    })
  }
  if (cleanupCount.value) {
    items.push({
      key: 'maintenance',
      title: `${cleanupCount.value} maintenance item${cleanupCount.value > 1 ? 's' : ''}`,
      detail: 'Review cleanup counts before running any destructive maintenance action.',
      tone: 'warning',
      target: 'maintenance',
    })
  }
  return items
})

const systemTone = computed(() => {
  if (unhealthyServices.value.length || apiErrorCount.value) return 'danger'
  if (attentionItems.value.length) return 'warning'
  return 'success'
})
const systemLabel = computed(() => {
  if (systemTone.value === 'danger') return 'Needs attention'
  if (systemTone.value === 'warning') return 'Review recommended'
  return 'Healthy'
})
const systemDetail = computed(() => {
  if (systemTone.value === 'danger') return 'Service health or API errors need investigation.'
  if (systemTone.value === 'warning') return 'Core services are online, but some operational items need review.'
  return 'Core services and readiness checks look clean.'
})

const serviceTone = (status?: string) => {
  if (status === 'healthy') return 'success'
  if (status === 'unhealthy') return 'danger'
  if (status === 'degraded') return 'warning'
  return 'neutral'
}

const attentionPanelClass = (tone: AttentionItem['tone']) => {
  if (tone === 'danger') return 'border-rose-200 bg-rose-50 dark:border-rose-500/30 dark:bg-rose-500/10'
  if (tone === 'warning') return 'border-amber-200 bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/10'
  return 'border-sky-200 bg-sky-50 dark:border-sky-500/30 dark:bg-sky-500/10'
}

const attentionTextClass = (tone: AttentionItem['tone']) => {
  if (tone === 'danger') return 'text-rose-700 dark:text-rose-200'
  if (tone === 'warning') return 'text-amber-800 dark:text-amber-100'
  return 'text-sky-800 dark:text-sky-100'
}

const recentFailedJobs = computed(() => props.operations?.recent_failed_jobs ?? [])
const recentErrors = computed(() => props.diagnostics?.recent_errors ?? [])
const recentFeedback = computed(() => props.diagnostics?.recent_feedback ?? [])
</script>

<template>
  <div class="space-y-5">
    <section class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
      <AdminPanel as="article" :tone="systemTone" padding="lg">
        <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <AdminSectionHeader
            eyebrow="Command Center"
            title="Overview"
            :description="`${systemDetail} This dashboard only points you to the right module; it does not run destructive actions.`"
            :icon="systemTone === 'success' ? CheckCircle2 : systemTone === 'warning' ? AlertTriangle : AlertCircle"
          >
            <template #badges>
              <StatusPill :tone="systemTone">{{ systemLabel }}</StatusPill>
            </template>
          </AdminSectionHeader>
          <div class="flex flex-col gap-2 sm:flex-row">
            <AdminActionButton
              tone="neutral"
              :disabled="savingKey === 'health-report:refresh'"
              :loading="savingKey === 'health-report:refresh'"
              @click="emit('refreshHealthReport')"
            >
              <template #icon>
                <RefreshCw class="h-4 w-4" />
              </template>
              Refresh health
            </AdminActionButton>
            <AdminActionButton
              tone="neutral"
              @click="emit('copyHealthReport')"
            >
              <template #icon>
                <ClipboardCopy class="h-4 w-4" />
              </template>
              {{ healthReportCopied ? 'Copied' : 'Copy report' }}
            </AdminActionButton>
          </div>
        </div>

        <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <AdminStateBlock
            tone="neutral"
            compact
            title="Environment"
            :description="healthReport?.environment || 'unknown'"
          >
            <span class="break-all text-xs">{{ healthReport?.app_version || 'version pending' }}</span>
          </AdminStateBlock>
          <AdminStateBlock
            tone="neutral"
            compact
            title="Services"
            :description="`${Object.keys(services).length - unhealthyServices.length}/${Object.keys(services).length} healthy`"
          />
          <AdminStateBlock
            tone="neutral"
            compact
            title="Payment"
            :description="`${readyPaymentCount}/${paymentProviders.length} configured, ${enabledPaymentCount} enabled`"
          />
          <AdminStateBlock
            tone="neutral"
            compact
            title="Jobs"
            :description="`${runningJobCount} running, ${failedJobCount} failed recently`"
          />
        </div>
      </AdminPanel>

      <AdminPanel as="article" padding="lg">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-lg font-semibold text-slate-950 dark:text-white">Attention Queue</h3>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Prioritized signals from health, providers, payments, jobs, errors, feedback, and maintenance.
            </p>
          </div>
          <StatusPill :tone="attentionItems.length ? 'warning' : 'success'">
            {{ attentionItems.length ? `${attentionItems.length} items` : 'Clear' }}
          </StatusPill>
        </div>

        <div class="mt-5 space-y-3">
          <button
            v-for="item in attentionItems"
            :key="item.key"
            type="button"
            class="w-full rounded-md border p-4 text-left transition hover:-translate-y-0.5 hover:shadow-sm"
            :class="attentionPanelClass(item.tone)"
            @click="emit('navigate', item.target)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="font-semibold" :class="attentionTextClass(item.tone)">{{ item.title }}</p>
                <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ item.detail }}</p>
              </div>
              <ArrowRight class="mt-1 h-4 w-4 shrink-0 text-slate-500 dark:text-slate-300" />
            </div>
          </button>

          <div
            v-if="!attentionItems.length"
            class="rounded-md border border-emerald-200 bg-emerald-50 p-6 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100"
          >
            No immediate operational attention items. Keep an eye on jobs, payments, and feedback after traffic changes.
          </div>
        </div>
      </AdminPanel>
    </section>

    <section class="grid gap-5 xl:grid-cols-3">
      <AdminPanel as="article">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <Server class="h-5 w-5 text-slate-600 dark:text-slate-300" />
              <h3 class="font-semibold text-slate-950 dark:text-white">System Health</h3>
            </div>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Backend, queue, database, and cache.</p>
          </div>
          <AdminActionButton tone="neutral" @click="emit('refreshAll')">Refresh</AdminActionButton>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="(service, name) in services"
            :key="name"
            class="flex items-start justify-between gap-3 rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="min-w-0">
              <p class="font-semibold text-slate-950 dark:text-white">{{ name }}</p>
              <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ service.detail || 'No detail' }}</p>
            </div>
            <StatusPill :tone="serviceTone(service.status)">{{ service.status }}</StatusPill>
          </div>
        </div>
      </AdminPanel>

      <AdminPanel as="article">
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <CreditCard class="h-5 w-5 text-slate-600 dark:text-slate-300" />
              <h3 class="font-semibold text-slate-950 dark:text-white">Payment Readiness</h3>
            </div>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Configuration readiness, not real-payment validation.</p>
          </div>
          <AdminActionButton tone="neutral" @click="emit('navigate', 'paymentSetup')">Open</AdminActionButton>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="provider in paymentProviders"
            :key="provider.key"
            class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="font-semibold text-slate-950 dark:text-white">{{ provider.display_name }}</p>
              <div class="flex flex-wrap gap-2">
                <StatusPill :tone="provider.enabled ? 'success' : 'neutral'">{{ provider.enabled ? 'enabled' : 'disabled' }}</StatusPill>
                <StatusPill :tone="provider.configured ? 'success' : 'warning'">{{ provider.configured ? 'configured' : 'missing config' }}</StatusPill>
              </div>
            </div>
            <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ provider.acceptance_detail }}</p>
          </div>
        </div>
      </AdminPanel>

      <AdminPanel as="article">
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <Network class="h-5 w-5 text-slate-600 dark:text-slate-300" />
              <h3 class="font-semibold text-slate-950 dark:text-white">Provider Readiness</h3>
            </div>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">OCR, Office, and AI runtime provider status.</p>
          </div>
          <AdminActionButton tone="neutral" @click="emit('navigate', 'serviceProviders')">Open</AdminActionButton>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="provider in serviceProviderConfigs"
            :key="`${provider.service_key}:${provider.provider_key}`"
            class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="font-semibold text-slate-950 dark:text-white">{{ provider.display_name }}</p>
              <div class="flex flex-wrap gap-2">
                <StatusPill :tone="provider.enabled ? 'success' : 'neutral'">{{ provider.enabled ? 'enabled' : 'disabled' }}</StatusPill>
                <StatusPill :tone="provider.readiness.status === 'ready' ? 'success' : 'warning'">{{ provider.readiness.label }}</StatusPill>
              </div>
            </div>
            <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ provider.readiness.detail }}</p>
          </div>
        </div>
      </AdminPanel>
    </section>

    <section class="grid gap-5 xl:grid-cols-3">
      <AdminPanel as="article">
        <div class="flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-950 dark:text-white">Recent Failed Jobs</h3>
          <AdminActionButton tone="neutral" @click="emit('navigate', 'jobs')">Open jobs</AdminActionButton>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="job in recentFailedJobs.slice(0, 4)"
            :key="job.job_id"
            class="rounded-md border border-rose-200 bg-rose-50 p-3 dark:border-rose-500/30 dark:bg-rose-500/10"
          >
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill tone="danger">{{ job.job_type }}</StatusPill>
              <span class="text-xs text-rose-700 dark:text-rose-200/70">{{ formatDate(job.created_at) }}</span>
            </div>
            <p class="mt-2 break-all font-mono text-xs text-slate-600 dark:text-slate-300">{{ job.job_id }}</p>
            <p class="mt-2 text-sm leading-6 text-rose-700 dark:text-rose-200">{{ job.error_message || 'No error summary' }}</p>
          </div>
          <p v-if="!recentFailedJobs.length" class="rounded-md border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400">
            No recent failed jobs.
          </p>
        </div>
      </AdminPanel>

      <AdminPanel as="article">
        <div class="flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-950 dark:text-white">Recent Errors</h3>
          <AdminActionButton tone="neutral" @click="emit('navigate', 'errors')">Open diagnostics</AdminActionButton>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="apiError in recentErrors.slice(0, 4)"
            :key="apiError.id"
            class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill tone="danger">{{ apiError.status_code }}</StatusPill>
              <span class="text-xs text-slate-500 dark:text-slate-400">{{ formatDate(apiError.created_at) }}</span>
            </div>
            <p class="mt-2 break-all text-sm font-semibold text-slate-950 dark:text-white">{{ apiError.method }} {{ apiError.path }}</p>
            <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ apiError.error_message || apiError.error_type || 'No summary' }}</p>
          </div>
          <p v-if="!recentErrors.length" class="rounded-md border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400">
            No recent API errors.
          </p>
        </div>
      </AdminPanel>

      <AdminPanel as="article">
        <div class="flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-950 dark:text-white">Recent Feedback</h3>
          <AdminActionButton tone="neutral" @click="emit('navigate', 'feedback')">Open inbox</AdminActionButton>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="feedback in recentFeedback.slice(0, 4)"
            :key="feedback.id"
            class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill tone="info">{{ feedback.severity }}</StatusPill>
              <StatusPill tone="neutral">{{ feedback.status }}</StatusPill>
            </div>
            <p class="mt-2 text-sm font-semibold text-slate-950 dark:text-white">{{ feedback.title }}</p>
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ formatDate(feedback.created_at) }}</p>
          </div>
          <p v-if="!recentFeedback.length" class="rounded-md border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400">
            No recent feedback.
          </p>
        </div>
      </AdminPanel>
    </section>
  </div>
</template>
