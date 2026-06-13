<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: 'neutral' | 'info' | 'success' | 'warning' | 'danger'
  }>(),
  {
    tone: 'neutral',
  }
)
</script>

<template>
  <span
    class="inline-block max-w-full whitespace-normal break-all rounded-full px-3 py-1 text-left align-middle text-xs font-semibold"
    :class="
      tone === 'info'
        ? 'bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-200'
        : tone === 'success'
          ? 'bg-emerald-400/15 text-emerald-700 dark:text-emerald-200'
          : tone === 'warning'
            ? 'bg-amber-50 text-amber-700 dark:bg-amber-400/15 dark:text-amber-200'
            : tone === 'danger'
              ? 'bg-rose-400/15 text-rose-700 dark:text-rose-200'
              : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
    "
  >
    <slot />
  </span>
</template>
