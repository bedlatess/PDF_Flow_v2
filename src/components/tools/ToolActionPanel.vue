<script setup lang="ts">
import { computed } from 'vue'
import Button from '@/components/common/Button.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'

type Accent = 'blue' | 'emerald' | 'amber' | 'purple' | 'slate'
type ActionVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'

interface StatItem {
  label: string
  value: string | number | null | undefined
}

const props = withDefaults(defineProps<{
  label?: string
  title: string
  description?: string
  accent?: Accent
  stats?: StatItem[]
  progress?: number
  progressLabel?: string
  showProgress?: boolean
  actionLabel: string
  actionVariant?: ActionVariant
  loading?: boolean
  disabled?: boolean
}>(), {
  label: '',
  description: '',
  accent: 'slate',
  stats: () => [],
  progress: 0,
  progressLabel: '',
  showProgress: false,
  actionVariant: 'primary',
  loading: false,
  disabled: false,
})

const emit = defineEmits<{
  action: []
}>()

const accentClasses = computed(() => {
  const map: Record<Accent, string> = {
    blue: 'text-blue-600 dark:text-blue-300',
    emerald: 'text-emerald-600 dark:text-emerald-300',
    amber: 'text-amber-600 dark:text-amber-300',
    purple: 'text-purple-600 dark:text-purple-300',
    slate: 'text-slate-500 dark:text-slate-400',
  }

  return map[props.accent]
})
</script>

<template>
  <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
    <div class="space-y-5">
      <div>
        <p
          v-if="label"
          :class="['text-xs font-semibold uppercase tracking-[0.18em]', accentClasses]"
        >
          {{ label }}
        </p>
        <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
          {{ title }}
        </h2>
        <p
          v-if="description"
          class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300"
        >
          {{ description }}
        </p>
      </div>

      <slot />

      <div
        v-if="stats.length > 0"
        class="grid gap-3 sm:grid-cols-2"
      >
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/45"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
            {{ stat.label }}
          </p>
          <p class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">
            {{ stat.value ?? '-' }}
          </p>
        </div>
      </div>

      <slot name="details" />

      <ProgressBar
        v-if="showProgress"
        :progress="progress"
        :label="progressLabel"
        variant="primary"
        size="md"
      />

      <Button
        :variant="actionVariant"
        size="lg"
        :loading="loading"
        :disabled="disabled"
        full-width
        @click="emit('action')"
      >
        {{ actionLabel }}
      </Button>
    </div>
  </section>
</template>
