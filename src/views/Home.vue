<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useSiteConfigStore } from '@/stores/siteConfig'
import ProBadge from '@/components/common/ProBadge.vue'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()
const siteConfigStore = useSiteConfigStore()
const activeLocale = computed(() => locale.value)

interface Tool {
  name: string
  titleKey: string
  descriptionKey: string
  icon: string
  route: string
  color: string
  glow: string
  featureKey: string
}

const tools = computed<Tool[]>(() => [
  {
    name: 'merge',
    titleKey: 'tools.merge.title',
    descriptionKey: 'tools.merge.desc',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
    route: '/tools/merge',
    color: 'from-sky-500 to-blue-600',
    glow: 'bg-sky-400/20',
    featureKey: 'merge_pdf',
  },
  {
    name: 'split',
    titleKey: 'tools.split.title',
    descriptionKey: 'tools.split.desc',
    icon: 'M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5',
    route: '/tools/split',
    color: 'from-emerald-500 to-teal-600',
    glow: 'bg-emerald-400/20',
    featureKey: 'split_pdf',
  },
  {
    name: 'rotate',
    titleKey: 'tools.rotate.title',
    descriptionKey: 'tools.rotate.desc',
    icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
    route: '/tools/rotate',
    color: 'from-violet-500 to-fuchsia-600',
    glow: 'bg-violet-400/20',
    featureKey: 'rotate_pdf',
  },
  {
    name: 'compress',
    titleKey: 'tools.compress.title',
    descriptionKey: 'tools.compress.desc',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4',
    route: '/tools/compress',
    color: 'from-indigo-500 to-blue-700',
    glow: 'bg-indigo-400/20',
    featureKey: 'compress_pdf',
  },
  {
    name: 'imageToPdf',
    titleKey: 'tools.imageToPdf.title',
    descriptionKey: 'tools.imageToPdf.desc',
    icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
    route: '/tools/image-to-pdf',
    color: 'from-orange-400 to-rose-500',
    glow: 'bg-orange-300/25',
    featureKey: 'image_to_pdf',
  },
  {
    name: 'pdfToImage',
    titleKey: 'tools.pdfToImage.title',
    descriptionKey: 'tools.pdfToImage.desc',
    icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    route: '/tools/pdf-to-image',
    color: 'from-rose-500 to-red-600',
    glow: 'bg-rose-400/20',
    featureKey: 'pdf_to_image',
  },
  {
    name: 'deletePages',
    titleKey: 'tools.deletePages.title',
    descriptionKey: 'tools.deletePages.desc',
    icon: 'M14.121 14.121L19 19m-4.879-4.879a3 3 0 10-4.243-4.242m4.243 4.242L9.879 9.879m0 0L5 5m4.879 4.879a3 3 0 11-4.243 4.242M9.879 9.879L5 14.758',
    route: '/tools/delete-pages',
    color: 'from-red-500 to-orange-600',
    glow: 'bg-red-400/18',
    featureKey: 'delete_pages_pdf',
  },
  {
    name: 'organize',
    titleKey: 'tools.organize.title',
    descriptionKey: 'tools.organize.desc',
    icon: 'M4 6h16M4 12h16M4 18h7m6-3l3 3m0 0l-3 3m3-3H9',
    route: '/tools/organize',
    color: 'from-emerald-500 to-cyan-600',
    glow: 'bg-emerald-400/18',
    featureKey: 'organize_pdf',
  },
  {
    name: 'pageNumbers',
    titleKey: 'tools.pageNumbers.title',
    descriptionKey: 'tools.pageNumbers.desc',
    icon: 'M7 20l4-16m2 16l4-16M6 9h14M4 15h14',
    route: '/tools/page-numbers',
    color: 'from-blue-500 to-cyan-600',
    glow: 'bg-blue-400/18',
    featureKey: 'page_numbers_pdf',
  },
  {
    name: 'protect',
    titleKey: 'tools.protect.title',
    descriptionKey: 'tools.protect.desc',
    icon: 'M12 11c1.105 0 2 .895 2 2v2a2 2 0 11-4 0v-2c0-1.105.895-2 2-2zm6 0V8a6 6 0 10-12 0v3m12 0H6a2 2 0 00-2 2v6a2 2 0 002 2h12a2 2 0 002-2v-6a2 2 0 00-2-2z',
    route: '/tools/protect',
    color: 'from-slate-700 to-blue-700',
    glow: 'bg-blue-400/18',
    featureKey: 'protect_pdf',
  },
  {
    name: 'ocr',
    titleKey: 'tools.ocr.title',
    descriptionKey: 'home.toolDescriptions.ocr',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    route: '/tools/ocr',
    color: 'from-pink-500 to-fuchsia-600',
    glow: 'bg-pink-400/22',
    featureKey: 'ocr_pdf',
  },
  {
    name: 'officeToPdf',
    titleKey: 'tools.officeToPdf.title',
    descriptionKey: 'tools.officeToPdf.desc',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    route: '/tools/office-to-pdf',
    color: 'from-teal-500 to-cyan-600',
    glow: 'bg-cyan-400/20',
    featureKey: 'office_to_pdf',
  },
  {
    name: 'aiAnalyzer',
    titleKey: 'ai.title',
    descriptionKey: 'home.toolDescriptions.aiAnalyzer',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    route: '/tools/ai-analyzer',
    color: 'from-purple-500 to-pink-600',
    glow: 'bg-purple-400/22',
    featureKey: 'ai_analyzer',
  },
  {
    name: 'watermark',
    titleKey: 'tools.watermark.title',
    descriptionKey: 'tools.watermark.desc',
    icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01',
    route: '/tools/watermark',
    color: 'from-cyan-500 to-sky-600',
    glow: 'bg-cyan-400/20',
    featureKey: 'watermark_pdf',
  },
  {
    name: 'fillForm',
    titleKey: 'tools.fillForm.title',
    descriptionKey: 'tools.fillForm.description',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    route: '/tools/fill-form',
    color: 'from-emerald-500 to-lime-600',
    glow: 'bg-emerald-400/22',
    featureKey: 'fill_form',
  },
  {
    name: 'annotate',
    titleKey: 'tools.annotate.title',
    descriptionKey: 'tools.annotate.description',
    icon: 'M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z',
    route: '/tools/annotate',
    color: 'from-amber-400 to-orange-600',
    glow: 'bg-amber-300/25',
    featureKey: 'annotate_pdf',
  },
])

const visibleTools = computed(() =>
  tools.value
    .map((tool) => ({
      ...tool,
      flag: siteConfigStore.getFeatureFlag(tool.featureKey, t(tool.titleKey)),
    }))
    .filter((tool) => tool.flag.enabled)
)

const disabledFeatureMessage = computed(() => {
  const featureKey = route.query.disabledFeature
  if (typeof featureKey !== 'string') return ''

  const flag = siteConfigStore.getFeatureFlag(featureKey)
  return flag.maintenance_message || '该功能正在维护中，暂时无法使用。'
})

const homeHeroBlock = computed(() =>
  siteConfigStore.getContentBlock('home_hero', locale.value, {
    title: t('app.title'),
    content: t('app.tagline'),
    description: null,
  })
)

const isChinese = computed(() => locale.value.toLowerCase().startsWith('zh'))
const isSpanish = computed(() => locale.value.toLowerCase().startsWith('es'))

const homeCopy = computed(() => {
  if (isChinese.value) {
    return {
      eyebrow: '隐私优先的 PDF 工作台',
      heroTitle: '把常用 PDF 工具、云端增强和 AI 能力放进一个清爽工作区',
      heroDescription: '小文件优先本地快速处理，大文件、OCR、Office、AI 等任务按需交给云端。免费功能和 Pro 能力清楚区分，使用路径更直观。',
      start: '开始处理文件',
      pricing: '查看 Pro 能力',
      localLabel: '本地优先',
      localText: '合并、拆分、旋转等日常任务尽量留在浏览器完成。',
      cloudLabel: '云端增强',
      cloudText: '大文件、长任务和专业格式转换更稳定。',
      proLabel: 'Pro 能力',
      proText: 'OCR、AI、表单和标注等高级工作流清楚标识。',
      workspaceLabel: 'PDF Workspace',
      toolsHint: '常用工具保持轻快，专业能力用 Pro 角标清楚区分。',
      whyTitle: '一个更安静、更清楚的 PDF 工作流',
    }
  }

  if (isSpanish.value) {
    return {
      eyebrow: 'Espacio PDF con privacidad primero',
      heroTitle: 'Herramientas PDF, nube avanzada e IA en un espacio claro',
      heroDescription: 'Los archivos pequeños se procesan localmente cuando conviene. Archivos grandes, OCR, Office e IA usan la nube cuando aporta más estabilidad.',
      start: 'Empezar',
      pricing: 'Ver Pro',
      localLabel: 'Local primero',
      localText: 'Fusionar, dividir y rotar permanecen en el navegador cuando es posible.',
      cloudLabel: 'Nube avanzada',
      cloudText: 'Archivos grandes y tareas largas son más estables en la nube.',
      proLabel: 'Funciones Pro',
      proText: 'OCR, IA, formularios y anotaciones se distinguen con claridad.',
      workspaceLabel: 'PDF Workspace',
      toolsHint: 'Herramientas diarias rápidas, funciones Pro claramente marcadas.',
      whyTitle: 'Un flujo PDF más claro y tranquilo',
    }
  }

  return {
    eyebrow: 'Privacy-first PDF workspace',
    heroTitle: 'Everyday PDF tools, cloud boosts, and AI in one calmer workspace',
    heroDescription: 'Small files stay fast locally when possible. Large files, OCR, Office, and AI workflows use the cloud when it adds stability.',
    start: 'Start processing',
    pricing: 'View Pro',
    localLabel: 'Local first',
    localText: 'Merge, split, and rotate stay in the browser whenever possible.',
    cloudLabel: 'Cloud boost',
    cloudText: 'Large files and long jobs are more stable in the cloud.',
    proLabel: 'Pro features',
    proText: 'OCR, AI, forms, and annotation are clearly marked.',
    workspaceLabel: 'PDF Workspace',
    toolsHint: 'Everyday tools stay fast, while Pro capabilities are clearly marked.',
    whyTitle: 'A calmer, clearer PDF workflow',
  }
})

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

onMounted(() => {
  siteConfigStore.fetchPublicConfig(true)
})
</script>

<template>
  <div
    class="home-container min-h-screen bg-background-light dark:bg-background-dark"
    :data-locale="activeLocale"
  >
    <!-- Hero Section -->
    <section class="relative overflow-hidden px-4 py-20 sm:px-6 lg:px-8">
      <div class="absolute left-1/2 top-0 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-sky-200/30 blur-3xl dark:bg-sky-500/10" />
      <div class="absolute right-0 top-10 h-72 w-72 rounded-full bg-amber-200/30 blur-3xl dark:bg-amber-500/10" />

      <div class="relative mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div class="rounded-[42px] border border-white/70 bg-white/86 p-8 shadow-2xl shadow-sky-100/60 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/74 dark:shadow-none sm:p-10">
          <div class="inline-flex items-center rounded-full border border-sky-200 bg-white/78 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-sky-700 shadow-sm backdrop-blur dark:border-sky-400/20 dark:bg-slate-950/50 dark:text-sky-200">
            {{ homeCopy.eyebrow }}
          </div>
          <h1 class="mt-6 max-w-4xl text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl lg:text-6xl">
            {{ homeHeroBlock?.title || homeCopy.heroTitle }}
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300 sm:text-lg">
            {{ homeHeroBlock?.content || homeCopy.heroDescription }}
          </p>

          <div class="mt-8 flex flex-wrap gap-3">
            <button
              class="inline-flex items-center justify-center rounded-full bg-slate-950 px-6 py-3 text-sm font-semibold text-white shadow-xl shadow-slate-900/15 transition hover:-translate-y-0.5 hover:bg-primary dark:bg-white dark:text-slate-950"
              type="button"
              @click="router.push('/tools/merge')"
            >
              {{ homeCopy.start }}
            </button>
            <button
              class="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white/70 px-6 py-3 text-sm font-semibold text-slate-700 shadow-sm backdrop-blur transition hover:-translate-y-0.5 hover:border-sky-200 hover:text-sky-700 dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-200"
              type="button"
              @click="router.push('/pricing')"
            >
              {{ homeCopy.pricing }}
            </button>
          </div>

          <div class="mt-8 flex flex-wrap gap-3">
            <span class="inline-flex items-center rounded-full bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              {{ t('common.privacyBadge') }}
            </span>
            <span class="inline-flex items-center rounded-full bg-sky-50 px-4 py-2 text-sm font-medium text-sky-700 dark:bg-sky-500/10 dark:text-sky-300">
              {{ t('home.badges.fast') }}
            </span>
            <span class="inline-flex items-center rounded-full bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 dark:bg-amber-500/10 dark:text-amber-200">
              {{ t('home.badges.languages') }}
            </span>
          </div>
        </div>

        <div class="relative rounded-[42px] border border-white/70 bg-white/72 p-4 shadow-2xl shadow-slate-200/70 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/60 dark:shadow-none">
          <div class="rounded-[34px] bg-[linear-gradient(135deg,#0f172a_0%,#164e63_48%,#92400e_100%)] p-6 text-white shadow-2xl shadow-slate-900/20">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">
                  {{ homeCopy.workspaceLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold">
                  PDF-Flow
                </h2>
              </div>
              <ProBadge tone="dark" />
            </div>

            <div class="mt-7 grid gap-4">
              <article class="rounded-[26px] border border-white/10 bg-white/10 p-5 backdrop-blur">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <h3 class="font-semibold">{{ homeCopy.localLabel }}</h3>
                    <p class="mt-2 text-sm leading-6 text-white/70">{{ homeCopy.localText }}</p>
                  </div>
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-300/15 text-emerald-100">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </span>
                </div>
              </article>

              <article class="rounded-[26px] border border-white/10 bg-white/10 p-5 backdrop-blur">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <h3 class="font-semibold">{{ homeCopy.cloudLabel }}</h3>
                    <p class="mt-2 text-sm leading-6 text-white/70">{{ homeCopy.cloudText }}</p>
                  </div>
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-300/15 text-sky-100">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h10a4 4 0 10-.8-7.9A6 6 0 105 15" />
                    </svg>
                  </span>
                </div>
              </article>

              <article class="rounded-[26px] border border-amber-200/20 bg-amber-100/10 p-5 backdrop-blur">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <h3 class="font-semibold">{{ homeCopy.proLabel }}</h3>
                    <p class="mt-2 text-sm leading-6 text-white/70">{{ homeCopy.proText }}</p>
                  </div>
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-amber-300/15 text-amber-100">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm1 4h12" />
                    </svg>
                  </span>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Tools Grid -->
    <section class="tools-grid pb-20">
      <div class="container mx-auto px-4">
        <div class="mx-auto mb-10 max-w-3xl text-center">
          <div class="mb-4 inline-flex items-center rounded-full border border-sky-200 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-sky-700 shadow-sm backdrop-blur dark:border-sky-400/20 dark:bg-slate-900/60 dark:text-sky-200">
            PDF Workspace
          </div>
          <h2 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
            {{ t('home.toolsTitle') }}
          </h2>
          <p class="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {{ homeCopy.toolsHint }}
          </p>
        </div>

        <div
          v-if="disabledFeatureMessage"
          class="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-800 shadow-sm dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100"
        >
          {{ disabledFeatureMessage }}
        </div>

        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <article
            v-for="tool in visibleTools"
            :key="tool.name"
            data-testid="tool-card"
            class="group relative min-h-[236px] cursor-pointer overflow-hidden rounded-[30px] border border-white/70 bg-white/82 p-[1px] shadow-xl shadow-slate-200/55 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-sky-200/45 dark:border-white/10 dark:bg-slate-900/70 dark:shadow-none"
            @click="navigateToTool(tool.route)"
          >
            <div
              class="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
              :class="tool.glow"
            />
            <div class="absolute -right-10 -top-10 h-28 w-28 rounded-full bg-white/45 blur-2xl dark:bg-white/5" />
            <div class="absolute bottom-0 left-0 h-px w-full bg-gradient-to-r from-transparent via-sky-300/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

            <div class="relative flex h-full min-h-[234px] flex-col rounded-[29px] bg-[linear-gradient(180deg,rgba(255,255,255,0.92)_0%,rgba(248,250,252,0.76)_100%)] p-5 text-left dark:bg-[linear-gradient(180deg,rgba(15,23,42,0.90)_0%,rgba(2,6,23,0.76)_100%)]">
              <ProBadge
                v-if="tool.flag.requires_pro"
                variant="corner"
              />

              <div class="mb-5 flex items-start justify-between gap-4">
                <div
                  :class="[
                    'relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br text-white shadow-lg transition-transform duration-300 group-hover:scale-105',
                    tool.color,
                  ]"
                >
                  <div class="absolute inset-0 rounded-2xl bg-white/18 opacity-0 transition-opacity group-hover:opacity-100" />
                  <svg
                    class="relative h-7 w-7"
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
              </div>

              <h3 class="pr-16 text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
                {{ t(tool.titleKey) }}
              </h3>
              <p class="mt-3 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t(tool.descriptionKey) }}
              </p>

              <div class="mt-6 flex items-center justify-between border-t border-slate-200/70 pt-4 dark:border-white/10">
                <span class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
                  PDF-Flow
                </span>
                <span class="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-950 text-white shadow-sm transition-all duration-300 group-hover:translate-x-1 group-hover:bg-primary dark:bg-white dark:text-slate-950">
                  <svg
                    class="h-4 w-4"
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
                </span>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features px-4 pb-20 sm:px-6 lg:px-8">
      <div class="mx-auto max-w-7xl rounded-[42px] border border-white/70 bg-white/80 p-6 shadow-2xl shadow-slate-200/60 backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/60 dark:shadow-none sm:p-8">
        <h2 class="mb-8 text-center text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
          {{ homeCopy.whyTitle }}
        </h2>

        <div class="grid gap-5 md:grid-cols-3">
          <div
            v-for="highlight in featureHighlights"
            :key="highlight.title"
            class="rounded-[28px] border border-slate-200/70 bg-slate-50/80 p-6 text-center shadow-sm dark:border-white/10 dark:bg-slate-950/45"
          >
            <div class="mb-4 flex justify-center">
              <div :class="['rounded-2xl p-4 shadow-sm', highlight.accent]">
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
