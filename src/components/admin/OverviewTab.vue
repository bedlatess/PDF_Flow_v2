<script setup lang="ts">
import { CircleDot, ClipboardCopy } from 'lucide-vue-next'
import type { AdminHealthReport, AdminJob, AdminOperations, AdminOverview } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
  overview: AdminOverview | null
  operations: AdminOperations | null
  jobs: AdminJob[]
  healthReport: AdminHealthReport | null
  healthReportSummary: string
  healthReportCopied: boolean
  savingKey: string | null
  formatDate: (value: string) => string
}>()

const emit = defineEmits<{
  refreshAll: []
  refreshHealthReport: []
  copyHealthReport: []
}>()

const serviceTone = (status?: string) => {
  if (status === 'healthy')
    return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
  if (status === 'unhealthy')
    return 'border-rose-200 bg-rose-500/10 text-rose-700 dark:border-rose-500/30 dark:text-rose-200'
  if (status === 'degraded')
    return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200'
  return 'border-slate-300/20 bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
}
</script>

<template>
  <div class="space-y-5">
    <section class="grid gap-4 xl:grid-cols-4">
      <AdminPanel as="article">
        <p class="text-sm text-slate-500 dark:text-slate-400">全部用户</p>
        <p class="mt-3 text-3xl font-semibold">
          {{ operations?.total_users ?? overview?.users_count ?? 0 }}
        </p>
        <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
          测试账号 {{ operations?.test_users ?? 0 }} 个
        </p>
      </AdminPanel>

      <AdminPanel as="article">
        <p class="text-sm text-slate-500 dark:text-slate-400">可登录用户</p>
        <p class="mt-3 text-3xl font-semibold">
          {{ operations?.active_users ?? overview?.active_users_count ?? 0 }}
        </p>
        <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
          封禁 {{ operations?.banned_users ?? 0 }} 个
        </p>
      </AdminPanel>

      <AdminPanel as="article">
        <p class="text-sm text-slate-500 dark:text-slate-400">近期可见任务</p>
        <p class="mt-3 text-3xl font-semibold">
          {{ operations?.visible_jobs ?? jobs.length }}
        </p>
        <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
          处理中 {{ operations?.running_jobs ?? 0 }} 个
        </p>
      </AdminPanel>

      <AdminPanel as="article">
        <p class="text-sm text-slate-500 dark:text-slate-400">失败任务</p>
        <p class="mt-3 text-3xl font-semibold text-rose-700 dark:text-rose-200">
          {{ operations?.failed_jobs ?? overview?.failed_jobs_count ?? 0 }}
        </p>
        <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">优先排查最近错误</p>
      </AdminPanel>
    </section>

    <section class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <AdminPanel as="article">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <p class="text-lg font-semibold">服务状态</p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              数据库、Redis 和任务队列线索。
            </p>
          </div>
          <AdminActionButton @click="emit('refreshAll')">刷新</AdminActionButton>
        </div>

        <div class="space-y-3">
          <div
            v-for="(service, name) in operations?.services"
            :key="name"
            class="rounded-md border p-4"
            :class="serviceTone(service.status)"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <CircleDot class="h-4 w-4" />
                <span class="font-semibold">{{ name }}</span>
              </div>
              <span class="text-xs uppercase tracking-[0.18em]">{{ service.status }}</span>
            </div>
            <p class="mt-2 text-sm opacity-80">{{ service.detail }}</p>
          </div>
        </div>
      </AdminPanel>

      <AdminPanel as="article" tone="info">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-lg font-semibold">上线健康报告</p>
            <p class="mt-1 text-sm leading-6 text-sky-700 dark:text-sky-200/75">
              一键复制当前线上状态，方便截图或发给管理员排查。
            </p>
          </div>
          <div class="flex gap-2">
            <AdminActionButton
              tone="neutral"
              :disabled="savingKey === 'health-report:refresh'"
              :loading="savingKey === 'health-report:refresh'"
              @click="emit('refreshHealthReport')"
            >
              刷新
            </AdminActionButton>
            <AdminActionButton tone="neutral" @click="emit('copyHealthReport')">
              <template #icon>
                <ClipboardCopy class="h-4 w-4" />
              </template>
              {{ healthReportCopied ? '已复制' : '复制报告' }}
            </AdminActionButton>
          </div>
        </div>

        <div class="mt-5 grid gap-3 sm:grid-cols-3">
          <AdminPanel as="div" tone="subtle" padding="sm">
            <p class="text-xs text-sky-700 dark:text-sky-200/70">后端版本</p>
            <p class="mt-2 break-all font-semibold text-slate-950 dark:text-white">
              {{ healthReport?.app_version || '未加载' }}
            </p>
          </AdminPanel>
          <AdminPanel as="div" tone="subtle" padding="sm">
            <p class="text-xs text-sky-700 dark:text-sky-200/70">迁移版本</p>
            <p class="mt-2 break-all font-semibold text-slate-950 dark:text-white">
              {{ healthReport?.migration_version || '未读取到' }}
            </p>
          </AdminPanel>
          <AdminPanel as="div" tone="subtle" padding="sm">
            <p class="text-xs text-sky-700 dark:text-sky-200/70">环境</p>
            <p class="mt-2 font-semibold text-slate-950 dark:text-white">
              {{ healthReport?.environment || 'unknown' }}
            </p>
          </AdminPanel>
        </div>

        <pre
          class="mt-4 max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-4 text-xs leading-6 text-sky-800 dark:border-slate-800 dark:bg-slate-950 dark:text-sky-100/85"
          >{{ healthReportSummary || '健康报告加载中...' }}</pre
        >
      </AdminPanel>
    </section>

    <section class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <AdminPanel as="article">
        <div class="mb-4">
          <p class="text-lg font-semibold">最近失败任务</p>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
            这里有内容时，优先看错误摘要和 job_id。
          </p>
        </div>
        <div class="space-y-3">
          <div
            v-for="job in operations?.recent_failed_jobs"
            :key="job.job_id"
            class="rounded-md border border-rose-200 bg-rose-500/10 p-4 dark:border-rose-500/30"
          >
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill tone="danger">{{ job.job_type }}</StatusPill>
              <span class="text-xs text-rose-700 dark:text-rose-200/70">
                {{ formatDate(job.created_at) }}
              </span>
            </div>
            <p class="mt-2 break-all font-semibold text-slate-950 dark:text-white">
              {{ job.job_id }}
            </p>
            <p class="mt-2 text-sm text-rose-700 dark:text-rose-200">
              {{ job.error_message || '暂无错误摘要' }}
            </p>
          </div>
          <div
            v-if="!operations?.recent_failed_jobs?.length"
            class="rounded-md border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
          >
            最近没有失败任务，状态不错。
          </div>
        </div>
      </AdminPanel>
    </section>

    <section class="grid gap-5 xl:grid-cols-2">
      <AdminPanel as="article">
        <p class="text-lg font-semibold">最近注册用户</p>
        <div class="mt-4 space-y-3">
          <div
            v-for="user in operations?.recent_users"
            :key="user.id"
            class="flex items-center justify-between gap-3 rounded-md bg-slate-50 p-3 dark:bg-slate-950/45"
          >
            <div>
              <p class="font-semibold text-slate-950 dark:text-white">{{ user.email }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {{ user.role }} · {{ user.is_test_account ? '测试账号' : '真实用户' }}
              </p>
            </div>
            <StatusPill :tone="user.is_active ? 'success' : 'danger'">
              {{ user.is_active ? '正常' : '已封禁' }}
            </StatusPill>
          </div>
        </div>
      </AdminPanel>

      <AdminPanel as="article">
        <p class="text-lg font-semibold">最近任务</p>
        <div class="mt-4 space-y-3">
          <div
            v-for="job in operations?.recent_jobs"
            :key="job.job_id"
            class="rounded-md bg-slate-50 p-3 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="font-semibold text-slate-950 dark:text-white">{{ job.job_type }}</span>
              <StatusPill
                :tone="
                  job.status === 'failed'
                    ? 'danger'
                    : job.status === 'completed'
                      ? 'success'
                      : 'warning'
                "
              >
                {{ job.status }}
              </StatusPill>
            </div>
            <p class="mt-2 break-all text-xs text-slate-500 dark:text-slate-400">
              {{ job.job_id }}
            </p>
          </div>
          <div
            v-if="!operations?.recent_jobs?.length"
            class="rounded-md border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
          >
            暂无近期任务。
          </div>
        </div>
      </AdminPanel>
    </section>
  </div>
</template>
