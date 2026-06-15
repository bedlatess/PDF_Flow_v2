<script setup lang="ts">
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    eyebrow?: string
    title: string
    description?: string
    icon?: Component
  }>(),
  {
    eyebrow: '',
    description: '',
    icon: undefined,
  },
)
</script>

<template>
  <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
    <div class="min-w-0">
      <div
        v-if="eyebrow || icon"
        class="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400"
      >
        <component :is="icon" v-if="icon" class="h-4 w-4" />
        <span v-if="eyebrow">{{ eyebrow }}</span>
        <slot name="badges" />
      </div>
      <h3 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
        {{ title }}
      </h3>
      <p v-if="description" class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.actions" class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-end">
      <slot name="actions" />
    </div>
  </div>
</template>
