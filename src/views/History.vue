<script setup lang="ts">
import { ArrowLeft, Clock3, ClipboardCheck, ShieldCheck } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from '@/components/common/Button.vue'
import HistoryPanel from '@/components/common/HistoryPanel.vue'
import { useLocalePath } from '@/composables/useLocalePath'

const router = useRouter()
const { t } = useI18n()
const { localePath } = useLocalePath()

const goHome = () => {
  router.push(localePath('/'))
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950">
    <section class="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <button
        class="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
        @click="goHome"
      >
        <ArrowLeft class="h-4 w-4" />
        {{ t('history.page.backHome') }}
      </button>

      <div class="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
        <div>
          <div class="inline-flex items-center gap-2 rounded-md border border-sky-200 bg-white px-4 py-2 text-sm font-semibold text-sky-700 shadow-sm dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200">
            <Clock3 class="h-4 w-4" />
            {{ t('history.page.badge') }}
          </div>
          <h1 class="mt-5 text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            {{ t('history.page.title') }}
          </h1>
          <p class="mt-4 max-w-2xl text-base leading-8 text-slate-600 dark:text-slate-300">
            {{ t('history.page.description') }}
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <ShieldCheck class="h-6 w-6 text-emerald-500" />
            <p class="mt-3 font-semibold text-slate-900 dark:text-white">{{ t('history.page.localTitle') }}</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {{ t('history.page.localDescription') }}
            </p>
          </div>
          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <ClipboardCheck class="h-6 w-6 text-amber-500" />
            <p class="mt-3 font-semibold text-slate-900 dark:text-white">{{ t('history.page.reviewTitle') }}</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {{ t('history.page.reviewDescription') }}
            </p>
          </div>
        </div>
      </div>

      <div class="mt-8 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-6">
        <HistoryPanel />
      </div>

      <div class="mt-6 flex justify-center">
        <Button
          variant="outline"
          class="rounded-md"
          @click="goHome"
        >
          {{ t('history.page.continueProcessing') }}
        </Button>
      </div>
    </section>
  </div>
</template>
