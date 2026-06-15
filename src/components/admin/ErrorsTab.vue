<script setup lang="ts">
import { ClipboardCopy, Flame } from 'lucide-vue-next'
import type {
  AdminApiError,
  AdminDiagnostics,
  AdminOperations,
  AdminOverview,
} from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
  apiErrors: AdminApiError[]
  diagnostics: AdminDiagnostics | null
  operations: AdminOperations | null
  overview: AdminOverview | null
  diagnosticSummaryCopied: boolean
  savingKey: string | null
  formatDate: (value: string) => string
}>()

const emit = defineEmits<{
  refresh: []
  copyDiagnosticSummary: []
  openFeedback: [feedbackId: number]
}>()
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Diagnostics"
        title="Errors & Diagnostics"
        description="Review recent API errors, failed jobs, and user feedback together. This view keeps request bodies and document contents out of sight."
      >
        <template #actions>
          <AdminActionButton
            class="min-h-11 py-3"
            :disabled="savingKey === 'errors:refresh'"
            :loading="savingKey === 'errors:refresh'"
            @click="emit('refresh')"
          >
            Refresh diagnostics
          </AdminActionButton>
        </template>
      </AdminSectionHeader>

      <div class="mt-5 grid gap-4 md:grid-cols-3">
        <AdminStateBlock tone="danger" compact title="API errors" :description="`${diagnostics?.api_error_count ?? 0} recent errors`" />
        <AdminStateBlock tone="warning" compact title="Failed jobs" :description="`${diagnostics?.failed_jobs_count ?? operations?.failed_jobs ?? 0} recent failures`" />
        <AdminStateBlock tone="info" compact title="Open feedback" :description="`${diagnostics?.open_feedback_count ?? overview?.open_feedback_count ?? 0} items waiting`" />
      </div>

      <div class="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
        <AdminSectionHeader
          eyebrow="Summary"
          title="Diagnostic packet"
          description="A backend-generated summary useful for support handoff and incident notes. It omits request bodies and file contents."
        >
          <template #actions>
            <AdminActionButton
              tone="neutral"
              class="min-h-11 shrink-0 py-3"
              :disabled="!diagnostics?.diagnostic_summary"
              @click="emit('copyDiagnosticSummary')"
            >
              <template #icon>
                <ClipboardCopy class="h-4 w-4" />
              </template>
              {{ diagnosticSummaryCopied ? 'Copied' : 'Copy packet' }}
            </AdminActionButton>
          </template>
        </AdminSectionHeader>
        <pre
          class="mt-4 max-h-72 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-white p-4 font-mono text-[12px] leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
        >{{ diagnostics?.diagnostic_summary || 'No diagnostic summary is available yet. Refresh diagnostics to generate one.' }}</pre>
      </div>
    </AdminPanel>

    <section class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
      <AdminPanel as="article">
        <AdminSectionHeader
          eyebrow="API"
          title="Recent API errors"
          description="Prioritize path, status code, error type, and time. Use request IDs and IPs only when you need to trace a backend incident."
          :icon="Flame"
        />
        <div class="mt-4 space-y-3">
          <div
            v-for="item in apiErrors"
            :key="item.id"
            class="rounded-lg border border-rose-200 bg-slate-50 p-4 dark:border-rose-500/30 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill tone="danger">{{ item.status_code }}</StatusPill>
              <StatusPill>{{ item.method }}</StatusPill>
              <span class="text-xs text-slate-500 dark:text-slate-400">
                {{ formatDate(item.created_at) }}
              </span>
            </div>
            <p class="mt-3 break-all font-semibold text-slate-950 dark:text-white">
              {{ item.path }}
            </p>
            <p
              v-if="item.error_type || item.error_message"
              class="mt-2 whitespace-pre-wrap text-sm leading-6 text-rose-700 dark:text-rose-200"
            >
              {{ item.error_type || 'Error' }}: {{ item.error_message || item.traceback_summary || 'No short summary available.' }}
            </p>
            <p class="mt-2 break-all text-xs text-slate-500 dark:text-slate-400">
              Request ID: {{ item.request_id || 'unknown' }} · IP: {{ item.ip_address || 'unknown' }}
            </p>
          </div>
          <AdminStateBlock
            v-if="apiErrors.length === 0"
            tone="neutral"
            title="No API errors yet"
            description="If this feels wrong, refresh diagnostics and check backend logs or recent deploys."
          />
        </div>
      </AdminPanel>

      <div class="space-y-5">
        <AdminPanel as="article">
          <AdminSectionHeader
            eyebrow="Jobs"
            title="Recent failed jobs"
            description="Failed task summaries belong here. Technical traces stay folded in the job center."
          />
          <div class="mt-4 space-y-3">
            <AdminStateBlock
              v-for="job in diagnostics?.recent_failed_jobs || []"
              :key="job.job_id"
              tone="warning"
              :title="job.job_type"
              :description="job.error_message || 'No short error summary recorded.'"
            >
              <p class="break-all text-xs text-slate-500 dark:text-slate-400">{{ job.job_id }}</p>
            </AdminStateBlock>
            <AdminStateBlock
              v-if="!diagnostics?.recent_failed_jobs?.length"
              tone="neutral"
              title="No recent failed jobs"
              description="Failed background tasks will appear here once the system records them."
            />
          </div>
        </AdminPanel>

        <AdminPanel as="article">
          <AdminSectionHeader
            eyebrow="Feedback"
            title="Pending feedback"
            description="Open user reports with a clean path into the feedback module."
          />
          <div class="mt-4 space-y-3">
            <button
              v-for="item in diagnostics?.recent_feedback || []"
              :key="item.id"
              type="button"
              class="w-full rounded-md border border-sky-200 bg-sky-50 p-4 text-left transition hover:-translate-y-0.5 hover:border-sky-300 hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-500/40 dark:border-sky-500/30 dark:bg-sky-500/10 dark:hover:bg-sky-500/15"
              @click="emit('openFeedback', item.id)"
            >
              <div class="flex flex-wrap items-center gap-2">
                <StatusPill tone="info">#{{ item.id }}</StatusPill>
                <StatusPill>{{ item.status }}</StatusPill>
                <span class="ml-auto text-xs font-semibold text-sky-700 dark:text-sky-200">
                  Open details
                </span>
              </div>
              <p class="mt-2 break-words font-semibold text-slate-950 dark:text-white">
                {{ item.title }}
              </p>
              <p v-if="item.page_url" class="mt-1 break-all text-xs text-slate-500 dark:text-slate-400">
                {{ item.page_url }}
              </p>
            </button>
            <AdminStateBlock
              v-if="!diagnostics?.recent_feedback?.length"
              tone="neutral"
              title="No pending feedback"
              description="User reports will appear here after they are submitted."
            />
          </div>
        </AdminPanel>
      </div>
    </section>
  </div>
</template>
