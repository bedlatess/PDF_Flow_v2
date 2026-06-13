<script setup lang="ts">
import { ClipboardCopy, Save } from 'lucide-vue-next'
import type { AdminFeedback } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
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
  <div class="contents">
    <AdminPanel as="section">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xl font-semibold">问题反馈</p>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            收集真实用户在页面右下角提交的问题，包含页面地址、诊断码、浏览器信息和用户描述，方便上线测试时快速复现。
          </p>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row">
          <select
            :value="feedbackStatusFilter"
            class="rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:text-white dark:focus:border-sky-400"
            @change="updateFeedbackStatusFilter"
          >
            <option value="">全部状态</option>
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
            刷新
          </AdminActionButton>
          <AdminActionButton
            tone="warning"
            class="min-h-11 py-3"
            :disabled="savingKey === 'feedback:cleanup-live'"
            :loading="savingKey === 'feedback:cleanup-live'"
            @click="emit('cleanupLive')"
          >
            关闭验收反馈
          </AdminActionButton>
        </div>
      </div>

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
              </div>
              <p class="mt-3 break-words text-lg font-semibold text-slate-950 dark:text-white">
                {{ report.title }}
              </p>
              <div
                class="mt-2 max-h-72 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
              >
                <p
                  class="whitespace-pre-wrap break-words text-sm leading-6 text-slate-600 dark:text-slate-300"
                >
                  {{ report.message }}
                </p>
              </div>
              <div class="mt-3 space-y-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                <p>
                  提交：{{ formatDate(report.created_at) }} · 联系：{{ report.email || '未提供' }}
                </p>
                <p v-if="report.page_url" class="break-all">页面：{{ report.page_url }}</p>
                <p v-if="report.diagnostic_code">诊断码：{{ report.diagnostic_code }}</p>
                <p v-if="report.user_agent" class="break-all">浏览器：{{ report.user_agent }}</p>
                <div
                  v-if="report.diagnostics"
                  class="max-h-36 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
                >
                  <pre
                    class="whitespace-pre-wrap break-words font-mono text-[11px] leading-5 text-slate-500 dark:text-slate-400"
                    >{{ parseDiagnostics(report.diagnostics) }}</pre
                  >
                </div>
              </div>
            </div>

            <div class="w-full space-y-3 xl:w-72">
              <select
                v-model="report.status"
                class="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:text-white dark:focus:border-sky-400"
              >
                <option value="new">New</option>
                <option value="reviewing">Reviewing</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
              <textarea
                v-model="report.admin_note"
                rows="4"
                placeholder="内部备注，例如：已复现 / 等截图 / 已修复待上线"
                class="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm leading-6 text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:text-slate-400 dark:text-white dark:focus:border-sky-400"
              />
              <AdminActionButton tone="neutral" full @click="emit('copySummary', report)">
                <template #icon>
                  <ClipboardCopy class="h-4 w-4" />
                </template>
                {{ copiedFeedbackId === report.id ? '已复制摘要' : '复制诊断摘要' }}
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
                保存反馈状态
              </AdminActionButton>
            </div>
          </div>
        </article>

        <div
          v-if="feedbackReports.length === 0"
          class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
        >
          当前没有匹配的问题反馈。用户可通过页面右下角“反馈问题”提交。
        </div>
      </div>
    </AdminPanel>
  </div>
</template>
