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
    <AdminPanel as="section">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xl font-semibold">错误观察</p>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            把最近 API 500
            错误、失败任务和用户反馈放在一起看。这里不会记录请求体或文件内容，只保留排查所需的摘要信息。
          </p>
        </div>
        <AdminActionButton
          class="min-h-11 py-3"
          :disabled="savingKey === 'errors:refresh'"
          :loading="savingKey === 'errors:refresh'"
          @click="emit('refresh')"
        >
          刷新诊断
        </AdminActionButton>
      </div>

      <div class="mt-5 grid gap-4 md:grid-cols-3">
        <AdminPanel as="div" tone="danger" padding="sm">
          <p class="text-sm text-rose-700 dark:text-rose-200/70">API 错误</p>
          <p class="mt-2 text-3xl font-semibold text-rose-800 dark:text-rose-100">
            {{ diagnostics?.api_error_count ?? 0 }}
          </p>
        </AdminPanel>
        <AdminPanel as="div" tone="warning" padding="sm">
          <p class="text-sm text-amber-700 dark:text-amber-200/70">失败任务</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ diagnostics?.failed_jobs_count ?? operations?.failed_jobs ?? 0 }}
          </p>
        </AdminPanel>
        <AdminPanel as="div" tone="info" padding="sm">
          <p class="text-sm text-sky-700 dark:text-sky-200/70">待处理反馈</p>
          <p class="mt-2 text-3xl font-semibold text-sky-800 dark:text-sky-100">
            {{ diagnostics?.open_feedback_count ?? overview?.open_feedback_count ?? 0 }}
          </p>
        </AdminPanel>
      </div>

      <div
        class="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
      >
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="font-semibold text-slate-950 dark:text-white">诊断排障包</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              后端生成的安全摘要，方便粘贴到工单或发布验收记录；不包含请求体或文件内容。
            </p>
          </div>
          <AdminActionButton
            tone="neutral"
            class="min-h-11 shrink-0 py-3"
            :disabled="!diagnostics?.diagnostic_summary"
            @click="emit('copyDiagnosticSummary')"
          >
            <template #icon>
              <ClipboardCopy class="h-4 w-4" />
            </template>
            {{ diagnosticSummaryCopied ? '已复制排障包' : '复制排障包' }}
          </AdminActionButton>
        </div>
        <pre
          class="mt-4 max-h-72 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-white p-4 font-mono text-[12px] leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
          >{{ diagnostics?.diagnostic_summary || '暂无诊断摘要，请刷新诊断。' }}</pre
        >
      </div>
    </AdminPanel>

    <section class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
      <AdminPanel as="article">
        <div class="mb-4 flex items-center gap-3">
          <Flame class="h-5 w-5 text-rose-200" />
          <div>
            <p class="font-semibold">最近 API 错误</p>
            <p class="text-sm text-slate-500 dark:text-slate-400">
              优先看路径、状态码、错误类型和时间。
            </p>
          </div>
        </div>
        <div class="space-y-3">
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
              {{ item.error_type || 'Error' }}：{{
                item.error_message || item.traceback_summary || '无错误摘要'
              }}
            </p>
            <p class="mt-2 break-all text-xs text-slate-500 dark:text-slate-400">
              Request ID: {{ item.request_id || '未记录' }} · IP:
              {{ item.ip_address || '未知' }}
            </p>
          </div>
          <div
            v-if="apiErrors.length === 0"
            class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
          >
            目前没有记录到 API 500 级错误。
          </div>
        </div>
      </AdminPanel>

      <div class="space-y-5">
        <AdminPanel as="article">
          <p class="font-semibold">最近失败任务</p>
          <div class="mt-4 space-y-3">
            <div
              v-for="job in diagnostics?.recent_failed_jobs || []"
              :key="job.job_id"
              class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10"
            >
              <p class="font-semibold text-slate-950 dark:text-white">{{ job.job_type }}</p>
              <p class="mt-1 break-all text-xs text-slate-500 dark:text-slate-400">
                {{ job.job_id }}
              </p>
              <p class="mt-2 text-sm text-amber-700 dark:text-amber-200">
                {{ job.error_message || '暂无错误摘要' }}
              </p>
            </div>
            <div
              v-if="!diagnostics?.recent_failed_jobs?.length"
              class="rounded-md border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
            >
              最近没有失败任务。
            </div>
          </div>
        </AdminPanel>

        <AdminPanel as="article">
          <p class="font-semibold">待处理反馈</p>
          <div class="mt-4 space-y-3">
            <button
              v-for="item in diagnostics?.recent_feedback || []"
              :key="item.id"
              type="button"
              class="w-full rounded-md border border-sky-200 bg-sky-50 p-4 text-left transition hover:-translate-y-0.5 hover:border-sky-300 hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-500/40 dark:border-sky-500/30 dark:bg-sky-500/10 dark:bg-sky-500/15"
              @click="emit('openFeedback', item.id)"
            >
              <div class="flex flex-wrap items-center gap-2">
                <StatusPill tone="info">#{{ item.id }}</StatusPill>
                <StatusPill>{{ item.status }}</StatusPill>
                <span class="ml-auto text-xs font-semibold text-sky-700 dark:text-sky-200">
                  打开详情
                </span>
              </div>
              <p class="mt-2 break-words font-semibold text-slate-950 dark:text-white">
                {{ item.title }}
              </p>
              <p
                v-if="item.page_url"
                class="mt-1 break-all text-xs text-slate-500 dark:text-slate-400"
              >
                {{ item.page_url }}
              </p>
            </button>
            <div
              v-if="!diagnostics?.recent_feedback?.length"
              class="rounded-md border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
            >
              没有待处理反馈。
            </div>
          </div>
        </AdminPanel>
      </div>
    </section>
  </div>
</template>
