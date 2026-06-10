<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'

const router = useRouter()
const userStore = useUserStore()
const { t, locale } = useI18n()
const activeLocale = computed(() => locale.value)

interface PricingTier {
  id: 'free' | 'pro' | 'enterprise'
  name: string
  price: string
  priceDetail: string
  description: string
  features: string[]
  limitations?: string[]
  cta: string
  ctaVariant: 'outline' | 'primary' | 'ghost'
  popular?: boolean
  current?: boolean
}

const isLoggedIn = computed(() => userStore.isAuthenticated)
const currentTier = computed(() => userStore.user?.role || 'free')

const enterprisePrice = computed(() => {
  if (locale.value === 'zh') return '按需'
  if (locale.value === 'es') return 'A medida'
  return 'Custom'
})

const pricingTiers = computed<PricingTier[]>(() => [
  {
    id: 'free',
    name: t('marketing.pricingPage.tiers.free.name'),
    price: '$0',
    priceDetail: t('marketing.pricingPage.tiers.free.priceDetail'),
    description: t('marketing.pricingPage.tiers.free.description'),
    features: [
      t('marketing.pricingPage.tiers.free.features.0'),
      t('marketing.pricingPage.tiers.free.features.1'),
      t('marketing.pricingPage.tiers.free.features.2'),
      t('marketing.pricingPage.tiers.free.features.3'),
    ],
    limitations: [
      t('marketing.pricingPage.tiers.free.limitations.0'),
      t('marketing.pricingPage.tiers.free.limitations.1'),
    ],
    cta: currentTier.value === 'free' ? t('marketing.pricingPage.currentPlan') : t('marketing.pricingPage.tiers.free.ctaDefault'),
    ctaVariant: 'outline',
    current: currentTier.value === 'free',
  },
  {
    id: 'pro',
    name: t('marketing.pricingPage.tiers.pro.name'),
    price: '$9.9',
    priceDetail: t('marketing.pricingPage.tiers.pro.priceDetail'),
    description: t('marketing.pricingPage.tiers.pro.description'),
    features: [
      t('marketing.pricingPage.tiers.pro.features.0'),
      t('marketing.pricingPage.tiers.pro.features.1'),
      t('marketing.pricingPage.tiers.pro.features.2'),
      t('marketing.pricingPage.tiers.pro.features.3'),
      t('marketing.pricingPage.tiers.pro.features.4'),
    ],
    limitations: [t('marketing.pricingPage.tiers.pro.limitations.0')],
    cta: currentTier.value === 'pro' ? t('marketing.pricingPage.currentPlan') : t('marketing.pricingPage.tiers.pro.ctaDefault'),
    ctaVariant: 'primary',
    popular: true,
    current: currentTier.value === 'pro',
  },
  {
    id: 'enterprise',
    name: t('marketing.pricingPage.tiers.enterprise.name'),
    price: enterprisePrice.value,
    priceDetail: t('marketing.pricingPage.tiers.enterprise.priceDetail'),
    description: t('marketing.pricingPage.tiers.enterprise.description'),
    features: [
      t('marketing.pricingPage.tiers.enterprise.features.0'),
      t('marketing.pricingPage.tiers.enterprise.features.1'),
      t('marketing.pricingPage.tiers.enterprise.features.2'),
      t('marketing.pricingPage.tiers.enterprise.features.3'),
    ],
    limitations: [t('marketing.pricingPage.tiers.enterprise.limitations.0')],
    cta: currentTier.value === 'enterprise' ? t('marketing.pricingPage.currentPlan') : t('marketing.pricingPage.tiers.enterprise.ctaDefault'),
    ctaVariant: 'outline',
    current: currentTier.value === 'enterprise',
  },
])

const handleCTA = async (tier: PricingTier) => {
  if (tier.current) {
    router.push('/auth/profile')
    return
  }

  if (tier.id === 'free') {
    router.push('/')
    return
  }

  if (tier.id === 'pro') {
    if (!isLoggedIn.value) {
      router.push('/auth/login?redirect=/pricing')
      return
    }

    try {
      const { paymentAPI } = await import('@/services/api')
      const response = await paymentAPI.createCheckoutSession({
        plan: 'monthly',
        success_url: `${window.location.origin}/payment/success`,
        cancel_url: `${window.location.origin}/payment/cancel`,
      })
      window.location.href = response.checkout_url
    } catch (error) {
      console.error('Failed to create checkout session:', error)
      alert(t('marketing.pricingPage.alerts.paymentStartFailed'))
    }
    return
  }

  if (tier.id === 'enterprise') {
    window.location.href = 'mailto:sales@pdf-flow.com?subject=Enterprise Plan Inquiry'
  }
}
</script>

<template>
  <div
    class="pricing-page min-h-screen bg-background-light p-8 dark:bg-background-dark"
    :data-locale="activeLocale"
  >
    <div class="mx-auto max-w-7xl">
      <div class="mb-12 text-center">
        <h1 class="mb-4 text-4xl font-bold text-gray-900 dark:text-white">
          {{ t('marketing.pricingPage.title') }}
        </h1>
        <p class="text-xl text-gray-600 dark:text-gray-300">
          {{ t('marketing.pricingPage.description') }}
        </p>
        <div class="mt-6 flex justify-center gap-4">
          <span class="inline-flex items-center rounded-lg bg-success/10 px-4 py-2 text-sm font-medium text-success">
            {{ t('marketing.pricingPage.badges.refund') }}
          </span>
          <span class="inline-flex items-center rounded-lg bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            {{ t('marketing.pricingPage.badges.cancel') }}
          </span>
          <span class="inline-flex items-center rounded-lg bg-warning/10 px-4 py-2 text-sm font-medium text-warning">
            {{ t('marketing.pricingPage.badges.security') }}
          </span>
        </div>
      </div>

      <div class="grid gap-8 md:grid-cols-3">
        <div
          v-for="tier in pricingTiers"
          :key="tier.name"
          class="relative"
        >
          <div
            v-if="tier.popular"
            class="absolute -top-4 left-1/2 -translate-x-1/2 transform"
          >
            <span class="rounded-full bg-gradient-to-r from-primary to-purple-600 px-4 py-1 text-sm font-semibold text-white shadow-lg">
              {{ t('marketing.pricingPage.popular') }}
            </span>
          </div>

          <Card
            :class="[
              'h-full transition-all',
              tier.popular ? 'border-2 border-primary shadow-xl' : '',
              tier.current ? 'ring-2 ring-success' : '',
            ]"
          >
            <div class="flex h-full flex-col p-6">
              <div class="mb-4">
                <h3 class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ tier.name }}
                </h3>
                <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {{ tier.description }}
                </p>
              </div>

              <div class="mb-6">
                <div class="flex items-baseline">
                  <span class="text-4xl font-extrabold text-gray-900 dark:text-white">
                    {{ tier.price }}
                  </span>
                </div>
                <p class="mt-1 text-sm text-gray-500">
                  {{ tier.priceDetail }}
                </p>
              </div>

              <div
                v-if="tier.current"
                class="mb-4 rounded-lg bg-success/10 px-3 py-2 text-center text-sm font-medium text-success"
              >
                {{ t('marketing.pricingPage.currentPlan') }}
              </div>

              <Button
                :variant="tier.ctaVariant"
                size="lg"
                full-width
                class="mb-6"
                @click="handleCTA(tier)"
              >
                {{ tier.cta }}
              </Button>

              <div class="flex-1">
                <h4 class="mb-3 text-sm font-semibold text-gray-900 dark:text-white">
                  {{ t('marketing.pricingPage.featuresLabel') }}
                </h4>
                <ul class="space-y-2">
                  <li
                    v-for="(feature, index) in tier.features"
                    :key="index"
                    class="flex items-start text-sm text-gray-600 dark:text-gray-300"
                  >
                    <span>{{ feature }}</span>
                  </li>
                </ul>

                <div
                  v-if="tier.limitations"
                  class="mt-4"
                >
                  <h4 class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-400">
                    {{ t('marketing.pricingPage.limitationsLabel') }}
                  </h4>
                  <ul class="space-y-1">
                    <li
                      v-for="(limitation, index) in tier.limitations"
                      :key="index"
                      class="text-xs text-gray-500 dark:text-gray-500"
                    >
                      {{ limitation }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div class="mt-16">
        <h2 class="mb-8 text-center text-3xl font-bold text-gray-900 dark:text-white">
          {{ t('marketing.pricingPage.faqTitle') }}
        </h2>
        <div class="grid gap-6 md:grid-cols-2">
          <Card>
            <div class="p-6">
              <h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                {{ t('marketing.pricingPage.faq.upgrade.q') }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ t('marketing.pricingPage.faq.upgrade.a') }}
              </p>
            </div>
          </Card>

          <Card>
            <div class="p-6">
              <h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                {{ t('marketing.pricingPage.faq.cancel.q') }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ t('marketing.pricingPage.faq.cancel.a') }}
              </p>
            </div>
          </Card>

          <Card>
            <div class="p-6">
              <h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                {{ t('marketing.pricingPage.faq.security.q') }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ t('marketing.pricingPage.faq.security.a') }}
              </p>
            </div>
          </Card>

          <Card>
            <div class="p-6">
              <h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                {{ t('marketing.pricingPage.faq.enterprise.q') }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ t('marketing.pricingPage.faq.enterprise.a') }}
              </p>
            </div>
          </Card>
        </div>
      </div>

      <div class="mt-16 rounded-2xl bg-gradient-to-r from-primary/10 to-purple-500/10 p-8 text-center">
        <h3 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('marketing.pricingPage.trust.title') }}
        </h3>
        <p class="mb-6 text-gray-600 dark:text-gray-300">
          {{ t('marketing.pricingPage.trust.description') }}
        </p>
        <div class="flex flex-wrap justify-center gap-6">
          <div class="text-center">
            <div class="text-3xl font-bold text-primary">99.9%</div>
            <div class="text-sm text-gray-600">{{ t('marketing.pricingPage.trust.metrics.availability') }}</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-success">4.9/5</div>
            <div class="text-sm text-gray-600">{{ t('marketing.pricingPage.trust.metrics.feedback') }}</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-warning">&lt; 2s</div>
            <div class="text-sm text-gray-600">{{ t('marketing.pricingPage.trust.metrics.processing') }}</div>
          </div>
        </div>
      </div>

      <div class="mt-16 text-center">
        <p class="mb-4 text-lg text-gray-600 dark:text-gray-300">
          {{ t('marketing.pricingPage.bottomPrompt') }}
        </p>
        <Button
          variant="primary"
          size="lg"
          @click="router.push('/auth/register')"
        >
          {{ t('marketing.pricingPage.bottomAction') }}
        </Button>
      </div>
    </div>
  </div>
</template>
