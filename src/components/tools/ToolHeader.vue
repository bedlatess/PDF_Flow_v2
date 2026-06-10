<script setup lang="ts">
import { computed } from 'vue'

type Accent = 'purple' | 'blue' | 'amber' | 'cyan' | 'emerald' | 'pink'

const props = withDefaults(defineProps<{
  title: string
  subtitle: string
  badge: string
  accent?: Accent
}>(), {
  accent: 'purple',
})

const accentClasses = computed(() => {
  const map: Record<Accent, { bg: string; pill: string; glow: string }> = {
    purple: {
      bg: 'from-purple-50 via-white to-indigo-50 dark:from-purple-950/30 dark:via-slate-950 dark:to-indigo-950/20',
      pill: 'bg-gradient-to-r from-purple-500 to-pink-500 text-white',
      glow: 'bg-purple-200/50 dark:bg-purple-500/20',
    },
    blue: {
      bg: 'from-blue-50 via-white to-cyan-50 dark:from-blue-950/30 dark:via-slate-950 dark:to-cyan-950/20',
      pill: 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white',
      glow: 'bg-blue-200/50 dark:bg-blue-500/20',
    },
    amber: {
      bg: 'from-amber-50 via-white to-orange-50 dark:from-amber-950/30 dark:via-slate-950 dark:to-orange-950/20',
      pill: 'bg-gradient-to-r from-amber-500 to-orange-500 text-white',
      glow: 'bg-amber-200/50 dark:bg-amber-500/20',
    },
    cyan: {
      bg: 'from-cyan-50 via-white to-sky-50 dark:from-cyan-950/30 dark:via-slate-950 dark:to-sky-950/20',
      pill: 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white',
      glow: 'bg-cyan-200/50 dark:bg-cyan-500/20',
    },
    emerald: {
      bg: 'from-emerald-50 via-white to-teal-50 dark:from-emerald-950/30 dark:via-slate-950 dark:to-teal-950/20',
      pill: 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white',
      glow: 'bg-emerald-200/50 dark:bg-emerald-500/20',
    },
    pink: {
      bg: 'from-pink-50 via-white to-fuchsia-50 dark:from-pink-950/30 dark:via-slate-950 dark:to-fuchsia-950/20',
      pill: 'bg-gradient-to-r from-pink-500 to-fuchsia-500 text-white',
      glow: 'bg-pink-200/50 dark:bg-pink-500/20',
    },
  }

  return map[props.accent]
})
</script>

<template>
  <section :class="['relative overflow-hidden py-16 sm:py-20', `bg-gradient-to-br ${accentClasses.bg}`]">
    <div
      :class="[
        'absolute left-1/2 top-0 h-72 w-72 -translate-x-1/2 rounded-full blur-3xl',
        accentClasses.glow,
      ]"
    />

    <div class="relative mx-auto max-w-4xl px-4 text-center">
      <h1 class="text-4xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
        {{ title }}
      </h1>
      <p class="mx-auto mt-4 max-w-2xl text-base text-slate-600 dark:text-slate-300 sm:text-lg">
        {{ subtitle }}
      </p>

      <div
        :class="[
          'mt-6 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium shadow-sm',
          accentClasses.pill,
        ]"
      >
        <slot name="badgeIcon">
          *
        </slot>
        <span>{{ badge }}</span>
      </div>

      <div class="mt-6">
        <slot name="extra" />
      </div>
    </div>
  </section>
</template>
