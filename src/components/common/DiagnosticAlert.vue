<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, Info, ShieldAlert } from 'lucide-vue-next'

type Tone = 'danger' | 'warning' | 'info'

const props = withDefaults(defineProps<{
  title: string
  message: string
  diagnosticCode?: string
  supportHint?: string
  tone?: Tone
}>(), {
  diagnosticCode: '',
  supportHint: 'If this keeps happening, please screenshot this message and send it to the administrator.',
  tone: 'danger',
})

const toneClasses = computed(() => {
  const map: Record<Tone, { box: string; icon: string }> = {
    danger: {
      box: 'border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-100',
      icon: 'text-red-500 dark:text-red-300',
    },
    warning: {
      box: 'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-100',
      icon: 'text-amber-500 dark:text-amber-300',
    },
    info: {
      box: 'border-sky-200 bg-sky-50 text-sky-900 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-100',
      icon: 'text-sky-500 dark:text-sky-300',
    },
  }

  return map[props.tone]
})

const iconComponent = computed(() => {
  if (props.tone === 'warning') {
    return ShieldAlert
  }

  if (props.tone === 'info') {
    return Info
  }

  return AlertTriangle
})
</script>

<template>
  <div :class="['rounded-[24px] border px-5 py-4 shadow-sm', toneClasses.box]">
    <div class="flex items-start gap-3">
      <component :is="iconComponent" :class="['mt-0.5 h-5 w-5 flex-shrink-0', toneClasses.icon]" />
      <div class="min-w-0 space-y-2">
        <div class="space-y-1">
          <p class="text-sm font-semibold">
            {{ title }}
          </p>
          <p class="text-sm leading-6 opacity-90">
            {{ message }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span
            v-if="diagnosticCode"
            class="rounded-full border border-current/15 bg-white/50 px-2.5 py-1 font-semibold uppercase tracking-[0.18em] dark:bg-black/10"
          >
            {{ diagnosticCode }}
          </span>
          <span class="opacity-75">
            {{ supportHint }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
