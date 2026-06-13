<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-5xl">
      <section class="rounded-lg border border-amber-200 bg-white p-6 shadow-sm dark:border-amber-900/50 dark:bg-slate-900 sm:p-8">
        <div class="grid gap-7 lg:grid-cols-[1fr_20rem] lg:items-start">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
              <XCircle class="h-4 w-4" />
              {{ t('payment.cancel.badge') }}
            </div>
            <h1 class="mt-5 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
              {{ t('payment.cancel.title') }}
            </h1>
            <p class="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
              {{ t('payment.cancel.message') }}
            </p>

            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button variant="primary" size="lg" @click="tryAgain">
                <RefreshCw class="mr-2 h-5 w-5" />
                {{ t('payment.cancel.tryAgain') }}
              </Button>
              <Button variant="outline" size="lg" @click="goBack">
                <ReceiptText class="mr-2 h-5 w-5" />
                {{ t('payment.cancel.goBack') }}
              </Button>
              <Button variant="ghost" size="lg" @click="continueFree">
                {{ t('payment.cancel.continueFree') }}
              </Button>
            </div>
          </div>

          <aside class="rounded-md border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950/45">
            <div class="flex items-start gap-3">
              <ShieldCheck class="mt-1 h-5 w-5 shrink-0 text-sky-600 dark:text-sky-300" />
              <div>
                <p class="text-sm font-semibold text-slate-950 dark:text-white">
                  {{ t('payment.cancel.noChargeTitle') }}
                </p>
                <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('payment.cancel.noChargeDescription') }}
                </p>
              </div>
            </div>

            <div class="mt-5 grid gap-3 border-t border-slate-200 pt-5 dark:border-slate-800">
              <div
                v-for="item in statusItems"
                :key="item.label"
                class="flex items-start justify-between gap-4"
              >
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ item.label }}</span>
                <span class="text-right text-sm font-semibold text-slate-950 dark:text-white">{{ item.value }}</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <div class="mt-6 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section class="rounded-lg border border-white/70 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
            {{ t('payment.cancel.whyPro') }}
          </h2>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <div
              v-for="benefit in benefits"
              :key="benefit"
              class="flex min-h-20 items-start gap-3 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
            >
              <span class="mt-2 h-2 w-2 shrink-0 rounded-full bg-sky-600 dark:bg-sky-300" />
              <span class="text-sm leading-6 text-slate-700 dark:text-slate-200">{{ benefit }}</span>
            </div>
          </div>
        </section>

        <section class="rounded-lg border border-white/70 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
            {{ t('payment.cancel.faqTitle') }}
          </h2>
          <div class="mt-5 space-y-4">
            <div
              v-for="item in faqItems"
              :key="item.question"
              class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
            >
              <h3 class="text-sm font-semibold text-slate-950 dark:text-white">{{ item.question }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ item.answer }}</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ReceiptText, RefreshCw, ShieldCheck, XCircle } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import { useLocalePath } from '@/composables/useLocalePath'

const router = useRouter()
const { t } = useI18n()
const { localePath } = useLocalePath()
const benefits = computed(() => [
  t('payment.cancel.benefit1'),
  t('payment.cancel.benefit2'),
  t('payment.cancel.benefit3'),
  t('payment.cancel.benefit4'),
])
const faqItems = computed(() => [
  { question: t('payment.cancel.faq1Q'), answer: t('payment.cancel.faq1A') },
  { question: t('payment.cancel.faq2Q'), answer: t('payment.cancel.faq2A') },
  { question: t('payment.cancel.faq3Q'), answer: t('payment.cancel.faq3A') },
])
const statusItems = computed(() => [
  { label: t('payment.cancel.checkoutStatus'), value: t('payment.cancel.checkoutCanceled') },
  { label: t('payment.cancel.currentPlan'), value: t('payment.cancel.freePlan') },
])

const tryAgain = () => {
  router.push(localePath('/pricing'))
}

const goBack = () => {
  router.push(localePath('/pricing'))
}

const continueFree = () => {
  router.push(localePath('/'))
}
</script>
