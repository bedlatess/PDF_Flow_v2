<script setup lang="ts">
import { AlertCircle } from 'lucide-vue-next'

defineProps<{
  message: string
}>()
</script>

<template>
  <div
    v-if="message"
    role="alert"
    class="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800 shadow-sm dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-100"
  >
    <AlertCircle class="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-300" />
    <p class="min-w-0">
      {{ message }}
    </p>
  </div>
</template>
