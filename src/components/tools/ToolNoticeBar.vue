<script setup lang="ts">
import { computed } from 'vue'

type Variant = 'amber' | 'purple' | 'blue' | 'emerald'

const props = withDefaults(defineProps<{
  variant?: Variant
}>(), {
  variant: 'amber',
})

const classes = computed(() => {
  const map: Record<Variant, string> = {
    amber: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-200',
    purple: 'border-purple-200 bg-purple-50 text-purple-800 dark:border-purple-800 dark:bg-purple-900/20 dark:text-purple-200',
    blue: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-200',
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-200',
  }

  return map[props.variant]
})
</script>

<template>
  <div :class="['rounded-2xl border px-5 py-4', classes]">
    <div class="flex items-start gap-3">
      <div class="mt-0.5 text-lg">
        <slot name="icon">
          !
        </slot>
      </div>
      <div class="text-sm leading-6">
        <slot />
      </div>
    </div>
  </div>
</template>
