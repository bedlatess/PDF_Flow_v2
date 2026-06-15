<script setup lang="ts">
import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Info,
  Loader2,
} from 'lucide-vue-next'
import type { Component } from 'vue'

const props = withDefaults(
  defineProps<{
    tone?: 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'loading'
    title: string
    description?: string
    compact?: boolean
  }>(),
  {
    tone: 'neutral',
    description: '',
    compact: false,
  },
)

const iconForTone = (): Component => {
  if (props.tone === 'success') return CheckCircle2
  if (props.tone === 'warning' || props.tone === 'danger') return AlertTriangle
  if (props.tone === 'loading') return Loader2
  if (props.tone === 'info') return Info
  return CircleDot
}
</script>

<template>
  <div
    class="rounded-lg border"
    :class="[
      compact ? 'p-4' : 'p-5',
      tone === 'success'
        ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100'
        : tone === 'warning'
          ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'
          : tone === 'danger'
            ? 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100'
            : tone === 'info'
              ? 'border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100'
              : 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-200',
    ]"
  >
    <div class="flex items-start gap-3">
      <component
        :is="iconForTone()"
        class="mt-0.5 h-4 w-4 shrink-0"
        :class="tone === 'loading' ? 'animate-spin' : ''"
      />
      <div class="min-w-0">
        <p class="font-semibold">{{ title }}</p>
        <p v-if="description" class="mt-1 text-sm leading-6 opacity-85">
          {{ description }}
        </p>
        <div v-if="$slots.default" class="mt-3 text-sm leading-6">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
