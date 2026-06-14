<script setup lang="ts">
import { computed } from 'vue'

interface ModalProps {
  modelValue: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnClickOutside?: boolean
  showCloseButton?: boolean
}

const props = withDefaults(defineProps<ModalProps>(), {
  size: 'md',
  closeOnClickOutside: true,
  showCloseButton: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'max-w-sm'
    case 'md':
      return 'max-w-md'
    case 'lg':
      return 'max-w-lg'
    case 'xl':
      return 'max-w-xl'
    case 'full':
      return 'max-w-full mx-4'
    default:
      return 'max-w-md'
  }
})

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

const handleBackdropClick = () => {
  if (props.closeOnClickOutside) {
    close()
  }
}

const handleContentClick = (event: MouseEvent) => {
  event.stopPropagation()
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
        @click="handleBackdropClick"
      >
        <Transition
          enter-active-class="transition-all duration-200"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-200"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="modelValue"
            role="dialog"
            aria-modal="true"
            :aria-label="title || undefined"
            :class="[
              'relative max-h-[calc(100vh-2rem)] w-full overflow-hidden rounded-lg bg-white shadow-2xl shadow-slate-950/20 dark:bg-slate-900',
              sizeClasses,
            ]"
            @click="handleContentClick"
          >
            <!-- Header -->
            <div
              v-if="title || showCloseButton || $slots.header"
              class="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800"
            >
              <slot name="header">
                <h3 class="text-lg font-semibold text-slate-950 dark:text-white">
                  {{ title }}
                </h3>
              </slot>

              <button
                v-if="showCloseButton"
                class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                @click="close"
              >
                <svg
                  class="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <!-- Body -->
            <div class="max-h-[calc(100vh-9rem)] overflow-y-auto px-6 py-5">
              <slot />
            </div>

            <!-- Footer -->
            <div
              v-if="$slots.footer"
              class="border-t border-slate-200 px-6 py-4 dark:border-slate-800"
            >
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
