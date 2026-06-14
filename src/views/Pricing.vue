<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Copy,
  CreditCard,
  Crown,
  QrCode,
  RefreshCw,
  ShieldCheck,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import Modal from '@/components/common/Modal.vue'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import type { PaymentProviderKey, PaymentProviderOption, PublicPricingPlan } from '@/services/api'
import { useLocalePath } from '@/composables/useLocalePath'
import { getEntitlementSummary } from '@/utils/entitlements'

type PlanId = 'free' | 'pro_monthly' | 'pro_yearly' | 'enterprise'
type CheckoutPlanId = 'pro_monthly' | 'pro_yearly'
type CurrentTier = 'free' | 'pro' | 'enterprise' | 'admin'
type ButtonVariant = 'primary' | 'outline'

interface Plan {
  id: PlanId
  name: string
  eyebrow: string
  price: string
  period: string
  description: string
  bestFor: string
  features: string[]
  notes: string[]
  cta: string
  variant: ButtonVariant
  highlighted?: boolean
  current?: boolean
}

interface PricingPageCopy {
  eyebrow: string
  title: string
  description: string
  freeName: string
  freeEyebrow: string
  freePeriod: string
  freeDescription: string
  freeBestFor: string
  freeCta: string
  proName: string
  proEyebrow: string
  proPeriod: string
  proDescription: string
  proBestFor: string
  proCta: string
  enterpriseName: string
  enterpriseEyebrow: string
  enterprisePrice: string
  enterprisePeriod: string
  enterpriseDescription: string
  enterpriseBestFor: string
  enterpriseCta: string
  currentPlan: string
  popular: string
  featuresLabel: string
  notesLabel: string
  faqTitle: string
  faqSubtitle: string
  ctaTitle: string
  ctaBody: string
  authHint: string
  paymentFailed: string
  paymentFailedTitle: string
  paymentFailedHint: string
  paymentMethodTitle: string
  paymentModalTitle: string
  paymentModalSubtitle: string
  paymentModalConfirm: string
  paymentModalChange: string
  paymentProvidersLoading: string
  paymentProvidersRetry: string
  paymentProvidersFailedTitle: string
  paymentProvidersFailedMessage: string
  paymentProvidersFailedHint: string
  paymentNoProviders: string
  paymentProviderUnavailable: string
  paymentRedirectBadge: string
  paymentQrBadge: string
  paymentSubscriptionBadge: string
  paymentOneTimeBadge: string
  paymentQrTitle: string
  paymentQrMessage: string
  paymentQrCodeLabel: string
  paymentQrOpen: string
  paymentQrCopy: string
  paymentQrCopied: string
  paymentQrCopyFailed: string
  viewFeatures: string
  freeFeatures: string[]
  freeNotes: string[]
  proFeatures: string[]
  proNotes: string[]
  enterpriseFeatures: string[]
  enterpriseNotes: string[]
  faq: [question: string, answer: string][]
}

const router = useRouter()
const userStore = useUserStore()
const { tm } = useI18n()
const { localePath } = useLocalePath()
const checkoutLoadingPlan = ref<PlanId | null>(null)
const checkoutError = ref<FormattedUserError | null>(null)
const paymentModalOpen = ref(false)
const dbPricingPlans = ref<PublicPricingPlan[]>([])
const selectedCheckoutPlan = ref<CheckoutPlanId>('pro_monthly')
const paymentProviders = ref<PaymentProviderOption[]>([])
const paymentProvidersLoading = ref(false)
const paymentProvidersError = ref<FormattedUserError | null>(null)
const selectedPaymentProvider = ref<PaymentProviderKey | null>(null)
const paymentCodeCopyState = ref<'idle' | 'copied' | 'failed'>('idle')
const qrCheckoutResult = ref<{
  provider: PaymentProviderKey
  displayName: string
  qrCodeUrl: string
  checkoutUrl: string
  merchantOrderId: string
  expiresAt?: string | null
} | null>(null)

const QR_PAYMENT_PROVIDERS = new Set<PaymentProviderKey>([
  'gmpay',
])

const currentEntitlement = computed(() =>
  getEntitlementSummary({
    role: userStore.user?.role,
    subscription_status: userStore.user?.subscription_status,
    subscription_end_date: userStore.user?.subscription_end_date,
  }),
)

const currentTier = computed<CurrentTier>(() => {
  const role = userStore.user?.role
  if (role === 'admin') return 'admin'
  if (!currentEntitlement.value.isActive) return 'free'
  return role === 'pro' || role === 'enterprise' ? role : 'free'
})
const copy = computed(() => tm('pricing.page') as PricingPageCopy)

const fallbackPlans = computed<Plan[]>(() => [
  {
    id: 'free',
    name: copy.value.freeName,
    eyebrow: copy.value.freeEyebrow,
    price: '$0',
    period: copy.value.freePeriod,
    description: copy.value.freeDescription,
    bestFor: copy.value.freeBestFor,
    features: copy.value.freeFeatures,
    notes: copy.value.freeNotes,
    cta: currentTier.value === 'free' ? copy.value.currentPlan : copy.value.freeCta,
    variant: 'outline',
    current: currentTier.value === 'free',
  },
  {
    id: 'pro_monthly',
    name: copy.value.proName,
    eyebrow: copy.value.proEyebrow,
    price: '$9.90',
    period: copy.value.proPeriod,
    description: copy.value.proDescription,
    bestFor: copy.value.proBestFor,
    features: copy.value.proFeatures,
    notes: copy.value.proNotes,
    cta: currentTier.value === 'pro' ? copy.value.currentPlan : copy.value.proCta,
    variant: 'primary',
    highlighted: true,
    current: currentTier.value === 'pro',
  },
  {
    id: 'pro_yearly',
    name: `${copy.value.proName} Annual`,
    eyebrow: copy.value.proEyebrow,
    price: '$79',
    period: '/ year',
    description: copy.value.proDescription,
    bestFor: copy.value.proBestFor,
    features: copy.value.proFeatures,
    notes: copy.value.proNotes,
    cta: currentTier.value === 'pro' ? copy.value.currentPlan : copy.value.proCta,
    variant: 'outline',
    current: currentTier.value === 'pro',
  },
  {
    id: 'enterprise',
    name: copy.value.enterpriseName,
    eyebrow: copy.value.enterpriseEyebrow,
    price: copy.value.enterprisePrice,
    period: copy.value.enterprisePeriod,
    description: copy.value.enterpriseDescription,
    bestFor: copy.value.enterpriseBestFor,
    features: copy.value.enterpriseFeatures,
    notes: copy.value.enterpriseNotes,
    cta: currentTier.value === 'enterprise' || currentTier.value === 'admin'
      ? copy.value.currentPlan
      : copy.value.enterpriseCta,
    variant: 'outline',
    current: currentTier.value === 'enterprise' || currentTier.value === 'admin',
  },
])

const planCopy = (planKey: PlanId) => {
  if (planKey === 'free') {
    return {
      features: copy.value.freeFeatures,
      notes: copy.value.freeNotes,
      bestFor: copy.value.freeBestFor,
      cta: currentTier.value === 'free' ? copy.value.currentPlan : copy.value.freeCta,
      variant: 'outline' as ButtonVariant,
      current: currentTier.value === 'free',
      eyebrow: copy.value.freeEyebrow,
    }
  }
  if (planKey === 'enterprise') {
    return {
      features: copy.value.enterpriseFeatures,
      notes: copy.value.enterpriseNotes,
      bestFor: copy.value.enterpriseBestFor,
      cta: currentTier.value === 'enterprise' || currentTier.value === 'admin'
        ? copy.value.currentPlan
        : copy.value.enterpriseCta,
      variant: 'outline' as ButtonVariant,
      current: currentTier.value === 'enterprise' || currentTier.value === 'admin',
      eyebrow: copy.value.enterpriseEyebrow,
    }
  }
  return {
    features: copy.value.proFeatures,
    notes: copy.value.proNotes,
    bestFor: copy.value.proBestFor,
    cta: currentTier.value === 'pro' ? copy.value.currentPlan : copy.value.proCta,
    variant: planKey === 'pro_monthly' ? 'primary' as ButtonVariant : 'outline' as ButtonVariant,
    current: currentTier.value === 'pro',
    eyebrow: copy.value.proEyebrow,
  }
}

const plans = computed<Plan[]>(() => {
  const publicPlans = dbPricingPlans.value.filter((plan) => plan.is_public)
  if (!publicPlans.length) {
    return fallbackPlans.value
  }
  return publicPlans
    .slice()
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((plan) => {
      const localCopy = planCopy(plan.plan_key)
      const fallbackPlan = fallbackPlans.value.find((item) => item.id === plan.plan_key)
      return {
        id: plan.plan_key,
        name: plan.display_name,
        eyebrow: localCopy.eyebrow,
        price: plan.display_price || fallbackPlan?.price || '',
        period: plan.billing_interval === 'month'
          ? copy.value.proPeriod
          : plan.billing_interval === 'year'
            ? '/ year'
            : plan.billing_interval === 'custom'
              ? copy.value.enterprisePeriod
              : fallbackPlan?.period || '',
        description: plan.description || fallbackPlan?.description || '',
        bestFor: localCopy.bestFor,
        features: localCopy.features,
        notes: localCopy.notes,
        cta: localCopy.cta,
        variant: localCopy.variant,
        highlighted: plan.highlighted,
        current: localCopy.current,
      }
    })
})

const planIcon = (planId: PlanId) => {
  if (planId === 'pro_monthly' || planId === 'pro_yearly') return Crown
  if (planId === 'enterprise') return Building2
  return ShieldCheck
}

const comparisonRows = computed(() => [
  {
    label: copy.value.freeName,
    values: copy.value.freeFeatures,
  },
  {
    label: copy.value.proName,
    values: copy.value.proFeatures,
  },
  {
    label: copy.value.enterpriseName,
    values: copy.value.enterpriseFeatures,
  },
])

const enabledPaymentProviders = computed(() =>
  paymentProviders.value.filter((provider) => provider.enabled),
)

const selectedPaymentProviderOption = computed(() =>
  paymentProviders.value.find((provider) => provider.key === selectedPaymentProvider.value) || null,
)

const paymentActionDisabled = computed(() =>
  paymentProvidersLoading.value || !selectedPaymentProvider.value || enabledPaymentProviders.value.length === 0,
)

const providerBadge = (provider: PaymentProviderOption) =>
  QR_PAYMENT_PROVIDERS.has(provider.key) ? copy.value.paymentQrBadge : copy.value.paymentRedirectBadge

const providerSettlementLabel = (provider: PaymentProviderOption) =>
  provider.supports_subscription ? copy.value.paymentSubscriptionBadge : copy.value.paymentOneTimeBadge

const selectPaymentProvider = (provider: PaymentProviderOption) => {
  if (!provider.enabled) return
  selectedPaymentProvider.value = provider.key
  qrCheckoutResult.value = null
  paymentCodeCopyState.value = 'idle'
}

const loadPaymentProviders = async () => {
  paymentProvidersLoading.value = true
  paymentProvidersError.value = null

  try {
    const { paymentAPI } = await import('@/services/api')
    const response = await paymentAPI.listProviders()
    paymentProviders.value = response.providers
    const enabled = response.providers.filter((provider) => provider.enabled)
    const currentStillEnabled = enabled.some((provider) => provider.key === selectedPaymentProvider.value)
    if (!currentStillEnabled) {
      selectedPaymentProvider.value = enabled[0]?.key || null
    }
  } catch (error) {
    const formatted = formatUserFacingError(error, {
      area: 'GENERAL',
      fallbackTitle: copy.value.paymentProvidersFailedTitle,
      fallbackMessage: copy.value.paymentProvidersFailedMessage,
    })
    paymentProvidersError.value = {
      ...formatted,
      title: copy.value.paymentProvidersFailedTitle,
      message: copy.value.paymentProvidersFailedMessage,
    }
    paymentProviders.value = []
    selectedPaymentProvider.value = null
  } finally {
    paymentProvidersLoading.value = false
  }
}

const loadPricingPlans = async () => {
  try {
    const { pricingAPI } = await import('@/services/api')
    const response = await pricingAPI.listPlans()
    dbPricingPlans.value = response.plans
  } catch {
    dbPricingPlans.value = []
  }
}

const handleCTA = async (plan: Plan) => {
  checkoutError.value = null
  paymentCodeCopyState.value = 'idle'

  if (plan.current) {
    router.push(localePath('/auth/profile'))
    return
  }

  if (plan.id === 'free') {
    router.push(localePath('/'))
    return
  }

  if (plan.id === 'enterprise') {
    window.location.href = 'mailto:sales@pdf-flow.com?subject=PDF-Flow Enterprise'
    return
  }

  if (!userStore.isAuthenticated) {
    router.push({
      path: localePath('/auth/login'),
      query: { redirect: localePath('/pricing') },
    })
    return
  }

  selectedCheckoutPlan.value = plan.id as CheckoutPlanId
  paymentModalOpen.value = true
  if (paymentProviders.value.length === 0) {
    await loadPaymentProviders()
  }
}

const startProCheckout = async () => {
  checkoutError.value = null
  paymentCodeCopyState.value = 'idle'

  try {
    checkoutLoadingPlan.value = selectedCheckoutPlan.value
    qrCheckoutResult.value = null

    if (!selectedPaymentProvider.value) {
      await loadPaymentProviders()
    }

    if (!selectedPaymentProvider.value) {
      checkoutError.value = {
        title: copy.value.paymentProvidersFailedTitle,
        message: copy.value.paymentNoProviders,
        diagnosticCode: 'PF-GENERAL-PAYMENT-PROVIDER',
        supportHint: copy.value.paymentProvidersFailedHint,
      }
      checkoutLoadingPlan.value = null
      return
    }

    const { paymentAPI } = await import('@/services/api')
    const response = await paymentAPI.createCheckoutSession({
      plan: selectedCheckoutPlan.value,
      success_url: `${window.location.origin}${localePath('/payment/success')}`,
      cancel_url: `${window.location.origin}${localePath('/payment/cancel')}`,
      provider: selectedPaymentProvider.value,
    })

    if (response.qr_code_url) {
      qrCheckoutResult.value = {
        provider: response.provider,
        displayName: selectedPaymentProviderOption.value?.display_name || response.provider,
        qrCodeUrl: response.qr_code_url,
        checkoutUrl: response.checkout_url,
        merchantOrderId: response.merchant_order_id,
        expiresAt: response.expires_at,
      }
      checkoutLoadingPlan.value = null
      return
    }

    window.location.href = response.checkout_url
  } catch (error) {
    checkoutError.value = formatUserFacingError(error, {
      area: 'GENERAL',
      fallbackTitle: copy.value.paymentFailedTitle,
      fallbackMessage: copy.value.paymentFailed,
    })
    checkoutLoadingPlan.value = null
  }
}

const openQrCheckout = () => {
  if (qrCheckoutResult.value?.checkoutUrl) {
    window.location.href = qrCheckoutResult.value.checkoutUrl
  }
}

const copyPaymentCode = async () => {
  if (!qrCheckoutResult.value?.qrCodeUrl) return

  try {
    await navigator.clipboard.writeText(qrCheckoutResult.value.qrCodeUrl)
    paymentCodeCopyState.value = 'copied'
  } catch {
    paymentCodeCopyState.value = 'failed'
  }
}

watch(
  () => userStore.isAuthenticated,
  (isAuthenticated) => {
    if (!isAuthenticated) {
      paymentProviders.value = []
      selectedPaymentProvider.value = null
      paymentProvidersError.value = null
      return
    }

    void loadPaymentProviders()
  },
  { immediate: true },
)

onMounted(loadPricingPlans)
</script>

<template>
  <div class="min-h-screen bg-[#f6f8fb] px-4 pb-16 pt-10 dark:bg-slate-950 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-7xl">
      <section class="text-center">
        <div class="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm dark:border-white/10 dark:bg-slate-900 dark:text-slate-300">
          <CreditCard class="h-4 w-4" />
          {{ copy.eyebrow }}
        </div>
        <h1 class="mx-auto mt-5 max-w-4xl text-3xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-5xl">
          {{ copy.title }}
        </h1>
        <p class="mx-auto mt-4 max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300">
          {{ copy.description }}
        </p>
      </section>

      <section class="mt-9 grid gap-5 xl:grid-cols-3">
        <article
          v-for="plan in plans"
          :key="plan.id"
          :class="[
            'relative flex min-h-[560px] flex-col rounded-lg border bg-white p-7 shadow-sm dark:bg-slate-900',
            plan.highlighted
              ? 'border-amber-300 ring-2 ring-amber-100 dark:border-amber-300/25 dark:ring-amber-300/10'
              : 'border-slate-200 dark:border-white/10 dark:shadow-none',
          ]"
        >
          <div
            v-if="plan.highlighted"
            class="absolute right-5 top-5 rounded-md bg-amber-500 px-3 py-1 text-xs font-semibold text-white shadow-sm"
          >
            {{ copy.popular }}
          </div>

          <div class="flex h-12 w-12 items-center justify-center rounded-md bg-slate-950 text-white dark:bg-white dark:text-slate-950">
            <component
              :is="planIcon(plan.id)"
              class="h-5 w-5"
            />
          </div>

          <div class="mt-5 flex flex-wrap items-center gap-2">
            <h2 class="text-2xl font-semibold text-slate-950 dark:text-white">
              {{ plan.name }}
            </h2>
          </div>
          <p class="mt-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            {{ plan.eyebrow }}
          </p>

          <div class="mt-6">
            <span class="text-4xl font-semibold tracking-tight text-slate-950 dark:text-white">
              {{ plan.price }}
            </span>
            <span class="ml-2 text-sm text-slate-500 dark:text-slate-400">
              {{ plan.period }}
            </span>
          </div>

          <p class="mt-5 min-h-[72px] text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ plan.description }}
          </p>

          <Button
            :variant="plan.variant"
            size="lg"
            full-width
            class="mt-6 rounded-md"
            :loading="checkoutLoadingPlan === plan.id"
            @click="handleCTA(plan)"
          >
            {{ plan.cta }}
          </Button>

            <DiagnosticAlert
            v-if="(plan.id === 'pro_monthly' || plan.id === 'pro_yearly') && checkoutError"
            class="mt-4"
            :title="checkoutError.title"
            :message="checkoutError.message"
            :diagnostic-code="checkoutError.diagnosticCode"
            :support-hint="copy.paymentFailedHint"
            tone="warning"
          />

          <ul class="mt-7 space-y-3">
            <li
              v-for="feature in plan.features"
              :key="feature"
              class="flex items-start gap-3"
            >
              <CheckCircle2 class="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
              <span class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ feature }}
              </span>
            </li>
          </ul>

          <p class="mt-auto pt-7 text-sm font-semibold text-slate-500 dark:text-slate-400">
            {{ copy.notesLabel }}: {{ plan.bestFor }}
          </p>
        </article>
      </section>

      <section class="mt-10 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900 sm:p-8">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-500 dark:text-slate-400">
              {{ copy.eyebrow }}
            </p>
            <h2 class="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">
              {{ copy.featuresLabel }}
            </h2>
          </div>
          <Button
            variant="outline"
            class="rounded-md"
            @click="router.push(localePath('/features'))"
          >
            {{ copy.viewFeatures }}
            <ArrowRight class="ml-2 h-4 w-4" />
          </Button>
        </div>

        <div class="mt-6 grid gap-4 lg:grid-cols-3">
          <div
            v-for="row in comparisonRows"
            :key="row.label"
            class="rounded-md border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <h3 class="font-semibold text-slate-950 dark:text-white">
              {{ row.label }}
            </h3>
            <ul class="mt-4 space-y-2">
              <li
                v-for="value in row.values"
                :key="value"
                class="flex gap-2 text-sm leading-6 text-slate-600 dark:text-slate-300"
              >
                <CheckCircle2 class="mt-1 h-4 w-4 shrink-0 text-emerald-500" />
                <span>{{ value }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section class="mt-10 grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
        <article class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900 sm:p-8">
          <div class="flex h-12 w-12 items-center justify-center rounded-md bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            <ShieldCheck class="h-5 w-5" />
          </div>
          <h2 class="mt-5 text-2xl font-semibold text-slate-950 dark:text-white">
            {{ copy.ctaTitle }}
          </h2>
          <p class="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ copy.ctaBody }}
          </p>
          <div class="mt-6 flex flex-wrap gap-3">
            <Button
              variant="primary"
              class="rounded-md"
              @click="router.push(localePath('/'))"
            >
              {{ copy.freeCta }}
            </Button>
            <Button
              variant="outline"
              class="rounded-md"
              @click="router.push(localePath('/features'))"
            >
              {{ copy.viewFeatures }}
            </Button>
          </div>
        </article>

        <article class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900 sm:p-8">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p class="text-sm font-semibold text-slate-500 dark:text-slate-400">
                {{ copy.faqTitle }}
              </p>
              <h2 class="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">
                {{ copy.faqSubtitle }}
              </h2>
            </div>
            <div class="inline-flex items-center gap-2 rounded-md bg-slate-50 px-4 py-2 text-sm text-slate-600 dark:bg-slate-950/50 dark:text-slate-300">
              <ShieldCheck class="h-4 w-4" />
              {{ copy.authHint }}
            </div>
          </div>

          <div class="mt-6 grid gap-4 md:grid-cols-2">
            <div
              v-for="[question, answer] in copy.faq"
              :key="question"
              class="rounded-md border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/45"
            >
              <h3 class="font-semibold text-slate-950 dark:text-white">
                {{ question }}
              </h3>
              <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                {{ answer }}
              </p>
            </div>
          </div>
        </article>
      </section>
    </div>

    <Modal
      v-model="paymentModalOpen"
      size="lg"
      :title="copy.paymentModalTitle"
    >
      <div class="space-y-5">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex items-start gap-3">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-white text-slate-700 shadow-sm dark:bg-slate-900 dark:text-slate-200">
              <CreditCard class="h-5 w-5" />
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-950 dark:text-white">
                {{ copy.paymentMethodTitle }}
              </p>
              <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ copy.paymentModalSubtitle }}
              </p>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-semibold text-slate-950 dark:text-white">
            {{ copy.paymentMethodTitle }}
          </p>
          <button
            type="button"
            class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            :aria-label="copy.paymentProvidersRetry"
            :disabled="paymentProvidersLoading"
            @click="loadPaymentProviders"
          >
            <RefreshCw :class="['h-4 w-4', paymentProvidersLoading ? 'animate-spin' : '']" />
          </button>
        </div>

        <DiagnosticAlert
          v-if="paymentProvidersError"
          :title="paymentProvidersError.title"
          :message="paymentProvidersError.message"
          :diagnostic-code="paymentProvidersError.diagnosticCode"
          :support-hint="copy.paymentProvidersFailedHint"
          tone="warning"
        />

        <div
          v-else-if="paymentProvidersLoading"
          class="rounded-md border border-dashed border-slate-300 bg-white px-4 py-5 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
        >
          {{ copy.paymentProvidersLoading }}
        </div>

        <div
          v-else-if="enabledPaymentProviders.length === 0"
          class="rounded-md border border-dashed border-slate-300 bg-white px-4 py-5 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
        >
          {{ copy.paymentNoProviders }}
        </div>

        <div
          v-else
          role="radiogroup"
          :aria-label="copy.paymentMethodTitle"
          class="grid gap-2 sm:grid-cols-2"
        >
          <button
            v-for="provider in paymentProviders"
            :key="provider.key"
            type="button"
            role="radio"
            :aria-checked="selectedPaymentProvider === provider.key"
            :disabled="!provider.enabled"
            :class="[
              'flex min-h-[72px] w-full items-center justify-between gap-3 rounded-md border px-3 py-3 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500',
              selectedPaymentProvider === provider.key
                ? 'border-amber-300 bg-amber-50 text-slate-950 dark:border-amber-300/50 dark:bg-amber-400/10 dark:text-white'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-slate-700 dark:hover:bg-slate-800',
              !provider.enabled ? 'cursor-not-allowed opacity-50' : '',
            ]"
            @click="selectPaymentProvider(provider)"
          >
            <span class="flex min-w-0 items-center gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-950 text-white dark:bg-white dark:text-slate-950">
                <QrCode
                  v-if="QR_PAYMENT_PROVIDERS.has(provider.key)"
                  class="h-4 w-4"
                />
                <CreditCard
                  v-else
                  class="h-4 w-4"
                />
              </span>
              <span class="min-w-0">
                <span class="block truncate text-sm font-semibold">
                  {{ provider.display_name }}
                </span>
                <span class="mt-1 block truncate text-xs text-slate-500 dark:text-slate-400">
                  {{ provider.enabled ? providerSettlementLabel(provider) : copy.paymentProviderUnavailable }}
                </span>
              </span>
            </span>
            <span class="shrink-0 rounded-md border border-current/15 px-2 py-1 text-[11px] font-semibold">
              {{ providerBadge(provider) }}
            </span>
          </button>
        </div>

        <DiagnosticAlert
          v-if="checkoutError"
          :title="checkoutError.title"
          :message="checkoutError.message"
          :diagnostic-code="checkoutError.diagnosticCode"
          :support-hint="copy.paymentFailedHint"
          tone="warning"
        />

        <div
          v-if="qrCheckoutResult"
          class="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-emerald-950 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100"
        >
          <div class="flex items-start gap-3">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-white text-emerald-700 shadow-sm dark:bg-slate-950 dark:text-emerald-300">
              <QrCode class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-semibold">
                {{ copy.paymentQrTitle }}
              </p>
              <p class="mt-1 text-sm leading-6 opacity-85">
                {{ copy.paymentQrMessage }}
              </p>
            </div>
          </div>

          <div class="mt-4 rounded-md border border-emerald-200/80 bg-white p-3 dark:border-emerald-400/20 dark:bg-slate-950/70">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700 dark:text-emerald-300">
              {{ copy.paymentQrCodeLabel }} - {{ qrCheckoutResult.displayName }}
            </p>
            <p class="mt-2 break-all font-mono text-xs leading-5 text-slate-700 dark:text-slate-200">
              {{ qrCheckoutResult.qrCodeUrl }}
            </p>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <Button
              v-if="qrCheckoutResult.checkoutUrl"
              variant="outline"
              size="sm"
              class="rounded-md border-emerald-700 text-emerald-800 hover:bg-emerald-700 hover:text-white dark:border-emerald-300 dark:text-emerald-200"
              @click="openQrCheckout"
            >
              {{ copy.paymentQrOpen }}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              class="rounded-md border border-emerald-700/20 bg-white/70 text-emerald-800 hover:bg-white dark:bg-slate-950/40 dark:text-emerald-200"
              @click="copyPaymentCode"
            >
              <Copy class="mr-2 h-4 w-4" />
              {{ paymentCodeCopyState === 'copied' ? copy.paymentQrCopied : copy.paymentQrCopy }}
            </Button>
          </div>

          <p
            v-if="paymentCodeCopyState === 'failed'"
            class="mt-3 text-xs font-semibold text-amber-700 dark:text-amber-200"
          >
            {{ copy.paymentQrCopyFailed }}
          </p>
        </div>
      </div>

      <template #footer>
        <div class="flex flex-col gap-3 sm:flex-row sm:justify-end">
          <Button
            variant="outline"
            class="rounded-md"
            @click="paymentModalOpen = false"
          >
            {{ copy.paymentModalChange }}
          </Button>
          <Button
            variant="primary"
            class="rounded-md"
            :loading="checkoutLoadingPlan === selectedCheckoutPlan"
            :disabled="paymentActionDisabled"
            @click="startProCheckout"
          >
            {{ copy.paymentModalConfirm }}
          </Button>
        </div>
      </template>
    </Modal>
  </div>
</template>
