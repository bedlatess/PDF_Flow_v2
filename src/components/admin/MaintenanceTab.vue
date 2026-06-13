<script setup lang="ts">
import { CircleDot, ClipboardList, Trash2 } from 'lucide-vue-next'
import type { AdminDiagnostics, AdminMaintenance, AdminOperations } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'

defineProps<{
  maintenance: AdminMaintenance | null
  operations: AdminOperations | null
  diagnostics: AdminDiagnostics | null
  savingKey: string | null
}>()

const emit = defineEmits<{
  refresh: []
  cleanupLive: []
  cleanupTestUsers: []
  cleanupExpiredFiles: []
}>()
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xl font-semibold">维护清理</p>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            上方按钮只会重新统计数量，不会删除任何内容。真正清理请使用下方对应卡片里的执行按钮，批量动作会写入审计日志。
          </p>
        </div>
        <AdminActionButton
          class="min-h-11 py-3"
          :disabled="savingKey === 'maintenance:refresh'"
          :loading="savingKey === 'maintenance:refresh'"
          @click="emit('refresh')"
        >
          重新统计数量
        </AdminActionButton>
      </div>

      <div
        class="mt-5 rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm leading-6 text-sky-800 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100"
      >
        <div class="flex items-start gap-3">
          <CircleDot class="mt-1 h-4 w-4 shrink-0" />
          <p>
            “重新统计数量”只刷新维护视图。需要清理测试数据时，请继续点击对应动作按钮并确认操作范围。
          </p>
        </div>
      </div>

      <div class="mt-5 grid gap-4 md:grid-cols-4">
        <AdminPanel as="div" tone="warning" padding="sm">
          <p class="text-sm text-amber-700 dark:text-amber-200/70">测试账号</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ maintenance?.test_users_count ?? operations?.test_users ?? 0 }}
          </p>
          <p class="mt-2 text-xs text-amber-700 dark:text-amber-200/60">
            smoke / ocr / office / @example.com
          </p>
        </AdminPanel>
        <AdminPanel as="div" tone="info" padding="sm">
          <p class="text-sm text-sky-700 dark:text-sky-200/70">验收反馈</p>
          <p class="mt-2 text-3xl font-semibold text-sky-800 dark:text-sky-100">
            {{ maintenance?.live_acceptance_feedback_count ?? 0 }}
          </p>
          <p class="mt-2 text-xs text-sky-700 dark:text-sky-200/60">
            标题以 live acceptance 开头
          </p>
        </AdminPanel>
        <AdminPanel as="div" tone="danger" padding="sm">
          <p class="text-sm text-rose-700 dark:text-rose-200/70">需要关注</p>
          <p class="mt-2 text-3xl font-semibold text-rose-800 dark:text-rose-100">
            {{ maintenance?.failed_jobs_count ?? diagnostics?.failed_jobs_count ?? 0 }}
          </p>
          <p class="mt-2 text-xs text-rose-700 dark:text-rose-200/60">
            失败任务暂不自动删除，保留排查线索
          </p>
        </AdminPanel>
        <AdminPanel as="div" tone="success" padding="sm">
          <p class="text-sm text-emerald-700 dark:text-emerald-200/70">过期临时文件</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">
            {{ maintenance?.file_retention?.removable_count ?? 0 }}
          </p>
          <p class="mt-2 text-xs text-emerald-700 dark:text-emerald-200/60">
            上传、结果和下载包按保留策略清理
          </p>
        </AdminPanel>
      </div>
    </AdminPanel>

    <section class="grid gap-5 xl:grid-cols-3">
      <AdminPanel as="article">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-lg font-semibold">关闭验收反馈</p>
            <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              将上线验收脚本生成的 live acceptance 反馈标记为 closed，不删除真实用户留言。
            </p>
          </div>
          <ClipboardList class="h-5 w-5 text-sky-600 dark:text-sky-300" />
        </div>
        <div
          class="mt-5 rounded-lg border border-sky-200 bg-sky-50 p-4 dark:border-sky-500/30 dark:bg-sky-500/10"
        >
          <p class="text-sm text-sky-700 dark:text-sky-200/70">当前可关闭</p>
          <p class="mt-2 text-3xl font-semibold text-sky-800 dark:text-sky-100">
            {{ maintenance?.live_acceptance_feedback_count ?? 0 }}
          </p>
          <p class="mt-2 text-xs text-sky-700 dark:text-sky-200/60">
            {{
              (maintenance?.live_acceptance_feedback_count ?? 0) === 0
                ? '没有可关闭的验收反馈'
                : '点击下方按钮后才会写入更改'
            }}
          </p>
        </div>
        <AdminActionButton
          class="mt-5 min-h-11 py-3"
          full
          :disabled="
            savingKey === 'feedback:cleanup-live' ||
            (maintenance?.live_acceptance_feedback_count ?? 0) === 0
          "
          :loading="savingKey === 'feedback:cleanup-live'"
          @click="emit('cleanupLive')"
        >
          执行：关闭验收反馈
        </AdminActionButton>
      </AdminPanel>

      <AdminPanel as="article" tone="danger">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-lg font-semibold">删除测试账号</p>
            <p class="mt-2 text-sm leading-6 text-rose-700 dark:text-rose-200/75">
              删除 smoke-、ocr-、office- 和 @example.com 测试账号；管理员和真实邮箱账号不会被批量删除。
            </p>
          </div>
          <Trash2 class="h-5 w-5 text-rose-700 dark:text-rose-200" />
        </div>
        <div
          class="mt-5 rounded-lg border border-rose-200 bg-slate-50 p-4 dark:border-rose-500/30 dark:bg-slate-950/45"
        >
          <p class="text-sm text-rose-700 dark:text-rose-200/70">当前可删除</p>
          <p class="mt-2 text-3xl font-semibold text-rose-800 dark:text-rose-100">
            {{ maintenance?.test_users_count ?? operations?.test_users ?? 0 }}
          </p>
          <p class="mt-2 text-xs text-rose-700 dark:text-rose-200/60">
            {{
              (maintenance?.test_users_count ?? operations?.test_users ?? 0) === 0
                ? '没有可删除的测试账号'
                : '点击下方按钮并确认后才会删除'
            }}
          </p>
        </div>
        <AdminActionButton
          tone="danger"
          class="mt-5 min-h-11 py-3"
          full
          :disabled="
            savingKey === 'maintenance:cleanup-users' ||
            (maintenance?.test_users_count ?? operations?.test_users ?? 0) === 0
          "
          :loading="savingKey === 'maintenance:cleanup-users'"
          @click="emit('cleanupTestUsers')"
        >
          执行：删除测试账号
        </AdminActionButton>
      </AdminPanel>

      <AdminPanel as="article" tone="success">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-lg font-semibold">清理云端临时文件</p>
            <p class="mt-2 text-sm leading-6 text-emerald-700 dark:text-emerald-200/75">
              删除超过保留时间的上传文件、转换结果和下载包。只扫描配置的上传目录，并使用固定前缀白名单保护其他文件。
            </p>
          </div>
          <Trash2 class="h-5 w-5 text-emerald-700 dark:text-emerald-200" />
        </div>
        <div
          class="mt-5 rounded-lg border border-emerald-200 bg-slate-50 p-4 dark:border-emerald-500/30 dark:bg-slate-950/45"
        >
          <p class="text-sm text-emerald-700 dark:text-emerald-200/70">当前可清理</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">
            {{ maintenance?.file_retention?.removable_count ?? 0 }}
          </p>
          <p class="mt-2 break-all text-xs text-emerald-700 dark:text-emerald-200/60">
            {{ maintenance?.file_retention?.upload_dir || '未读取到上传目录' }}
          </p>
        </div>
        <AdminActionButton
          tone="success"
          class="mt-5 min-h-11 py-3"
          full
          :disabled="
            savingKey === 'maintenance:cleanup-files' ||
            (maintenance?.file_retention?.removable_count ?? 0) === 0
          "
          :loading="savingKey === 'maintenance:cleanup-files'"
          @click="emit('cleanupExpiredFiles')"
        >
          执行：清理过期临时文件
        </AdminActionButton>
      </AdminPanel>
    </section>

    <section
      class="rounded-lg border border-slate-200 bg-slate-50 p-5 text-sm leading-7 text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300"
    >
      <p class="font-semibold text-slate-950 dark:text-white">暂不自动清理的内容</p>
      <p class="mt-2">
        API 错误、失败任务、审计日志和真实用户反馈会保留，用于后续排查。云端文件内容会按保留策略自动或手动清理，数据库中的任务摘要只保留必要的排查线索。
      </p>
    </section>
  </div>
</template>
