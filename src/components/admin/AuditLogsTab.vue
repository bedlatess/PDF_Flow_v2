<script setup lang="ts">
import { LockKeyhole, ShieldCheck } from 'lucide-vue-next'
import type { AdminAuditLog } from '@/admin/api'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
  auditLogs: AdminAuditLog[]
  formatDate: (value: string) => string
}>()
</script>

<template>
  <AdminPanel as="section" padding="lg">
    <AdminSectionHeader
      eyebrow="System"
      title="Audit Logs"
      description="Review recent admin actions, changed targets, and status. Secrets should never appear here."
      :icon="ShieldCheck"
    />

    <AdminStateBlock
      class="mt-5"
      tone="neutral"
      title="Audit trail"
      description="This is a read-only accountability log. It helps confirm who changed what and when."
    />

    <div class="mt-5 space-y-3">
      <div
        v-for="log in auditLogs"
        :key="log.id"
        class="flex flex-col gap-2 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45 sm:flex-row sm:items-center sm:justify-between"
      >
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <StatusPill>{{ log.action }}</StatusPill>
            <StatusPill tone="neutral">{{ log.status }}</StatusPill>
          </div>
          <p class="mt-2 break-words font-semibold text-slate-950 dark:text-white">
            {{ log.target_type }} · {{ log.target_key }}
          </p>
          <p v-if="log.detail" class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ log.detail }}
          </p>
        </div>
        <div class="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
          <LockKeyhole class="h-4 w-4" />
          <span>{{ formatDate(log.created_at) }}</span>
        </div>
      </div>
    </div>

    <AdminStateBlock
      v-if="auditLogs.length === 0"
      class="mt-5"
      tone="neutral"
      title="No audit logs yet"
      description="Admin actions will appear here after the next configuration save, entitlement change, or cleanup operation."
    />
  </AdminPanel>
</template>
