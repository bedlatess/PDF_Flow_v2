<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Card from '@/components/common/Card.vue'

const { t, locale } = useI18n()
const router = useRouter()
const activeLocale = computed(() => locale.value)

interface Tool {
  name: string
  titleKey: string
  descriptionKey: string
  icon: string
  route: string
  color: string
}

const tools = computed<Tool[]>(() => [
  {
    name: 'merge',
    titleKey: 'tools.merge.title',
    descriptionKey: 'tools.merge.desc',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
    route: '/tools/merge',
    color: 'bg-blue-500',
  },
  {
    name: 'split',
    titleKey: 'tools.split.title',
    descriptionKey: 'tools.split.desc',
    icon: 'M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5',
    route: '/tools/split',
    color: 'bg-green-500',
  },
  {
    name: 'rotate',
    titleKey: 'tools.rotate.title',
    descriptionKey: 'tools.rotate.desc',
    icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
    route: '/tools/rotate',
    color: 'bg-purple-500',
  },
  {
    name: 'compress',
    titleKey: 'tools.compress.title',
    descriptionKey: 'tools.compress.desc',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4',
    route: '/tools/compress',
    color: 'bg-indigo-500',
  },
  {
    name: 'imageToPdf',
    titleKey: 'tools.imageToPdf.title',
    descriptionKey: 'tools.imageToPdf.desc',
    icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
    route: '/tools/image-to-pdf',
    color: 'bg-orange-500',
  },
  {
    name: 'pdfToImage',
    titleKey: 'tools.pdfToImage.title',
    descriptionKey: 'tools.pdfToImage.desc',
    icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    route: '/tools/pdf-to-image',
    color: 'bg-red-500',
  },
  {
    name: 'ocr',
    titleKey: 'tools.ocr.title',
    descriptionKey: 'home.toolDescriptions.ocr',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    route: '/tools/ocr',
    color: 'bg-pink-500',
  },
  {
    name: 'officeToPdf',
    titleKey: 'tools.officeToPdf.title',
    descriptionKey: 'tools.officeToPdf.desc',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    route: '/tools/office-to-pdf',
    color: 'bg-teal-500',
  },
  {
    name: 'aiAnalyzer',
    titleKey: 'ai.title',
    descriptionKey: 'home.toolDescriptions.aiAnalyzer',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    route: '/tools/ai-analyzer',
    color: 'bg-gradient-to-r from-purple-500 to-pink-500',
  },
  {
    name: 'watermark',
    titleKey: 'tools.watermark.title',
    descriptionKey: 'tools.watermark.desc',
    icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01',
    route: '/tools/watermark',
    color: 'bg-cyan-500',
  },
  {
    name: 'fillForm',
    titleKey: 'tools.fillForm.title',
    descriptionKey: 'tools.fillForm.description',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    route: '/tools/fill-form',
    color: 'bg-emerald-500',
  },
  {
    name: 'annotate',
    titleKey: 'tools.annotate.title',
    descriptionKey: 'tools.annotate.description',
    icon: 'M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z',
    route: '/tools/annotate',
    color: 'bg-amber-500',
  },
])

const featureHighlights = computed(() => [
  {
    title: t('home.highlights.privacy.title'),
    description: t('home.highlights.privacy.description'),
    accent: 'bg-primary/10',
    textColor: 'text-primary',
    iconPath: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
  },
  {
    title: t('home.highlights.speed.title'),
    description: t('home.highlights.speed.description'),
    accent: 'bg-success/10',
    textColor: 'text-success',
    iconPath: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
  {
    title: t('home.highlights.free.title'),
    description: t('home.highlights.free.description'),
    accent: 'bg-warning/10',
    textColor: 'text-warning',
    iconPath: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z',
  },
])

const navigateToTool = (route: string) => {
  router.push(route)
}
</script>

<template>
  <div
    class="home-container min-h-screen bg-background-light dark:bg-background-dark"
    :data-locale="activeLocale"
  >
    <!-- Hero Section -->
    <section class="hero py-20">
      <div class="container mx-auto px-4">
        <div class="text-center">
          <h1 class="mb-4 text-5xl font-bold text-gray-900 dark:text-white">
            {{ t('app.title') }}
          </h1>
          <p class="mb-8 text-xl text-gray-600 dark:text-gray-300">
            {{ t('app.tagline') }}
          </p>
          <div class="flex justify-center gap-4">
            <span
              class="inline-flex items-center rounded-lg bg-primary/10 px-4 py-2 text-sm font-medium text-primary"
            >
              {{ t('common.privacyBadge') }}
            </span>
            <span
              class="inline-flex items-center rounded-lg bg-success/10 px-4 py-2 text-sm font-medium text-success"
            >
              {{ t('home.badges.fast') }}
            </span>
            <span
              class="inline-flex items-center rounded-lg bg-warning/10 px-4 py-2 text-sm font-medium text-warning"
            >
              {{ t('home.badges.languages') }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tools Grid -->
    <section class="tools-grid pb-20">
      <div class="container mx-auto px-4">
        <h2 class="mb-8 text-center text-3xl font-bold text-gray-900 dark:text-white">
          {{ t('home.toolsTitle') }}
        </h2>

        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Card
            v-for="tool in tools"
            :key="tool.name"
            data-testid="tool-card"
            variant="glass"
            hoverable
            clickable
            @click="navigateToTool(tool.route)"
          >
            <div class="flex flex-col items-center text-center">
              <!-- Icon -->
              <div
                :class="[
                  'mb-4 flex h-16 w-16 items-center justify-center rounded-full',
                  tool.color,
                  'text-white shadow-lg',
                ]"
              >
                <svg
                  class="h-8 w-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    :d="tool.icon"
                  />
                </svg>
              </div>

              <!-- Title -->
              <h3 class="mb-2 text-xl font-semibold text-gray-900 dark:text-white">
                {{ t(tool.titleKey) }}
              </h3>

              <!-- Description -->
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ t(tool.descriptionKey) }}
              </p>

              <!-- Arrow -->
              <div class="mt-4 text-primary">
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
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features bg-white py-16 dark:bg-gray-900">
      <div class="container mx-auto px-4">
        <h2 class="mb-12 text-center text-3xl font-bold text-gray-900 dark:text-white">
          {{ t('home.whyTitle') }}
        </h2>

        <div class="grid gap-8 md:grid-cols-3">
          <div
            v-for="highlight in featureHighlights"
            :key="highlight.title"
            class="text-center"
          >
            <div class="mb-4 flex justify-center">
              <div :class="['rounded-full p-4', highlight.accent]">
                <svg
                  :class="['h-8 w-8', highlight.textColor]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    :d="highlight.iconPath"
                  />
                </svg>
              </div>
            </div>
            <h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
              {{ highlight.title }}
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-300">
              {{ highlight.description }}
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
}

.dark .hero {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}
</style>
