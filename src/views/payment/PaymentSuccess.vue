<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-5xl">
      <section class="rounded-lg border border-emerald-200 bg-white p-6 shadow-sm dark:border-emerald-900/50 dark:bg-slate-900 sm:p-8">
        <div class="grid gap-7 lg:grid-cols-[1fr_20rem] lg:items-start">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200">
              <CheckCircle2 class="h-4 w-4" />
              {{ tr('payment.success.badge', 'Payment complete') }}
            </div>
            <h1 class="mt-5 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
              {{ tr('payment.success.title', 'Payment complete') }}
            </h1>
            <p class="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
              {{ tr('payment.success.message', 'Thanks for upgrading. PDF-Flow is refreshing your account state.') }}
            </p>

            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button variant="primary" size="lg" @click="startUsing">
                <Sparkles class="mr-2 h-5 w-5" />
                {{ tr('payment.success.startUsing', 'Start using PDF-Flow') }}
              </Button>
              <Button variant="outline" size="lg" @click="goToProfile">
                <BadgeCheck class="mr-2 h-5 w-5" />
                {{ tr('payment.success.viewAccount', 'View account') }}
              </Button>
            </div>
          </div>

          <aside class="rounded-md border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950/45">
            <div class="flex items-start gap-3">
              <CreditCard class="mt-1 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-300" />
              <div>
                <p class="text-sm font-semibold text-slate-950 dark:text-white">
                  {{ tr('payment.success.checkoutState', 'Payment status') }}
                </p>
                <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ checkoutStateText }}
                </p>
              </div>
            </div>

            <div class="mt-5 grid gap-3 border-t border-slate-200 pt-5 dark:border-slate-800">
              <div class="flex items-center justify-between gap-4">
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ tr('payment.success.plan', 'Plan') }}</span>
                <span class="text-lg font-semibold text-slate-950 dark:text-white">Pro</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ tr('payment.success.status', 'Status') }}</span>
                <span class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-200">
                  {{ tr('payment.success.active', 'Active') }}
                </span>
              </div>
              <div v-if="checkoutReference" class="flex items-center justify-between gap-4">
                <span class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ tr('payment.success.referenceLabel', 'Reference') }}</span>
                <code class="max-w-full break-all rounded bg-white px-2 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-900 dark:text-slate-200">
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
            {{ tr('payment.success.unlocked', 'What Pro unlocks') }}
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
                {{ tr('payment.success.nextSteps', 'Next steps') }}
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
            <span>{{ tr('payment.success.needHelp', 'Need help?') }}</span>
            <a :href="`mailto:${supportEmail}`" class="inline-flex min-h-8 items-center px-1 font-semibold text-emerald-700 hover:text-emerald-800 dark:text-emerald-300">
              {{ tr('payment.success.contactSupport', 'Contact support') }}
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
const tr = (key: string, fallback: string) => {
  const value = t(key)
  return value === key ? fallback : value
}
const checkoutReference = computed(() => {
  const raw = Array.isArray(route.query.session_id) ? route.query.session_id[0] : route.query.session_id
  if (!raw) return ''
  return raw.length > 12 ? `...${raw.slice(-8)}` : raw
})
const checkoutStateText = computed(() =>
  checkoutReference.value
    ? tr('payment.success.checkoutReturnedWithReference', 'Payment finished with a reference number. Keep it handy if support needs it.')
    : tr('payment.success.checkoutReturned', 'Payment finished successfully. Your account will update shortly.')
)
const accountRefreshText = computed(() => {
  if (refreshState.value === 'refreshing') return tr('payment.success.accountSyncing', 'Refreshing your account so the latest subscription state is visible.')
  if (refreshState.value === 'synced') return tr('payment.success.accountSynced', 'Your account details were refreshed. If Pro access does not appear immediately, wait a moment and refresh again.')
  if (refreshState.value === 'guest') return tr('payment.success.accountGuest', 'You are not signed in on this browser. Sign in with the account used at checkout to see subscription status.')
  return tr('payment.success.accountPending', 'We will refresh your account once the page is ready.')
})
const unlockedFeatures = computed(() => [
  tr('payment.success.feature1', 'Higher conversion quotas for cloud tools and document workflows.'),
  tr('payment.success.feature2', 'Access to OCR, Office conversion, AI analysis, and Pro-only tools.'),
  tr('payment.success.feature3', 'Account-level history so successful results can be downloaded again while available.'),
  tr('payment.success.feature4', 'Priority processing and clearer support handoff for payment questions.'),
])
const nextSteps = computed(() => [
  tr('payment.success.step1', 'Open your account to confirm the current plan and billing status.'),
  tr('payment.success.step2', 'Try cloud OCR, Office conversion, or AI workflows when Pro access is visible.'),
  tr('payment.success.step3', 'Contact support with the payment reference if access does not update after a few minutes.'),
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
