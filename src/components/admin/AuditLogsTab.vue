<script setup lang="ts">
import { LockKeyhole, ShieldCheck } from 'lucide-vue-next'
import type { AdminAuditLog } from '@/admin/api'
import AdminPanel from './AdminPanel.vue'

defineProps<{
  auditLogs: AdminAuditLog[]
  formatDate: (value: string) => string
}>()
</script>

<template>
  <AdminPanel as="section">
    <div class="mb-5 flex items-center gap-3">
      <ShieldCheck class="h-5 w-5 text-sky-600 dark:text-sky-300" />
      <div>
        <p class="font-semibold">最近管理员操作</p>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          只展示最近 50 条，完整留存由后端审计表负责。
        </p>
      </div>
    </div>

    <div class="space-y-3">
      <div
        v-for="log in auditLogs"
        :key="log.id"
        class="flex flex-col gap-2 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <p class="font-medium">{{ log.action }} {{ log.target_type }}</p>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {{ log.target_key }}
          </p>
        </div>
        <div class="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
          <LockKeyhole class="h-4 w-4" />
          <span>{{ formatDate(log.created_at) }}</span>
        </div>
      </div>
    </div>
  </AdminPanel>
</template>
