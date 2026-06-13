<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Cloud, Cpu, LogIn, Sparkles } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()

const canUseCloud = computed(() => userStore.canUseCloudFeatures)

const copy = computed(() => ({
  localTitle: t('common.cloudToggle.localTitle'),
  localDesc: t('common.cloudToggle.localDesc'),
  cloudTitle: t('common.cloudToggle.cloudTitle'),
  cloudDesc: t('common.cloudToggle.cloudDesc'),
  lockedDesc: t('common.cloudToggle.lockedDesc'),
  switchLabel: t('common.cloudToggle.switchLabel'),
}))

const title = computed(() => (props.modelValue && canUseCloud.value ? copy.value.cloudTitle : copy.value.localTitle))
const description = computed(() => {
  return props.modelValue ? copy.value.cloudDesc : copy.value.localDesc
})
const actionHint = computed(() => {
  if (canUseCloud.value) return ''
  return copy.value.lockedDesc
})

const toggle = () => {
  if (!canUseCloud.value) {
    router.push(userStore.isAuthenticated ? '/pricing' : '/auth/login')
    return
  }
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/50">
    <div class="flex items-start justify-between gap-4">
      <div class="flex gap-3">
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md"
          :class="modelValue && canUseCloud ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-200' : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'"
        >
          <Cloud v-if="modelValue && canUseCloud" class="h-5 w-5" />
          <Cpu v-else class="h-5 w-5" />
        </div>
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <p class="text-sm font-semibold text-slate-900 dark:text-white">
              {{ title }}
            </p>
          </div>
          <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
            {{ description }}
          </p>
          <p
            v-if="actionHint"
            class="mt-2 inline-flex items-center gap-1 text-xs font-medium text-slate-500 dark:text-slate-400"
          >
            <LogIn v-if="!userStore.isAuthenticated" class="h-3.5 w-3.5" />
            <Sparkles v-else class="h-3.5 w-3.5" />
            {{ actionHint }}
          </p>
        </div>
      </div>

      <button
        type="button"
        role="switch"
        :aria-checked="modelValue"
        :aria-label="copy.switchLabel"
        :title="actionHint"
        class="relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors"
        :class="[
          modelValue && canUseCloud ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700',
          !canUseCloud ? 'opacity-75' : '',
        ]"
        @click="toggle"
      >
        <span
          class="inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform"
          :class="modelValue && canUseCloud ? 'translate-x-6' : 'translate-x-1'"
        />
      </button>
    </div>
  </div>
</template>
