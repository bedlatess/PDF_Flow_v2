<script setup lang="ts">
import ToolErrorAlert from './ToolErrorAlert.vue'

type Layout = 'balanced' | 'wide-primary' | 'wide-secondary'

const props = withDefaults(defineProps<{
  errorMessage?: string
  layout?: Layout
}>(), {
  errorMessage: '',
  layout: 'balanced',
})

const layoutClasses: Record<Layout, string> = {
  balanced: 'lg:grid-cols-[minmax(0,1fr)_minmax(300px,0.88fr)]',
  'wide-primary': 'xl:grid-cols-[minmax(0,1.1fr)_minmax(300px,0.9fr)]',
  'wide-secondary': 'lg:grid-cols-[minmax(0,0.95fr)_minmax(300px,1.05fr)]',
}
</script>

<template>
  <div class="space-y-5">
    <ToolErrorAlert
      v-if="props.errorMessage"
      :message="props.errorMessage"
    />

    <slot name="upload" />

    <div
      v-if="$slots.primary || $slots.secondary"
      :class="[
        'grid min-w-0 items-start gap-5 lg:gap-6',
        layoutClasses[props.layout],
      ]"
    >
      <section
        v-if="$slots.primary"
        class="min-w-0 space-y-5 lg:sticky lg:top-24"
      >
        <slot name="primary" />
      </section>

      <aside
        v-if="$slots.secondary"
        class="min-w-0 space-y-5"
      >
        <slot name="secondary" />
      </aside>
    </div>
  </div>
</template>
