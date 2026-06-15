<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  BadgeCheck,
  Cloud,
  FileStack,
  Layers3,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-vue-next'
import ProBadge from '@/components/common/ProBadge.vue'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { pdfTools, toolCategories, type PdfToolMeta, type ToolCategory, type ToolMode } from '@/data/pdfTools'
import { useLocalePath } from '@/composables/useLocalePath'
import {
  betaToolIds,
  featureAccessSummary,
  quotaSummary,
  scanFirstToolIds,
  toneClass,
} from '@/utils/release-polish'

type ModeFilter = ToolMode | 'all'
type SpotlightGroup = 'convert' | 'scan' | 'daily'

const { t } = useI18n()
const router = useRouter()
const siteConfigStore = useSiteConfigStore()
const { localePath } = useLocalePath()

const query = ref('')
const activeCategory = ref<ToolCategory | 'all'>('all')
const activeMode = ref<ModeFilter>('all')

const copy = computed(() => {
  return {
    eyebrow: t('toolsCenter.eyebrow'),
    title: t('toolsCenter.title'),
    description: t('toolsCenter.description'),
    searchPlaceholder: t('toolsCenter.searchPlaceholder'),
    allCategories: t('toolsCenter.allCategories'),
    allModes: t('toolsCenter.allModes'),
    noResults: t('toolsCenter.noResults'),
    noResultsHint: t('toolsCenter.noResultsHint'),
    enabled: t('toolsCenter.enabled'),
    advanced: t('toolsCenter.advanced'),
    localFirst: t('toolsCenter.localFirst'),
    categoryLabel: t('toolsCenter.categoryLabel'),
    modeLabel: t('toolsCenter.modeLabel'),
    openTool: t('toolsCenter.openTool'),
    localDescription: t('toolsCenter.localDescription'),
    cloudDescription: t('toolsCenter.cloudDescription'),
    aiDescription: t('toolsCenter.aiDescription'),
    spotlightTitle: t('toolsCenter.spotlightTitle'),
    spotlightDescription: t('toolsCenter.spotlightDescription'),
    beta: t('toolsCenter.beta'),
    scanFirst: t('toolsCenter.scanFirst'),
    signInRequired: t('toolsCenter.signInRequired'),
    proRequired: t('toolsCenter.proRequired'),
    spotlightGroups: {
      convert: {
        label: t('toolsCenter.spotlightGroups.convert.label'),
        description: t('toolsCenter.spotlightGroups.convert.description'),
      },
      scan: {
        label: t('toolsCenter.spotlightGroups.scan.label'),
        description: t('toolsCenter.spotlightGroups.scan.description'),
      },
      daily: {
        label: t('toolsCenter.spotlightGroups.daily.label'),
        description: t('toolsCenter.spotlightGroups.daily.description'),
      },
    },
    categories: {
      organize: t('toolsCenter.categories.organize'),
      convert: t('toolsCenter.categories.convert'),
      optimize: t('toolsCenter.categories.optimize'),
      secure: t('toolsCenter.categories.secure'),
      extract: t('toolsCenter.categories.extract'),
      advanced: t('toolsCenter.categories.advanced'),
    },
    modes: {
      local: t('toolsCenter.modes.local'),
      cloud: t('toolsCenter.modes.cloud'),
      ai: t('toolsCenter.modes.ai'),
    },
  }
})

const modeOptions = computed(() => [
  { id: 'all' as const, label: copy.value.allModes },
  { id: 'local' as const, label: copy.value.modes.local },
  { id: 'cloud' as const, label: copy.value.modes.cloud },
  { id: 'ai' as const, label: copy.value.modes.ai },
])

const categoryOptions = computed(() => [
  { id: 'all' as const, label: copy.value.allCategories },
  ...toolCategories.map((category) => ({ id: category, label: copy.value.categories[category] })),
])

const toolsWithFlags = computed(() =>
  pdfTools
    .map((tool) => ({
      ...tool,
      flag: siteConfigStore.getFeatureFlag(tool.featureKey, t(tool.titleKey)),
    }))
    .filter((tool) => siteConfigStore.isFeatureVisible(tool.featureKey, t(tool.titleKey)))
)

const normalizedQuery = computed(() => query.value.trim().toLowerCase())

const filteredTools = computed(() =>
  toolsWithFlags.value.filter((tool) => {
    if (activeCategory.value !== 'all' && tool.category !== activeCategory.value) return false
    if (activeMode.value !== 'all' && tool.mode !== activeMode.value) return false
    if (!normalizedQuery.value) return true

    return [
      tool.id,
      t(tool.titleKey),
      t(tool.descriptionKey),
      copy.value.categories[tool.category],
      copy.value.modes[tool.mode],
    ].join(' ').toLowerCase().includes(normalizedQuery.value)
  })
)

const stats = computed(() => [
  {
    label: copy.value.enabled,
    value: toolsWithFlags.value.length,
    icon: FileStack,
  },
  {
    label: copy.value.localFirst,
    value: toolsWithFlags.value.filter((tool) => tool.mode === 'local').length,
    icon: ShieldCheck,
  },
  {
    label: copy.value.advanced,
    value: toolsWithFlags.value.filter((tool) => tool.mode !== 'local').length,
    icon: Sparkles,
  },
])

const groupedTools = computed(() =>
  toolCategories
    .map((category) => ({
      category,
      label: copy.value.categories[category],
      tools: filteredTools.value.filter((tool) => tool.category === category),
    }))
    .filter((group) => group.tools.length > 0)
)

const spotlightToolIds: Record<SpotlightGroup, string[]> = {
  convert: ['pdfToWord', 'pdfToExcel', 'htmlToPdf', 'officeToPdf'],
  scan: ['ocr', 'pdfToWord', 'pdfToExcel'],
  daily: ['merge', 'batchConvert', 'compress'],
}

const spotlightGroups = computed(() =>
  (Object.entries(spotlightToolIds) as Array<[SpotlightGroup, string[]]>)
    .map(([id, toolIds]) => ({
      id,
      ...copy.value.spotlightGroups[id],
      tools: toolIds
        .map((toolId) => toolsWithFlags.value.find((tool) => tool.id === toolId))
        .filter((tool): tool is PdfToolMeta & { flag: ReturnType<typeof siteConfigStore.getFeatureFlag> } => Boolean(tool)),
    }))
    .filter((group) => group.tools.length > 0)
)

const toolBadges = (tool: PdfToolMeta) => {
  const badges: Array<{ label: string; tone: string }> = []
  if (betaToolIds.has(tool.id)) {
    badges.push({
      label: copy.value.beta,
      tone: 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-200 dark:ring-amber-300/20',
    })
  }
  if (scanFirstToolIds.has(tool.id)) {
    badges.push({
      label: copy.value.scanFirst,
      tone: 'bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-200 dark:ring-sky-300/20',
    })
  }
  if (tool.access === 'login') {
    badges.push({
      label: copy.value.signInRequired,
      tone: 'bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-700/40 dark:text-slate-100 dark:ring-slate-500/30',
    })
  }
  if (tool.access === 'pro' || tool.requiresPro) {
    badges.push({
      label: copy.value.proRequired,
      tone: 'bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-500/10 dark:text-violet-200 dark:ring-violet-300/20',
    })
  }
  return badges
}

const releaseSummary = (tool: PdfToolMeta & { flag: ReturnType<typeof siteConfigStore.getFeatureFlag> }) => {
  const access = featureAccessSummary(tool.flag)
  return {
    access,
    quota: quotaSummary(tool.flag, false),
  }
}

const accentClassMap: Record<string, string> = {
  pdf: 'bg-red-50 text-red-700 ring-red-200 dark:bg-red-500/10 dark:text-red-200 dark:ring-red-300/20',
  emerald: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-200 dark:ring-emerald-300/20',
  amber: 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-200 dark:ring-amber-300/20',
  sky: 'bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-200 dark:ring-sky-300/20',
  rose: 'bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-500/10 dark:text-rose-200 dark:ring-rose-300/20',
  violet: 'bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-500/10 dark:text-violet-200 dark:ring-violet-300/20',
  slate: 'bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-700/40 dark:text-slate-100 dark:ring-slate-500/30',
}

const modeClassMap: Record<ToolMode, string> = {
  local: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-200 dark:ring-emerald-300/20',
  cloud: 'bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-200 dark:ring-sky-300/20',
  ai: 'bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-500/10 dark:text-violet-200 dark:ring-violet-300/20',
}

const getAccentClass = (tool: PdfToolMeta) => accentClassMap[tool.accent] || accentClassMap.slate

const openTool = (tool: PdfToolMeta) => {
  router.push(localePath(tool.route))
}

onMounted(() => {
  siteConfigStore.fetchPublicConfig(true)
})
</script>

<template>
  <main class="pf-app-surface min-h-screen text-slate-950 dark:text-white">
    <section class="border-b border-slate-200/80 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
      <div class="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
        <div class="grid gap-6 lg:grid-cols-[1fr_420px] lg:items-end">
          <div>
            <div class="inline-flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-red-700 shadow-sm dark:border-red-400/20 dark:bg-red-500/10 dark:text-red-200">
              <Layers3 class="h-4 w-4" />
              {{ copy.eyebrow }}
            </div>
            <h1 class="mt-4 text-3xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-4xl">
              {{ copy.title }}
            </h1>
            <p class="mt-3 max-w-3xl text-base leading-7 text-slate-600 dark:text-slate-300">
              {{ copy.description }}
            </p>
          </div>

          <div class="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <article
              v-for="stat in stats"
              :key="stat.label"
              class="flex items-center gap-3 rounded-md border border-slate-200 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/55"
            >
              <span class="flex h-10 w-10 items-center justify-center rounded-md bg-white text-slate-700 shadow-sm dark:bg-slate-900 dark:text-slate-200">
                <component :is="stat.icon" class="h-5 w-5" />
              </span>
              <span>
                <span class="block text-2xl font-semibold text-slate-950 dark:text-white">{{ stat.value }}</span>
                <span class="text-sm text-slate-500 dark:text-slate-400">{{ stat.label }}</span>
              </span>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <section
        v-if="spotlightGroups.length"
        class="mb-5"
      >
        <div class="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 class="text-xl font-semibold text-slate-950 dark:text-white">
              {{ copy.spotlightTitle }}
            </h2>
            <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {{ copy.spotlightDescription }}
            </p>
          </div>
        </div>

        <div class="grid gap-3 lg:grid-cols-3">
          <article
            v-for="group in spotlightGroups"
            :key="group.id"
            class="pf-panel p-4"
          >
            <div class="flex items-start gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                <BadgeCheck class="h-5 w-5" />
              </span>
              <div class="min-w-0">
                <h3 class="text-sm font-semibold text-slate-950 dark:text-white">
                  {{ group.label }}
                </h3>
                <p class="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">
                  {{ group.description }}
                </p>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <button
                v-for="tool in group.tools"
                :key="tool.id"
                type="button"
                class="inline-flex min-h-9 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-red-200 hover:text-red-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200 dark:hover:border-red-300/30 dark:hover:text-red-200"
                @click="openTool(tool)"
              >
                <component :is="tool.icon" class="h-4 w-4" />
                {{ t(tool.titleKey) }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <div class="pf-panel p-4">
        <div class="grid gap-3 lg:grid-cols-[1fr_auto_auto] lg:items-center">
          <label class="relative block">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              v-model="query"
              type="search"
              :placeholder="copy.searchPlaceholder"
              class="h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20 dark:border-white/15 dark:bg-slate-950 dark:text-white"
            >
          </label>

          <select
            v-model="activeCategory"
            class="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-red-500 focus:ring-2 focus:ring-red-500/20 dark:border-white/15 dark:bg-slate-950 dark:text-white"
            :aria-label="copy.categoryLabel"
          >
            <option
              v-for="category in categoryOptions"
              :key="category.id"
              :value="category.id"
            >
              {{ category.label }}
            </option>
          </select>

          <select
            v-model="activeMode"
            class="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-red-500 focus:ring-2 focus:ring-red-500/20 dark:border-white/15 dark:bg-slate-950 dark:text-white"
            :aria-label="copy.modeLabel"
          >
            <option
              v-for="mode in modeOptions"
              :key="mode.id"
              :value="mode.id"
            >
              {{ mode.label }}
            </option>
          </select>
        </div>
      </div>

      <div
        v-if="groupedTools.length"
          class="mt-5 space-y-7"
      >
        <section
          v-for="group in groupedTools"
          :key="group.category"
        >
          <div class="mb-3 flex items-center justify-between gap-4">
            <h2 class="text-xl font-semibold text-slate-950 dark:text-white">
              {{ group.label }}
            </h2>
            <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {{ group.tools.length }}
            </span>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <article
              v-for="tool in group.tools"
              :key="tool.id"
              data-testid="tool-card"
            class="group flex min-h-[184px] cursor-pointer flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/60 transition hover:-translate-y-0.5 hover:border-red-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none dark:hover:border-red-300/30"
              @click="openTool(tool)"
            >
              <div class="flex items-start justify-between gap-3">
                <span
                  :class="[
                    'flex h-10 w-10 items-center justify-center rounded-md ring-1 ring-inset',
                    getAccentClass(tool),
                  ]"
                >
                  <component :is="tool.icon" class="h-5 w-5" />
                </span>
                <ProBadge
                  v-if="tool.flag.requires_pro || tool.requiresPro"
                  compact
                  tone="soft"
                />
              </div>

              <h3 class="mt-3 text-base font-semibold text-slate-950 dark:text-white">
                {{ t(tool.titleKey) }}
              </h3>
              <p class="mt-2 line-clamp-2 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t(tool.descriptionKey) }}
              </p>

              <div
                v-if="toolBadges(tool).length"
                class="mt-3 flex flex-wrap gap-1.5"
              >
                <span
                  v-for="badge in toolBadges(tool)"
                  :key="badge.label"
                  :class="[
                    'inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset',
                    badge.tone,
                  ]"
                >
                  {{ badge.label }}
                </span>
              </div>

              <div class="mt-3 rounded-md border px-3 py-2 text-xs leading-5" :class="toneClass(releaseSummary(tool).access.tone)">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="font-semibold">{{ releaseSummary(tool).access.label }}</span>
                  <span class="text-[11px] opacity-80">{{ releaseSummary(tool).quota }}</span>
                </div>
                <p
                  v-if="!tool.flag.enabled || scanFirstToolIds.has(tool.id)"
                  class="mt-1"
                >
                  {{ !tool.flag.enabled ? releaseSummary(tool).access.detail : copy.scanFirst }}
                </p>
              </div>

              <div class="mt-4 flex items-center justify-between border-t border-slate-200 pt-3 dark:border-slate-800">
                <span
                  :class="[
                    'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset',
                    modeClassMap[tool.mode],
                  ]"
                >
                  {{ copy.modes[tool.mode] }}
                </span>
                <span class="inline-flex items-center gap-1 text-sm font-semibold text-red-600 opacity-0 transition group-hover:opacity-100 dark:text-red-300">
                  {{ copy.openTool }}
                  <ArrowRight class="h-4 w-4" />
                </span>
              </div>
            </article>
          </div>
        </section>
      </div>

      <div
        v-else
        class="mt-6 rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <Search class="mx-auto h-8 w-8 text-slate-400" />
        <h2 class="mt-4 text-lg font-semibold text-slate-950 dark:text-white">
          {{ copy.noResults }}
        </h2>
        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {{ copy.noResultsHint }}
        </p>
      </div>
    </section>

    <section class="mx-auto grid max-w-7xl gap-3 px-4 pb-10 sm:px-6 lg:grid-cols-3 lg:px-8">
      <article class="pf-panel p-5">
        <ShieldCheck class="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
        <h3 class="mt-4 font-semibold text-slate-950 dark:text-white">
          {{ copy.modes.local }}
        </h3>
        <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ copy.localDescription }}
        </p>
      </article>
      <article class="pf-panel p-5">
        <Cloud class="h-5 w-5 text-sky-600 dark:text-sky-300" />
        <h3 class="mt-4 font-semibold text-slate-950 dark:text-white">
          {{ copy.modes.cloud }}
        </h3>
        <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ copy.cloudDescription }}
        </p>
      </article>
      <article class="pf-panel p-5">
        <Sparkles class="h-5 w-5 text-violet-600 dark:text-violet-300" />
        <h3 class="mt-4 font-semibold text-slate-950 dark:text-white">
          {{ copy.modes.ai }}
        </h3>
        <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ copy.aiDescription }}
        </p>
      </article>
    </section>
  </main>
</template>
