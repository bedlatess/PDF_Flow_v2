<script setup lang="ts">
import { ClipboardCopy, RefreshCw, Save } from 'lucide-vue-next'
import type { AdminFeedback } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
  feedbackReports: AdminFeedback[]
  feedbackStatusFilter: string
  highlightedFeedbackId: number | null
  copiedFeedbackId: number | null
  savingKey: string | null
  formatDate: (value: string) => string
  parseDiagnostics: (value: string | null) => string
}>()

const emit = defineEmits<{
  'update:feedbackStatusFilter': [value: string]
  refresh: []
  cleanupLive: []
  copySummary: [report: AdminFeedback]
  save: [report: AdminFeedback]
}>()

const updateFeedbackStatusFilter = (event: Event) => {
  emit('update:feedbackStatusFilter', (event.target as HTMLSelectElement).value)
}
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Operate"
        title="Feedback Inbox"
        description="Review user-reported issues with page URL, diagnostic code, browser context, message, status, and internal notes."
      >
        <template #actions>
          <select
            :value="feedbackStatusFilter"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
            @change="updateFeedbackStatusFilter"
          >
            <option value="">All statuses</option>
            <option value="new">New</option>
            <option value="reviewing">Reviewing</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <AdminActionButton
            class="min-h-11 py-3"
            :disabled="savingKey === 'feedback:refresh'"
            :loading="savingKey === 'feedback:refresh'"
            @click="emit('refresh')"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            Refresh
          </AdminActionButton>
          <AdminActionButton
            tone="warning"
            class="min-h-11 py-3"
            :disabled="savingKey === 'feedback:cleanup-live'"
            :loading="savingKey === 'feedback:cleanup-live'"
            @click="emit('cleanupLive')"
          >
            Close acceptance feedback
          </AdminActionButton>
        </template>
      </AdminSectionHeader>

      <div class="mt-5 space-y-4">
        <article
          v-for="report in feedbackReports"
          :id="`feedback-${report.id}`"
          :key="report.id"
          class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
          :class="highlightedFeedbackId === report.id ? 'shadow-sm ring-2 ring-cyan-300/80' : ''"
        >
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <StatusPill tone="info">#{{ report.id }}</StatusPill>
                <StatusPill>{{ report.category }}</StatusPill>
                <StatusPill
                  :tone="
                    report.severity === 'critical'
                      ? 'danger'
                      : report.severity === 'high'
                        ? 'warning'
                        : 'success'
                  "
                >
                  {{ report.severity }}
                </StatusPill>
                <StatusPill>{{ report.status }}</StatusPill>
              </div>
              <p class="mt-3 break-words text-lg font-semibold text-slate-950 dark:text-white">
                {{ report.title }}
              </p>
              <div class="mt-2 max-h-72 overflow-y-auto rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                <p class="whitespace-pre-wrap break-words text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ report.message }}
                </p>
              </div>
              <div class="mt-3 space-y-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                <p>Submitted {{ formatDate(report.created_at) }} · Contact {{ report.email || 'not provided' }}</p>
                <p v-if="report.page_url" class="break-all">Page: {{ report.page_url }}</p>
                <p v-if="report.diagnostic_code">Diagnostic code: {{ report.diagnostic_code }}</p>
                <p v-if="report.user_agent" class="break-all">Browser: {{ report.user_agent }}</p>
                <div v-if="report.diagnostics" class="max-h-36 overflow-y-auto rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                  <pre class="whitespace-pre-wrap break-words font-mono text-[11px] leading-5 text-slate-500 dark:text-slate-400">{{ parseDiagnostics(report.diagnostics) }}</pre>
                </div>
              </div>
            </div>

            <div class="w-full space-y-3 xl:w-72">
              <select
                v-model="report.status"
                class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
              >
                <option value="new">New</option>
                <option value="reviewing">Reviewing</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
              <textarea
                v-model="report.admin_note"
                rows="4"
                placeholder="Internal note, e.g. reproduced, waiting for screenshot, fixed in next deploy"
                class="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm leading-6 text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
              />
              <AdminActionButton tone="neutral" full @click="emit('copySummary', report)">
                <template #icon>
                  <ClipboardCopy class="h-4 w-4" />
                </template>
                {{ copiedFeedbackId === report.id ? 'Copied' : 'Copy diagnostic summary' }}
              </AdminActionButton>
              <AdminActionButton
                tone="neutral"
                full
                :disabled="savingKey === `feedback:${report.id}`"
                :loading="savingKey === `feedback:${report.id}`"
                @click="emit('save', report)"
              >
                <template #icon>
                  <Save class="h-4 w-4" />
                </template>
                Save feedback status
              </AdminActionButton>
            </div>
          </div>
        </article>

        <AdminStateBlock
          v-if="feedbackReports.length === 0"
          tone="neutral"
          title="No matching feedback"
          description="Try another status filter or wait for users to submit reports from the feedback widget."
        />
      </div>
    </AdminPanel>
  </div>
</template>
