<script setup lang="ts">
import { computed } from 'vue'
import ProBadge from '@/components/common/ProBadge.vue'

type Accent = 'red' | 'purple' | 'blue' | 'amber' | 'cyan' | 'emerald' | 'pink' | 'slate'

const props = withDefaults(defineProps<{
  title: string
  subtitle: string
  badge: string
  pro?: boolean
  accent?: Accent
}>(), {
  pro: false,
  accent: 'red',
})

const showInlineBadge = computed(() => !props.pro || props.badge.trim().toLowerCase() !== 'pro')

const accentClasses = computed(() => {
  const map: Record<Accent, { rail: string; icon: string }> = {
    red: {
      rail: 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-200',
      icon: 'text-red-600 dark:text-red-300',
    },
    purple: {
      rail: 'border-purple-200 bg-purple-50 text-purple-700 dark:border-purple-500/20 dark:bg-purple-500/10 dark:text-purple-200',
      icon: 'text-purple-600 dark:text-purple-300',
    },
    blue: {
      rail: 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-200',
      icon: 'text-blue-600 dark:text-blue-300',
    },
    amber: {
      rail: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200',
      icon: 'text-amber-600 dark:text-amber-300',
    },
    cyan: {
      rail: 'border-cyan-200 bg-cyan-50 text-cyan-800 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-200',
      icon: 'text-cyan-600 dark:text-cyan-300',
    },
    emerald: {
      rail: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200',
      icon: 'text-emerald-600 dark:text-emerald-300',
    },
    pink: {
      rail: 'border-pink-200 bg-pink-50 text-pink-800 dark:border-pink-500/20 dark:bg-pink-500/10 dark:text-pink-200',
      icon: 'text-pink-600 dark:text-pink-300',
    },
    slate: {
      rail: 'border-slate-200 bg-slate-100 text-slate-700 dark:border-white/10 dark:bg-slate-800 dark:text-slate-200',
      icon: 'text-slate-700 dark:text-slate-200',
    },
  }

  return map[props.accent]
})
</script>

<template>
  <section class="border-b border-slate-200/80 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
    <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
        <div class="flex items-start gap-4">
          <div :class="['pf-icon-tile h-11 w-11 border text-sm shadow-sm', accentClasses.rail]">
            <span :class="accentClasses.icon">
              <slot name="badgeIcon">
                *
              </slot>
            </span>
          </div>

          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="text-2xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-3xl">
                {{ title }}
              </h1>
              <span
                v-if="showInlineBadge"
                :class="['rounded-md border px-2 py-1 text-xs font-semibold', accentClasses.rail]"
              >
                {{ badge }}
              </span>
            </div>
            <p class="mt-2 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-base">
              {{ subtitle }}
            </p>
          </div>
        </div>

        <ProBadge
          v-if="pro"
          :label="badge"
          variant="seal"
        />
      </div>

      <div class="mt-6">
        <slot name="extra" />
      </div>
    </div>
  </section>
</template>
