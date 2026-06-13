<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, ArrowLeft, Home, RefreshCw, SearchX, Wrench } from 'lucide-vue-next'
import { getFirstQueryValue } from '@/utils/route-state'
import { pdfTools } from '@/data/pdfTools'
import { useLocalePath } from '@/composables/useLocalePath'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { localePath } = useLocalePath()

const state = computed(() => getFirstQueryValue(route.query.state) || 'not-found')
const featureKey = computed(() => getFirstQueryValue(route.query.feature))
const message = computed(() => getFirstQueryValue(route.query.message))
const returnTo = computed(() => getFirstQueryValue(route.query.returnTo))
const missingPath = computed(() => getFirstQueryValue(route.query.path) || route.fullPath)

const tool = computed(() => pdfTools.find((item) => item.featureKey === featureKey.value))
const isFeatureDisabled = computed(() => state.value === 'feature-disabled')

const title = computed(() =>
  isFeatureDisabled.value
    ? t('availability.featureDisabledTitle')
    : t('availability.notFoundTitle')
)

const description = computed(() => {
  if (!isFeatureDisabled.value) {
    return t('availability.notFoundMessage', { path: missingPath.value })
  }

  if (message.value && message.value !== 'feature_unavailable') {
    return message.value
  }

  return t('availability.featureDisabledMessage')
})

const eyebrow = computed(() =>
  isFeatureDisabled.value ? t('availability.featureDisabledEyebrow') : t('availability.notFoundEyebrow')
)

const primaryAction = computed(() =>
  isFeatureDisabled.value ? t('availability.backToTools') : t('availability.backHome')
)

const retryTarget = computed(() => {
  if (returnTo.value && returnTo.value.startsWith('/') && !returnTo.value.startsWith('//')) {
    return returnTo.value
  }

  return tool.value?.route || ''
})

const goPrimary = () => {
  router.push(isFeatureDisabled.value ? localePath('/tools') : localePath('/'))
}

const retry = () => {
  if (retryTarget.value) {
    router.push(localePath(retryTarget.value))
  }
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
    return
  }

  router.push(localePath('/'))
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10 text-slate-950 dark:bg-slate-950 dark:text-white sm:px-6 lg:px-8">
    <section class="mx-auto flex min-h-[58vh] max-w-5xl items-center">
      <div class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div class="max-w-2xl">
            <div class="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
              <component :is="isFeatureDisabled ? Wrench : SearchX" class="h-4 w-4" />
              {{ eyebrow }}
            </div>

            <h1 class="mt-5 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
              {{ title }}
            </h1>

            <p class="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-base">
              {{ description }}
            </p>

            <div
              v-if="tool"
              class="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50"
            >
              <p class="text-sm font-semibold text-slate-950 dark:text-white">
                {{ t(tool.titleKey) }}
              </p>
              <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t(tool.descriptionKey) }}
              </p>
            </div>

            <div
              v-else-if="!isFeatureDisabled"
              class="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300"
            >
              <span class="font-semibold text-slate-800 dark:text-slate-100">{{ t('availability.requestedPath') }}:</span>
              <span class="break-all">{{ missingPath }}</span>
            </div>
          </div>

          <div class="w-full rounded-md border border-amber-200 bg-amber-50 p-4 text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/25 dark:text-amber-100 lg:max-w-xs">
            <div class="flex items-start gap-3">
              <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" />
              <p class="text-sm leading-6">
                {{ isFeatureDisabled ? t('availability.featureDisabledHint') : t('availability.notFoundHint') }}
              </p>
            </div>
          </div>
        </div>

        <div class="mt-8 flex flex-col gap-3 sm:flex-row">
          <button
            class="inline-flex items-center justify-center rounded-md bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-700 dark:bg-sky-500 dark:hover:bg-sky-400"
            @click="goPrimary"
          >
            <Home class="mr-2 h-4 w-4" />
            {{ primaryAction }}
          </button>

          <button
            v-if="retryTarget"
            class="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
            @click="retry"
          >
            <RefreshCw class="mr-2 h-4 w-4" />
            {{ t('availability.retryTool') }}
          </button>

          <button
            class="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
            @click="goBack"
          >
            <ArrowLeft class="mr-2 h-4 w-4" />
            {{ t('availability.goBack') }}
          </button>
        </div>
      </div>
    </section>
  </main>
</template>
