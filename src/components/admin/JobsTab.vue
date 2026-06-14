<script setup lang="ts">
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

const updateJobSearch = (event: Event) => {
  emit('update:jobSearch', (event.target as HTMLInputElement).value)
}

const updateJobStatusFilter = (event: Event) => {
  emit('update:jobStatusFilter', (event.target as HTMLSelectElement).value)
}

const statusTone = (status: string) => {
  if (status === 'failed') return 'danger'
  if (status === 'completed') return 'success'
  if (status === 'processing') return 'info'
  return 'warning'
}

const statusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return labels[status] || status
}

const jobTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    compress_pdf: '压缩 PDF',
    merge_pdf: '合并 PDF',
    split_pdf: '拆分 PDF',
    rotate_pdf: '旋转 PDF',
    image_to_pdf: '图片转 PDF',
    pdf_to_image: 'PDF 转图片',
    ocr_pdf: 'OCR',
    office_to_pdf: 'Office 转 PDF',
    processing_job: '兼容任务',
  }
  return labels[type] || type
}

const sourceLabel = (job: AdminJob) => {
  const sources = job.sources?.length ? job.sources : [job.source]
  if (sources.includes('db') && sources.includes('redis')) return 'DB + Redis'
  if (sources.includes('db')) return 'Durable DB'
  if (sources.includes('redis')) return 'Redis'
  return job.source || 'unknown'
}

const sourceTone = (job: AdminJob) => {
  const sources = job.sources?.length ? job.sources : [job.source]
  if (sources.includes('db') && sources.includes('redis')) return 'success'
  if (sources.includes('db')) return 'info'
  if (sources.includes('redis')) return 'warning'
  return 'neutral'
}

const finishedAt = (job: AdminJob) => job.completed_at || job.started_at || job.created_at

const ageText = (job: AdminJob) => {
  const start = new Date(job.created_at).getTime()
  const end = new Date(finishedAt(job)).getTime()
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return '未知'
  const seconds = Math.max(0, Math.round((end - start) / 1000))
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remaining = seconds % 60
  return `${minutes}m ${remaining}s`
}

const summary = () => {
  const total = props.filteredJobs.length
  const failed = props.filteredJobs.filter((job) => job.status === 'failed').length
  const running = props.filteredJobs.filter((job) =>
    ['pending', 'processing'].includes(job.status)
  ).length
  const durable = props.filteredJobs.filter((job) => job.is_durable).length
  const mixed = props.filteredJobs.filter((job) => job.sources?.includes('db') && job.sources?.includes('redis')).length
  return { total, failed, running, durable, mixed }
}
</script>

<template>
  <div class="contents">
    <AdminPanel as="section">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div class="max-w-3xl">
          <p class="text-xl font-semibold text-slate-950 dark:text-white">任务中心</p>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            查看最近任务的执行状态、来源、输出路径和错误摘要。DB durable 记录用于历史追踪，Redis
            记录用于当前活动状态；同一个 job_id 会合并展示并优先显示 DB 记录。
          </p>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs sm:grid-cols-5 xl:min-w-[520px]">
          <div class="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/45">
            <p class="text-slate-500 dark:text-slate-400">匹配</p>
            <p class="mt-1 text-base font-semibold text-slate-950 dark:text-white">{{ summary().total }}</p>
          </div>
          <div class="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/45">
            <p class="text-slate-500 dark:text-slate-400">运行中</p>
            <p class="mt-1 text-base font-semibold text-slate-950 dark:text-white">{{ summary().running }}</p>
          </div>
          <div class="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/45">
            <p class="text-slate-500 dark:text-slate-400">失败</p>
            <p class="mt-1 text-base font-semibold text-rose-700 dark:text-rose-200">{{ summary().failed }}</p>
          </div>
          <div class="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/45">
            <p class="text-slate-500 dark:text-slate-400">Durable</p>
            <p class="mt-1 text-base font-semibold text-slate-950 dark:text-white">{{ summary().durable }}</p>
          </div>
          <div class="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/45">
            <p class="text-slate-500 dark:text-slate-400">Mixed</p>
            <p class="mt-1 text-base font-semibold text-slate-950 dark:text-white">{{ summary().mixed }}</p>
          </div>
        </div>
      </div>

      <div class="mt-5 flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <input
          :value="jobSearch"
          type="search"
          placeholder="搜索 job_id / 用户 / 类型 / 文件 / 错误"
          class="min-h-11 rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400 lg:min-w-[420px]"
          @input="updateJobSearch"
        />
        <div class="flex flex-col gap-2 sm:flex-row">
          <select
            :value="jobStatusFilter"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
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

      <div v-if="filteredJobs.length" class="mt-5 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
        <div class="hidden overflow-x-auto xl:block">
          <table class="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-normal text-slate-500 dark:bg-slate-950/60 dark:text-slate-400">
              <tr>
                <th class="px-4 py-3">任务</th>
                <th class="px-4 py-3">状态</th>
                <th class="px-4 py-3">来源</th>
                <th class="px-4 py-3">用户 / 文件</th>
                <th class="px-4 py-3">时间</th>
                <th class="px-4 py-3">输出 / 错误</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-950/30">
              <tr v-for="job in filteredJobs" :key="job.job_id" class="align-top">
                <td class="max-w-[260px] px-4 py-4">
                  <div class="flex flex-wrap gap-2">
                    <StatusPill tone="info">{{ jobTypeLabel(job.job_type) }}</StatusPill>
                  </div>
                  <p class="mt-2 break-all font-mono text-xs text-slate-500 dark:text-slate-400">{{ job.job_id }}</p>
                </td>
                <td class="px-4 py-4">
                  <StatusPill :tone="statusTone(job.status)">{{ statusLabel(job.status) }}</StatusPill>
                  <div class="mt-3 w-28">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                      <span>进度</span>
                      <span>{{ job.progress }}%</span>
                    </div>
                    <div class="mt-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800">
                      <div
                        class="h-1.5 rounded-full"
                        :class="job.status === 'failed' ? 'bg-rose-500' : job.status === 'completed' ? 'bg-emerald-500' : 'bg-sky-500'"
                        :style="{ width: `${Math.min(Math.max(job.progress, 0), 100)}%` }"
                      />
                    </div>
                  </div>
                </td>
                <td class="px-4 py-4">
                  <StatusPill :tone="sourceTone(job)">{{ sourceLabel(job) }}</StatusPill>
                  <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    {{ job.is_durable ? '可持久追踪' : '活动状态' }}
                  </p>
                </td>
                <td class="max-w-[260px] px-4 py-4">
                  <p class="truncate font-medium text-slate-950 dark:text-white">{{ job.input_file_name }}</p>
                  <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {{ job.user_email || (job.user_id ? `#${job.user_id}` : '匿名') }} ·
                    {{ formatAdminBytes(job.input_file_size) }}
                  </p>
                </td>
                <td class="px-4 py-4 text-xs text-slate-500 dark:text-slate-400">
                  <p>创建 {{ formatDate(job.created_at) }}</p>
                  <p class="mt-1">更新时间 {{ formatDate(finishedAt(job)) }}</p>
                  <p class="mt-1">耗时 {{ ageText(job) }}</p>
                </td>
                <td class="max-w-[320px] px-4 py-4 text-xs">
                  <p v-if="job.error_message" class="rounded-md border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-rose-700 dark:text-rose-200">
                    {{ job.error_message }}
                  </p>
                  <p v-else-if="job.output_file_url" class="break-all font-mono text-slate-500 dark:text-slate-400">
                    {{ job.output_file_url }}
                  </p>
                  <p v-else class="text-slate-400 dark:text-slate-500">暂无输出路径</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-950/30 xl:hidden">
          <article v-for="job in filteredJobs" :key="job.job_id" class="p-4">
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill tone="info">{{ jobTypeLabel(job.job_type) }}</StatusPill>
              <StatusPill :tone="statusTone(job.status)">{{ statusLabel(job.status) }}</StatusPill>
              <StatusPill :tone="sourceTone(job)">{{ sourceLabel(job) }}</StatusPill>
            </div>
            <p class="mt-3 font-semibold text-slate-950 dark:text-white">{{ job.input_file_name }}</p>
            <p class="mt-1 break-all font-mono text-xs text-slate-500 dark:text-slate-400">{{ job.job_id }}</p>
            <dl class="mt-3 grid grid-cols-2 gap-3 text-xs text-slate-500 dark:text-slate-400">
              <div>
                <dt>用户</dt>
                <dd class="mt-1 truncate text-slate-950 dark:text-white">{{ job.user_email || (job.user_id ? `#${job.user_id}` : '匿名') }}</dd>
              </div>
              <div>
                <dt>大小</dt>
                <dd class="mt-1 text-slate-950 dark:text-white">{{ formatAdminBytes(job.input_file_size) }}</dd>
              </div>
              <div>
                <dt>创建</dt>
                <dd class="mt-1 text-slate-950 dark:text-white">{{ formatDate(job.created_at) }}</dd>
              </div>
              <div>
                <dt>耗时</dt>
                <dd class="mt-1 text-slate-950 dark:text-white">{{ ageText(job) }}</dd>
              </div>
            </dl>
            <div class="mt-4">
              <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>进度</span>
                <span>{{ job.progress }}%</span>
              </div>
              <div class="mt-2 h-2 rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  class="h-2 rounded-full"
                  :class="job.status === 'failed' ? 'bg-rose-500' : job.status === 'completed' ? 'bg-emerald-500' : 'bg-sky-500'"
                  :style="{ width: `${Math.min(Math.max(job.progress, 0), 100)}%` }"
                />
              </div>
            </div>
            <p v-if="job.error_message" class="mt-3 rounded-md border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-700 dark:text-rose-200">
              {{ job.error_message }}
            </p>
            <p v-else-if="job.output_file_url" class="mt-3 break-all font-mono text-xs text-slate-500 dark:text-slate-400">
              {{ job.output_file_url }}
            </p>
          </article>
        </div>
      </div>

      <div
        v-else
        class="mt-5 rounded-lg border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400"
      >
        当前没有匹配任务。运行一次业务、OCR 或 Office smoke test 后刷新；如果仍为空，说明最近 Redis
        活动状态和 DB durable 记录里都没有匹配项。
      </div>
    </AdminPanel>
  </div>
</template>
