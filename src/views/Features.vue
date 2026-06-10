<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'

const { t, locale } = useI18n()
const router = useRouter()
const activeLocale = computed(() => locale.value)

interface Feature {
  icon: string
  title: string
  description: string
  details: string[]
}

const coreFeatures = computed<Feature[]>(() => [
  {
    icon: 'Shield',
    title: t('marketing.featuresPage.coreFeatures.privacy.title'),
    description: t('marketing.featuresPage.coreFeatures.privacy.description'),
    details: [
      t('marketing.featuresPage.coreFeatures.privacy.details.0'),
      t('marketing.featuresPage.coreFeatures.privacy.details.1'),
      t('marketing.featuresPage.coreFeatures.privacy.details.2'),
      t('marketing.featuresPage.coreFeatures.privacy.details.3'),
    ],
  },
  {
    icon: 'Zap',
    title: t('marketing.featuresPage.coreFeatures.speed.title'),
    description: t('marketing.featuresPage.coreFeatures.speed.description'),
    details: [
      t('marketing.featuresPage.coreFeatures.speed.details.0'),
      t('marketing.featuresPage.coreFeatures.speed.details.1'),
      t('marketing.featuresPage.coreFeatures.speed.details.2'),
      t('marketing.featuresPage.coreFeatures.speed.details.3'),
    ],
  },
  {
    icon: 'Cloud',
    title: t('marketing.featuresPage.coreFeatures.cloud.title'),
    description: t('marketing.featuresPage.coreFeatures.cloud.description'),
    details: [
      t('marketing.featuresPage.coreFeatures.cloud.details.0'),
      t('marketing.featuresPage.coreFeatures.cloud.details.1'),
      t('marketing.featuresPage.coreFeatures.cloud.details.2'),
      t('marketing.featuresPage.coreFeatures.cloud.details.3'),
    ],
  },
  {
    icon: 'Layout',
    title: t('marketing.featuresPage.coreFeatures.design.title'),
    description: t('marketing.featuresPage.coreFeatures.design.description'),
    details: [
      t('marketing.featuresPage.coreFeatures.design.details.0'),
      t('marketing.featuresPage.coreFeatures.design.details.1'),
      t('marketing.featuresPage.coreFeatures.design.details.2'),
      t('marketing.featuresPage.coreFeatures.design.details.3'),
    ],
  },
  {
    icon: 'Languages',
    title: t('marketing.featuresPage.coreFeatures.languages.title'),
    description: t('marketing.featuresPage.coreFeatures.languages.description'),
    details: [
      t('marketing.featuresPage.coreFeatures.languages.details.0'),
      t('marketing.featuresPage.coreFeatures.languages.details.1'),
      t('marketing.featuresPage.coreFeatures.languages.details.2'),
      t('marketing.featuresPage.coreFeatures.languages.details.3'),
    ],
  },
  {
    icon: 'Blocks',
    title: t('marketing.featuresPage.coreFeatures.tools.title'),
    description: t('marketing.featuresPage.coreFeatures.tools.description'),
    details: [
      t('marketing.featuresPage.coreFeatures.tools.details.0'),
      t('marketing.featuresPage.coreFeatures.tools.details.1'),
      t('marketing.featuresPage.coreFeatures.tools.details.2'),
      t('marketing.featuresPage.coreFeatures.tools.details.3'),
    ],
  },
])

const technicalFeatures = computed(() => [
  {
    icon: 'Stack',
    title: t('marketing.featuresPage.technicalFeatures.stack.title'),
    items: [
      t('marketing.featuresPage.technicalFeatures.stack.items.0'),
      t('marketing.featuresPage.technicalFeatures.stack.items.1'),
      t('marketing.featuresPage.technicalFeatures.stack.items.2'),
      t('marketing.featuresPage.technicalFeatures.stack.items.3'),
    ],
  },
  {
    icon: 'Lock',
    title: t('marketing.featuresPage.technicalFeatures.security.title'),
    items: [
      t('marketing.featuresPage.technicalFeatures.security.items.0'),
      t('marketing.featuresPage.technicalFeatures.security.items.1'),
      t('marketing.featuresPage.technicalFeatures.security.items.2'),
      t('marketing.featuresPage.technicalFeatures.security.items.3'),
    ],
  },
  {
    icon: 'Gauge',
    title: t('marketing.featuresPage.technicalFeatures.performance.title'),
    items: [
      t('marketing.featuresPage.technicalFeatures.performance.items.0'),
      t('marketing.featuresPage.technicalFeatures.performance.items.1'),
      t('marketing.featuresPage.technicalFeatures.performance.items.2'),
      t('marketing.featuresPage.technicalFeatures.performance.items.3'),
    ],
  },
  {
    icon: 'Check',
    title: t('marketing.featuresPage.technicalFeatures.quality.title'),
    items: [
      t('marketing.featuresPage.technicalFeatures.quality.items.0'),
      t('marketing.featuresPage.technicalFeatures.quality.items.1'),
      t('marketing.featuresPage.technicalFeatures.quality.items.2'),
      t('marketing.featuresPage.technicalFeatures.quality.items.3'),
    ],
  },
])
</script>

<template>
  <div
    class="features-page min-h-screen bg-background-light dark:bg-background-dark"
    :data-locale="activeLocale"
  >
    <div class="bg-gradient-to-br from-primary/10 via-purple-500/10 to-pink-500/10 py-20">
      <div class="container mx-auto px-4 text-center">
        <h1 class="mb-4 text-5xl font-bold text-gray-900 dark:text-white">
          {{ t('marketing.featuresPage.heroTitle') }}
        </h1>
        <p class="mx-auto max-w-2xl text-xl text-gray-600 dark:text-gray-300">
          {{ t('marketing.featuresPage.heroDescription') }}
        </p>
        <div class="mt-8 flex justify-center gap-4">
          <Button
            variant="primary"
            size="lg"
            @click="router.push('/')"
          >
            {{ t('marketing.featuresPage.startButton') }}
          </Button>
          <Button
            variant="outline"
            size="lg"
            @click="router.push('/pricing')"
          >
            {{ t('marketing.featuresPage.pricingButton') }}
          </Button>
        </div>
      </div>
    </div>

    <div class="container mx-auto px-4 py-16">
      <div class="mb-12 text-center">
        <h2 class="mb-4 text-3xl font-bold text-gray-900 dark:text-white">
          {{ t('marketing.featuresPage.coreTitle') }}
        </h2>
        <p class="text-lg text-gray-600 dark:text-gray-300">
          {{ t('marketing.featuresPage.coreDescription') }}
        </p>
      </div>

      <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        <Card
          v-for="feature in coreFeatures"
          :key="feature.title"
          class="transition-all hover:shadow-xl"
        >
          <div class="p-6">
            <div class="mb-4 text-2xl font-semibold text-primary">
              {{ feature.icon }}
            </div>
            <h3 class="mb-2 text-xl font-bold text-gray-900 dark:text-white">
              {{ feature.title }}
            </h3>
            <p class="mb-4 text-gray-600 dark:text-gray-400">
              {{ feature.description }}
            </p>
            <ul class="space-y-2">
              <li
                v-for="detail in feature.details"
                :key="detail"
                class="flex items-start text-sm text-gray-600 dark:text-gray-300"
              >
                <span class="mr-2 text-success">+</span>
                <span>{{ detail }}</span>
              </li>
            </ul>
          </div>
        </Card>
      </div>
    </div>

    <div class="bg-gray-50 py-16 dark:bg-gray-900">
      <div class="container mx-auto px-4">
        <div class="mb-12 text-center">
          <h2 class="mb-4 text-3xl font-bold text-gray-900 dark:text-white">
            {{ t('marketing.featuresPage.technicalTitle') }}
          </h2>
          <p class="text-lg text-gray-600 dark:text-gray-300">
            {{ t('marketing.featuresPage.technicalDescription') }}
          </p>
        </div>

        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card
            v-for="tech in technicalFeatures"
            :key="tech.title"
          >
            <div class="p-6 text-center">
              <div class="mb-4 text-xl font-semibold text-primary">
                {{ tech.icon }}
              </div>
              <h3 class="mb-4 text-lg font-bold text-gray-900 dark:text-white">
                {{ tech.title }}
              </h3>
              <ul class="space-y-2">
                <li
                  v-for="item in tech.items"
                  :key="item"
                  class="text-sm text-gray-600 dark:text-gray-400"
                >
                  {{ item }}
                </li>
              </ul>
            </div>
          </Card>
        </div>
      </div>
    </div>

    <div class="container mx-auto px-4 py-16">
      <div class="mb-12 text-center">
        <h2 class="mb-4 text-3xl font-bold text-gray-900 dark:text-white">
          {{ t('marketing.featuresPage.comparisonTitle') }}
        </h2>
        <p class="text-lg text-gray-600 dark:text-gray-300">
          {{ t('marketing.featuresPage.comparisonDescription') }}
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b-2 border-gray-200 dark:border-gray-700">
              <th class="p-4 text-left text-gray-900 dark:text-white">{{ t('marketing.featuresPage.comparisonHeaders.feature') }}</th>
              <th class="p-4 text-center">
                <div class="font-bold text-primary">PDF-Flow</div>
              </th>
              <th class="p-4 text-center text-gray-600 dark:text-gray-400">{{ t('marketing.featuresPage.comparisonHeaders.competitorA') }}</th>
              <th class="p-4 text-center text-gray-600 dark:text-gray-400">{{ t('marketing.featuresPage.comparisonHeaders.competitorB') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-gray-100 dark:border-gray-800">
              <td class="p-4">{{ t('marketing.featuresPage.comparisonRows.privacy') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
            </tr>
            <tr class="border-b border-gray-100 dark:border-gray-800">
              <td class="p-4">{{ t('marketing.featuresPage.comparisonRows.free') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-warning text-xl">{{ t('marketing.featuresPage.comparisonRows.partial') }}</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
            </tr>
            <tr class="border-b border-gray-100 dark:border-gray-800">
              <td class="p-4">{{ t('marketing.featuresPage.comparisonRows.progress') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
            </tr>
            <tr class="border-b border-gray-100 dark:border-gray-800">
              <td class="p-4">{{ t('marketing.featuresPage.comparisonRows.ocr') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-warning text-xl">{{ t('marketing.featuresPage.comparisonRows.paid') }}</td>
            </tr>
            <tr class="border-b border-gray-100 dark:border-gray-800">
              <td class="p-4">{{ t('marketing.featuresPage.comparisonRows.open') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
              <td class="p-4 text-center text-error text-2xl">-</td>
            </tr>
            <tr>
              <td class="p-4">{{ t('marketing.featuresPage.comparisonRows.api') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
              <td class="p-4 text-center text-warning text-xl">{{ t('marketing.featuresPage.comparisonRows.expensive') }}</td>
              <td class="p-4 text-center text-success text-2xl">+</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="bg-gradient-to-r from-primary to-purple-600 py-16 text-white">
      <div class="container mx-auto px-4 text-center">
        <h2 class="mb-4 text-3xl font-bold">
          {{ t('marketing.featuresPage.ctaTitle') }}
        </h2>
        <p class="mb-8 text-xl opacity-90">
          {{ t('marketing.featuresPage.ctaDescription') }}
        </p>
        <div class="flex justify-center gap-4">
          <Button
            variant="outline"
            size="lg"
            class="border-white text-white hover:bg-white hover:text-primary"
            @click="router.push('/auth/register')"
          >
            {{ t('marketing.featuresPage.ctaRegister') }}
          </Button>
          <Button
            variant="ghost"
            size="lg"
            class="text-white hover:bg-white/10"
            @click="router.push('/pricing')"
          >
            {{ t('marketing.featuresPage.ctaPricing') }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
