<script setup lang="ts">
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title: string
  message?: string
  primaryLabel: string
  secondaryLabel?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}>(), {
  message: '',
  secondaryLabel: '',
  size: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  primary: []
  secondary: []
}>()
</script>

<template>
  <Modal
    :model-value="props.modelValue"
    :title="props.title"
    :size="props.size"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="space-y-5 text-center">
      <p
        v-if="props.message"
        class="text-sm leading-6 text-slate-600 dark:text-slate-300"
      >
        {{ props.message }}
      </p>

      <slot />

      <div class="flex flex-col gap-3">
        <Button
          variant="primary"
          size="lg"
          full-width
          @click="emit('primary')"
        >
          {{ props.primaryLabel }}
        </Button>
        <Button
          v-if="props.secondaryLabel"
          variant="outline"
          size="lg"
          full-width
          @click="emit('secondary')"
        >
          {{ props.secondaryLabel }}
        </Button>
      </div>
    </div>
  </Modal>
</template>
