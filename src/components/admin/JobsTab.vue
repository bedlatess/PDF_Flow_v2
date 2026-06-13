<script setup lang="ts">
import type { AdminJob } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
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

const updateJobSearch = (event: Event) => {
  emit('update:jobSearch', (event.target as HTMLInputElement).value)
}

const updateJobStatusFilter = (event: Event) => {
  emit('update:jobStatusFilter', (event.target as HTMLSelectElement).value)
}

const formatBytes = (value: number) => {
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}
</script>

<template>
  <div class="contents">
    <AdminPanel as="section">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xl font-semibold">任务观察</p>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            快速查看最近云端处理任务，优先定位失败、卡住或异常耗时的用户操作。这里会合并显示最近 1
            小时 Redis 队列状态和数据库任务记录。
          </p>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row">
          <input
            :value="jobSearch"
            type="search"
            placeholder="搜索 job_id / 用户 / 类型 / 错误"
            class="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400 dark:text-white dark:focus:border-sky-400"
            @input="updateJobSearch"
          />
          <select
            :value="jobStatusFilter"
            class="rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:text-white dark:focus:border-sky-400"
            @change="updateJobStatusFilter"
          >
            <option value="">全部状态</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <AdminActionButton
            class="min-h-11 py-3"
            :disabled="savingKey === 'jobs:refresh'"
            :loading="savingKey === 'jobs:refresh'"
            @click="emit('refresh')"
          >
            刷新
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-5 space-y-3">
        <article
          v-for="job in filteredJobs"
          :key="job.job_id"
          class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
        >
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <StatusPill tone="info">{{ job.job_type }}</StatusPill>
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
              <p class="mt-3 font-semibold text-slate-950 dark:text-white">
                {{ job.input_file_name }}
              </p>
              <p class="mt-1 break-all text-sm text-slate-500 dark:text-slate-400">
                {{ job.job_id }}
              </p>
              <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
                用户：{{ job.user_email || (job.user_id ? `#${job.user_id}` : '未记录') }} ·
                大小：{{ formatBytes(job.input_file_size) }} · 创建：{{
                  formatDate(job.created_at)
                }}
              </p>
              <p
                v-if="job.error_message"
                class="mt-3 rounded-md border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-700 dark:text-rose-200"
              >
                {{ job.error_message }}
              </p>
            </div>
            <div class="min-w-[180px]">
              <div
                class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400"
              >
                <span>进度</span>
                <span>{{ job.progress }}%</span>
              </div>
              <div class="mt-2 h-2 rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  class="h-2 rounded-full bg-sky-600 dark:bg-sky-400"
                  :style="{ width: `${job.progress}%` }"
                />
              </div>
            </div>
          </div>
        </article>

        <div
          v-if="filteredJobs.length === 0"
          class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
        >
          当前没有匹配任务。运行一次业务、OCR 或 Office smoke test
          后，再点刷新；如果已刷新仍为空，说明最近 1 小时 Redis 状态和数据库任务里都没有匹配记录。
        </div>
      </div>
    </AdminPanel>
  </div>
</template>
