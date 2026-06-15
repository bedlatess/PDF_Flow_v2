<script setup lang="ts">
import type { AdminModuleRiskLevel } from '@/admin/control-room/types'

defineProps<{
  level: AdminModuleRiskLevel
  compact?: boolean
}>()

const labels: Record<AdminModuleRiskLevel, string> = {
  low: 'Low risk',
  medium: 'Medium risk',
  high: 'High risk',
  critical: 'Critical',
}
</script>

<template>
  <span
    class="inline-flex max-w-full items-center rounded-full border font-semibold"
    :class="[
      compact ? 'px-2 py-0.5 text-[11px] leading-4' : 'px-3 py-1 text-xs',
      level === 'critical'
        ? 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200'
        : level === 'high'
          ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200'
          : level === 'medium'
            ? 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200'
            : 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300',
    ]"
  >
    {{ labels[level] }}
  </span>
</template>
