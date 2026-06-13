<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-5xl">
      <section class="rounded-lg border border-emerald-200 bg-white p-6 shadow-sm dark:border-emerald-900/50 dark:bg-slate-900 sm:p-8">
        <div class="grid gap-7 lg:grid-cols-[1fr_20rem] lg:items-start">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200">
              <CheckCircle2 class="h-4 w-4" />
              {{ t('payment.success.badge') }}
            </div>
            <h1 class="mt-5 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
              {{ t('payment.success.title') }}
            </h1>
            <p class="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
              {{ t('payment.success.message') }}
            </p>

            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button variant="primary" size="lg" @click="startUsing">
                <Sparkles class="mr-2 h-5 w-5" />
                {{ t('payment.success.startUsing') }}
              </Button>
              <Button variant="outline" size="lg" @click="goToProfile">
                <BadgeCheck class="mr-2 h-5 w-5" />
                {{ t('payment.success.viewAccount') }}
              </Button>
            </div>
          </div>

          <aside class="rounded-md border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950/45">
            <div class="flex items-start gap-3">
              <CreditCard class="mt-1 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-300" />
              <div>
                <p class="text-sm font-semibold text-slate-950 dark:text-white">
                  {{ t('payment.success.checkoutState') }}
                </p>
                <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ checkoutStateText }}
                </p>
              </div>
            </div>

            <div class="mt-5 grid gap-3 border-t border-slate-200 pt-5 dark:border-slate-800">
              <div class="flex items-center justify-between gap-4">
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ t('payment.success.plan') }}</span>
                <span class="text-lg font-semibold text-slate-950 dark:text-white">Pro</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ t('payment.success.status') }}</span>
                <span class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-200">
                  {{ t('payment.success.active') }}
                </span>
              </div>
              <div v-if="checkoutReference" class="flex items-center justify-between gap-4">
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ t('payment.success.referenceLabel') }}</span>
                <code class="rounded bg-white px-2 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                  {{ checkoutReference }}
                </code>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <div class="mt-6 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section class="rounded-lg border border-white/70 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
            {{ t('payment.success.unlocked') }}
          </h2>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <div
              v-for="feature in unlockedFeatures"
              :key="feature"
              class="flex min-h-20 items-start gap-3 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
            >
              <CheckCircle2 class="mt-0.5 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-300" />
              <span class="text-sm leading-6 text-slate-700 dark:text-slate-200">{{ feature }}</span>
            </div>
          </div>
        </section>

        <section class="rounded-lg border border-white/70 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div class="flex items-start gap-3">
            <Clock3 class="mt-1 h-5 w-5 shrink-0 text-sky-600 dark:text-sky-300" />
            <div>
              <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
                {{ t('payment.success.nextSteps') }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ accountRefreshText }}
              </p>
            </div>
          </div>

          <div class="mt-5 space-y-3">
            <div
              v-for="(step, index) in nextSteps"
              :key="step"
              class="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
            >
              <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white dark:bg-emerald-500">
                {{ index + 1 }}
              </span>
              <span class="pt-0.5 text-sm leading-6 text-slate-700 dark:text-slate-200">{{ step }}</span>
            </div>
          </div>

          <p class="mt-5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
            <Mail class="h-4 w-4" />
            <span>{{ t('payment.success.needHelp') }}</span>
            <a :href="`mailto:${supportEmail}`" class="inline-flex min-h-8 items-center px-1 font-semibold text-emerald-700 hover:text-emerald-800 dark:text-emerald-300">
              {{ t('payment.success.contactSupport') }}
            </a>
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { BadgeCheck, CheckCircle2, Clock3, CreditCard, Mail, Sparkles } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import { useUserStore } from '@/stores/user'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { useLocalePath } from '@/composables/useLocalePath'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const userStore = useUserStore()
const siteConfigStore = useSiteConfigStore()
const { localePath } = useLocalePath()
const refreshState = ref<'idle' | 'refreshing' | 'synced' | 'guest'>('idle')

const supportEmail = computed(() => siteConfigStore.getSettingValue('support_email', 'support@pdf-flow.com'))
const checkoutReference = computed(() => {
  const raw = Array.isArray(route.query.session_id) ? route.query.session_id[0] : route.query.session_id
  if (!raw) return ''
  return raw.length > 12 ? `...${raw.slice(-8)}` : raw
})
const checkoutStateText = computed(() =>
  checkoutReference.value ? t('payment.success.checkoutReturnedWithReference') : t('payment.success.checkoutReturned')
)
const accountRefreshText = computed(() => {
  if (refreshState.value === 'refreshing') return t('payment.success.accountSyncing')
  if (refreshState.value === 'synced') return t('payment.success.accountSynced')
  if (refreshState.value === 'guest') return t('payment.success.accountGuest')
  return t('payment.success.accountPending')
})
const unlockedFeatures = computed(() => [
  t('payment.success.feature1'),
  t('payment.success.feature2'),
  t('payment.success.feature3'),
  t('payment.success.feature4'),
])
const nextSteps = computed(() => [
  t('payment.success.step1'),
  t('payment.success.step2'),
  t('payment.success.step3'),
])

onMounted(async () => {
  void siteConfigStore.fetchPublicConfig()

  refreshState.value = 'refreshing'
  const isAuthenticated = await userStore.checkAuth()
  refreshState.value = isAuthenticated ? 'synced' : 'guest'
})

const goToProfile = () => {
  router.push(localePath('/auth/profile'))
}

const startUsing = () => {
  router.push(localePath('/'))
}
</script>
