<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  BadgeCheck,
  Cloud,
  FileStack,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-vue-next'
import ProBadge from '@/components/common/ProBadge.vue'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { pdfTools, toolCategories, type PdfToolMeta, type ToolCategory, type ToolMode } from '@/data/pdfTools'

type HomeWorkspaceCopy = {
  eyebrow: string
  title: string
  description: string
  primaryAction: string
  secondaryAction: string
  searchPlaceholder: string
  quickTitle: string
  allTools: string
  noResults: string
  noResultsHint: string
  advancedTitle: string
  advancedDescription: string
  featuredTitle: string
  toolsTitle: string
  stats: [string, string][]
  trust: [string, string][]
  categories: Record<ToolCategory, string>
  modeLabels: Record<ToolMode, string>
}

const { t, tm } = useI18n()
const router = useRouter()
const siteConfigStore = useSiteConfigStore()

const searchQuery = ref('')
const activeCategory = ref<ToolCategory | 'all'>('all')

const workspaceCopy = computed(() => tm('home.workspace') as HomeWorkspaceCopy)

const enabledTools = computed(() =>
  pdfTools
    .map((tool) => ({
      ...tool,
      flag: siteConfigStore.getFeatureFlag(tool.featureKey, t(tool.titleKey)),
    }))
    .filter((tool) => tool.flag.enabled)
)

const normalizedSearch = computed(() => searchQuery.value.trim().toLowerCase())

const filteredTools = computed(() =>
  enabledTools.value.filter((tool) => {
    if (activeCategory.value !== 'all' && tool.category !== activeCategory.value) {
      return false
    }

    if (!normalizedSearch.value) {
      return true
    }

    return [
      tool.id,
      t(tool.titleKey),
      t(tool.descriptionKey),
      workspaceCopy.value.categories[tool.category],
      workspaceCopy.value.modeLabels[tool.mode],
    ].join(' ').toLowerCase().includes(normalizedSearch.value)
  })
)

const featuredTools = computed(() => enabledTools.value.filter((tool) => tool.featured).slice(0, 6))
const advancedTools = computed(() => enabledTools.value.filter((tool) => tool.mode !== 'local').slice(0, 4))

const categoryOptions = computed(() => [
  { id: 'all' as const, label: workspaceCopy.value.allTools },
  ...toolCategories.map((category) => ({
    id: category,
    label: workspaceCopy.value.categories[category],
  })),
])

const modeClassMap: Record<ToolMode, string> = {
  local: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-200 dark:ring-emerald-300/20',
  cloud: 'bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-200 dark:ring-sky-300/20',
  ai: 'bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-500/10 dark:text-violet-200 dark:ring-violet-300/20',
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

const getAccentClass = (tool: PdfToolMeta) => accentClassMap[tool.accent] || accentClassMap.slate

const navigateToTool = (tool: PdfToolMeta) => {
  router.push(tool.route)
}

onMounted(() => {
  siteConfigStore.fetchPublicConfig(true)
})
</script>

<template>
  <div class="min-h-screen bg-[#f6f8fb] text-slate-950 dark:bg-slate-950 dark:text-white">
    <section class="border-b border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900">
      <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div class="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(360px,0.7fr)] lg:items-end">
          <div>
            <div class="inline-flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 dark:border-red-400/20 dark:bg-red-500/10 dark:text-red-200">
              <FileStack class="h-4 w-4" />
              {{ workspaceCopy.eyebrow }}
            </div>
            <h1 class="mt-5 max-w-3xl text-3xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-5xl">
              {{ workspaceCopy.title }}
            </h1>
            <p class="mt-4 max-w-3xl text-base leading-7 text-slate-600 dark:text-slate-300">
              {{ workspaceCopy.description }}
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                class="inline-flex min-h-11 items-center gap-2 rounded-md bg-red-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-slate-950"
                @click="router.push('/tools/merge')"
              >
                {{ workspaceCopy.primaryAction }}
                <ArrowRight class="h-4 w-4" />
              </button>
              <button
                type="button"
                class="inline-flex min-h-11 items-center rounded-md border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-800 transition hover:border-slate-400 hover:bg-slate-50 dark:border-white/15 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
                @click="router.push('/pricing')"
              >
                {{ workspaceCopy.secondaryAction }}
              </button>
            </div>
          </div>

          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/45">
            <label class="relative block">
              <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                v-model="searchQuery"
                type="search"
                :placeholder="workspaceCopy.searchPlaceholder"
                class="h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20 dark:border-white/15 dark:bg-slate-900 dark:text-white"
              >
            </label>

            <div class="mt-4 grid gap-2 sm:grid-cols-2">
              <button
                v-for="tool in featuredTools"
                :key="tool.id"
                type="button"
                class="group flex min-h-[56px] items-center gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-left transition hover:border-red-200 hover:bg-red-50/50 dark:border-white/10 dark:bg-slate-900 dark:hover:border-red-300/30 dark:hover:bg-red-500/10"
                @click="navigateToTool(tool)"
              >
                <span :class="['flex h-9 w-9 shrink-0 items-center justify-center rounded-md ring-1 ring-inset', getAccentClass(tool)]">
                  <component :is="tool.icon" class="h-4 w-4" />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-semibold text-slate-950 dark:text-white">{{ t(tool.titleKey) }}</span>
                  <span class="mt-0.5 block truncate text-xs text-slate-500 dark:text-slate-400">{{ workspaceCopy.modeLabels[tool.mode] }}</span>
                </span>
                <ArrowRight class="h-4 w-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-red-600" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-sm font-semibold text-slate-500 dark:text-slate-400">
            {{ workspaceCopy.toolsTitle }}
          </p>
          <h2 class="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">
            {{ t('home.toolsTitle') }}
          </h2>
        </div>

        <div class="flex min-w-0 max-w-full gap-2 overflow-x-auto pb-1 md:flex-wrap md:justify-end md:overflow-visible md:pb-0">
          <button
            v-for="category in categoryOptions"
            :key="category.id"
            type="button"
            :class="[
              'h-10 shrink-0 rounded-md px-4 text-sm font-semibold transition',
              activeCategory === category.id
                ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800',
            ]"
            @click="activeCategory = category.id"
          >
            {{ category.label }}
          </button>
        </div>
      </div>

      <div
        v-if="filteredTools.length"
        class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      >
        <article
          v-for="tool in filteredTools"
          :key="tool.id"
          data-testid="tool-card"
          class="group flex min-h-[126px] cursor-pointer flex-col rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm transition hover:-translate-y-0.5 hover:border-red-200 hover:shadow-md dark:border-white/10 dark:bg-slate-900 dark:hover:border-red-300/30"
          @click="navigateToTool(tool)"
        >
          <div class="flex items-start justify-between gap-3">
            <span :class="['flex h-10 w-10 items-center justify-center rounded-md ring-1 ring-inset', getAccentClass(tool)]">
              <component :is="tool.icon" class="h-5 w-5" />
            </span>
          </div>
          <h3 class="mt-3 text-base font-semibold text-slate-950 dark:text-white">
            {{ t(tool.titleKey) }}
          </h3>
          <p class="mt-1 line-clamp-2 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ t(tool.descriptionKey) }}
          </p>
          <div class="mt-3 flex items-center justify-between">
            <span :class="['inline-flex rounded-md px-2.5 py-1 text-xs font-semibold ring-1 ring-inset', modeClassMap[tool.mode]]">
              {{ workspaceCopy.modeLabels[tool.mode] }}
            </span>
            <ArrowRight class="h-4 w-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-red-600" />
          </div>
        </article>
      </div>

      <div
        v-else
        class="mt-5 rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center dark:border-white/15 dark:bg-slate-900"
      >
        <Search class="mx-auto h-8 w-8 text-slate-400" />
        <h3 class="mt-4 text-lg font-semibold text-slate-950 dark:text-white">
          {{ workspaceCopy.noResults }}
        </h3>
        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {{ workspaceCopy.noResultsHint }}
        </p>
      </div>
    </section>

    <section class="mx-auto grid max-w-7xl min-w-0 gap-4 px-4 pb-10 sm:px-6 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:px-8">
      <div class="min-w-0 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
        <div class="grid gap-3 sm:grid-cols-3">
          <article
            v-for="[value, label] in workspaceCopy.stats"
            :key="label"
            class="rounded-md bg-slate-50 p-3 dark:bg-slate-950/55"
          >
            <p class="text-xl font-semibold text-slate-950 dark:text-white">{{ value }}</p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ label }}</p>
          </article>
        </div>
        <div class="mt-4 grid gap-3 sm:grid-cols-3">
          <article
            v-for="item in workspaceCopy.trust"
            :key="item[0]"
            class="rounded-md border border-slate-200 p-3 dark:border-white/10"
          >
            <ShieldCheck v-if="item[0] === workspaceCopy.trust[0][0]" class="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
            <Cloud v-else-if="item[0] === workspaceCopy.trust[1][0]" class="h-5 w-5 text-sky-600 dark:text-sky-300" />
            <BadgeCheck v-else class="h-5 w-5 text-slate-600 dark:text-slate-300" />
            <h3 class="mt-3 text-sm font-semibold text-slate-950 dark:text-white">{{ item[0] }}</h3>
            <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ item[1] }}</p>
          </article>
        </div>
      </div>

      <div class="min-w-0 rounded-lg border border-amber-200 bg-amber-50/70 p-5 shadow-sm dark:border-amber-300/20 dark:bg-amber-500/10">
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="flex h-10 w-10 items-center justify-center rounded-md bg-white text-amber-700 shadow-sm dark:bg-slate-900 dark:text-amber-200">
              <Sparkles class="h-5 w-5" />
            </div>
            <h2 class="mt-4 text-2xl font-semibold text-slate-950 dark:text-white">
              {{ workspaceCopy.advancedTitle }}
            </h2>
            <p class="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-200">
              {{ workspaceCopy.advancedDescription }}
            </p>
          </div>
          <ProBadge tone="ivory" />
        </div>

        <div class="mt-5 grid gap-3 sm:grid-cols-2">
          <button
            v-for="tool in advancedTools"
            :key="tool.id"
            type="button"
            class="group flex min-h-[78px] w-full min-w-0 items-center gap-3 rounded-md border border-amber-200 bg-white p-3 text-left transition hover:border-amber-300 hover:bg-amber-50 dark:border-amber-300/20 dark:bg-slate-900 dark:hover:bg-amber-500/10"
            @click="navigateToTool(tool)"
          >
            <span :class="['flex h-10 w-10 shrink-0 items-center justify-center rounded-md ring-1 ring-inset', getAccentClass(tool)]">
              <component :is="tool.icon" class="h-5 w-5" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-semibold text-slate-950 dark:text-white">{{ t(tool.titleKey) }}</span>
              <span class="mt-1 block truncate text-xs text-slate-500 dark:text-slate-400">{{ t(tool.descriptionKey) }}</span>
            </span>
            <ArrowRight class="h-4 w-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-amber-700" />
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
