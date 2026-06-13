<script setup lang="ts">
import ToolHeader from '@/components/tools/ToolHeader.vue'

type Accent = 'red' | 'blue' | 'amber' | 'cyan' | 'emerald' | 'pink' | 'purple' | 'slate'
type Width = 'md' | 'lg' | 'xl'

withDefaults(defineProps<{
  title: string
  subtitle: string
  badge: string
  accent?: Accent
  pro?: boolean
  width?: Width
}>(), {
  accent: 'red',
  pro: false,
  width: 'lg',
})

const widthClasses: Record<Width, string> = {
  md: 'max-w-5xl',
  lg: 'max-w-6xl',
  xl: 'max-w-7xl',
}
</script>

<template>
  <div class="bg-[#f7f8fb] text-slate-950 dark:bg-[#f7f8fb] dark:text-slate-950">
    <ToolHeader
      :title="title"
      :subtitle="subtitle"
      :badge="badge"
      :accent="accent"
      :pro="pro"
    >
      <template #badgeIcon>
        <slot name="badgeIcon" />
      </template>
      <template #extra>
        <slot name="headerExtra" />
      </template>
    </ToolHeader>

    <section :class="['mx-auto px-4 pb-12 pt-5 sm:px-6 lg:px-8', widthClasses[width]]">
      <slot />
    </section>
  </div>
</template>
