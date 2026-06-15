<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next'

withDefaults(
  defineProps<{
    tone?: 'primary' | 'neutral' | 'success' | 'warning' | 'danger'
    loading?: boolean
    disabled?: boolean
    full?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    tone: 'primary',
    loading: false,
    disabled: false,
    full: false,
    type: 'button',
  }
)
</script>

<template>
  <button
    :type="type"
    class="inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 py-2 text-center text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60"
    :class="[
      full ? 'w-full' : '',
      tone === 'primary'
        ? 'bg-sky-600 text-white hover:bg-sky-700 dark:bg-sky-400 dark:text-slate-950 dark:hover:bg-sky-300'
        : tone === 'neutral'
          ? 'border border-slate-200 bg-white text-slate-950 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800'
          : tone === 'success'
            ? 'bg-emerald-600 text-white hover:bg-emerald-700 dark:bg-emerald-400 dark:text-emerald-950 dark:hover:bg-emerald-300'
            : tone === 'warning'
              ? 'border border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200 dark:hover:bg-amber-500/20'
              : 'border border-rose-200 bg-rose-500/10 text-rose-700 hover:bg-rose-500/20 dark:border-rose-500/30 dark:text-rose-200',
    ]"
    :disabled="loading || disabled"
  >
    <Loader2 v-if="loading" class="h-4 w-4 shrink-0 animate-spin" />
    <slot v-else name="icon" />
    <span class="min-w-0 break-words">
      <slot />
    </span>
  </button>
</template>
