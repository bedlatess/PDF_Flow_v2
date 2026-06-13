<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ArrowRight, Crown, Search, ShieldCheck, Sparkles } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import ProBadge from '@/components/common/ProBadge.vue'
import { pdfTools, toolCategories, type PdfToolMeta, type ToolCategory } from '@/data/pdfTools'
import { useSiteConfigStore } from '@/stores/siteConfig'

interface FeaturesPageCopy {
  eyebrow: string
  title: string
  description: string
  start: string
  pricing: string
  freeLabel: string
  proLabel: string
  freeCountLabel: string
  proCountLabel: string
  freeTitle: string
  freeDesc: string
  proTitle: string
  proDesc: string
  allToolsTitle: string
  allToolsDesc: string
  categories: Record<ToolCategory, string>
}

const { t, tm } = useI18n()
const router = useRouter()
const siteConfigStore = useSiteConfigStore()

const copy = computed(() => tm('features.page') as FeaturesPageCopy)

const visibleTools = computed(() =>
  pdfTools
    .map((tool) => ({
      ...tool,
      flag: siteConfigStore.getFeatureFlag(tool.featureKey, t(tool.titleKey)),
    }))
    .filter((tool) => tool.flag.enabled),
)

const freeTools = computed(() => visibleTools.value.filter((tool) => tool.mode === 'local'))
const proTools = computed(() => visibleTools.value.filter((tool) => tool.mode !== 'local'))

const groupedTools = computed(() =>
  toolCategories
    .map((category) => ({
      id: category,
      title: copy.value.categories[category],
      tools: visibleTools.value.filter((tool) => tool.category === category),
    }))
    .filter((group) => group.tools.length > 0),
)

const openTool = (tool: PdfToolMeta) => {
  router.push(tool.route)
}

onMounted(() => {
  siteConfigStore.fetchPublicConfig()
})
</script>

<template>
  <div class="min-h-screen bg-[#f6f8fb] dark:bg-slate-950">
    <section class="border-b border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900">
      <div class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div class="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-end">
          <div>
            <div class="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:border-white/10 dark:bg-slate-800 dark:text-slate-200">
              <Search class="h-4 w-4" />
              {{ copy.eyebrow }}
            </div>
            <h1 class="mt-5 max-w-4xl text-3xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-5xl">
              {{ copy.title }}
            </h1>
            <p class="mt-4 max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300">
              {{ copy.description }}
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <Button
                variant="primary"
                size="lg"
                class="rounded-md px-6"
                @click="router.push('/tools')"
              >
                {{ copy.start }}
              </Button>
              <Button
                variant="outline"
                size="lg"
                class="rounded-md px-6"
                @click="router.push('/pricing')"
              >
                {{ copy.pricing }}
              </Button>
            </div>
          </div>

          <aside class="grid gap-3">
            <div class="rounded-lg border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-400/20 dark:bg-emerald-500/10">
              <div class="flex items-center gap-3">
                <div class="flex h-11 w-11 items-center justify-center rounded-md bg-white text-emerald-700 shadow-sm dark:bg-slate-900 dark:text-emerald-300">
                  <ShieldCheck class="h-5 w-5" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                    {{ copy.freeTitle }}
                  </p>
                  <p class="mt-1 text-sm text-emerald-800/75 dark:text-emerald-100/75">
                    {{ freeTools.length }} {{ copy.freeCountLabel }}
                  </p>
                </div>
              </div>
            </div>

            <div class="rounded-lg border border-amber-200 bg-amber-50 p-5 dark:border-amber-300/20 dark:bg-amber-500/10">
              <div class="flex items-center gap-3">
                <div class="flex h-11 w-11 items-center justify-center rounded-md bg-white text-amber-700 shadow-sm dark:bg-slate-900 dark:text-amber-200">
                  <Crown class="h-5 w-5" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <p class="text-sm font-semibold text-amber-900 dark:text-amber-100">
                      {{ copy.proTitle }}
                    </p>
                    <ProBadge
                      compact
                      tone="ivory"
                    />
                  </div>
                  <p class="mt-1 text-sm text-amber-900/75 dark:text-amber-100/75">
                    {{ proTools.length }} {{ copy.proCountLabel }}
                  </p>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.72fr)]">
        <div class="min-w-0 rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                {{ copy.freeLabel }}
              </p>
              <h2 class="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">
                {{ copy.freeTitle }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ copy.freeDesc }}
              </p>
            </div>
            <ShieldCheck class="h-6 w-6 text-emerald-600" />
          </div>

          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <button
              v-for="tool in freeTools"
              :key="tool.id"
              class="group flex min-h-[88px] min-w-0 items-center gap-3 rounded-md border border-slate-200 bg-slate-50/70 p-4 text-left transition hover:border-emerald-300 hover:bg-white dark:border-slate-800 dark:bg-slate-950/45 dark:hover:border-emerald-400/40"
              @click="openTool(tool)"
            >
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-white text-slate-700 shadow-sm dark:bg-slate-900 dark:text-slate-200">
                <component
                  :is="tool.icon"
                  class="h-5 w-5"
                />
              </div>
              <span class="min-w-0 flex-1">
                <span class="block font-semibold text-slate-950 dark:text-white">{{ t(tool.titleKey) }}</span>
                <span class="mt-1 block truncate text-sm text-slate-500 dark:text-slate-400">{{ t(tool.descriptionKey) }}</span>
              </span>
              <ArrowRight class="h-4 w-4 shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-emerald-600" />
            </button>
          </div>
        </div>

        <div class="min-w-0 rounded-lg border border-amber-200 bg-amber-50/80 p-5 shadow-sm dark:border-amber-300/20 dark:bg-amber-500/10">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm font-semibold text-amber-700 dark:text-amber-300">
                {{ copy.proLabel }}
              </p>
              <h2 class="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">
                {{ copy.proTitle }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
                {{ copy.proDesc }}
              </p>
            </div>
            <Sparkles class="h-6 w-6 text-amber-600" />
          </div>

          <div class="mt-5 grid gap-3">
            <button
              v-for="tool in proTools"
              :key="tool.id"
              class="group flex min-h-[86px] min-w-0 items-center gap-3 rounded-md border border-amber-200 bg-white p-4 text-left transition hover:border-amber-300 hover:shadow-sm dark:border-amber-300/20 dark:bg-slate-900"
              @click="openTool(tool)"
            >
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-200">
                <component
                  :is="tool.icon"
                  class="h-5 w-5"
                />
              </div>
              <span class="min-w-0 flex-1">
                <span class="flex min-w-0 items-center gap-2">
                  <span class="truncate font-semibold text-slate-950 dark:text-white">{{ t(tool.titleKey) }}</span>
                  <ProBadge
                    v-if="tool.requiresPro"
                    compact
                    tone="ivory"
                  />
                </span>
                <span class="mt-1 block truncate text-sm text-slate-500 dark:text-slate-400">{{ t(tool.descriptionKey) }}</span>
              </span>
              <ArrowRight class="h-4 w-4 shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-amber-600" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
      <div class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-500 dark:text-slate-400">
              {{ copy.eyebrow }}
            </p>
            <h2 class="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">
              {{ copy.allToolsTitle }}
            </h2>
          </div>
          <p class="max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            {{ copy.allToolsDesc }}
          </p>
        </div>

        <div class="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <section
            v-for="group in groupedTools"
            :key="group.id"
            class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <h3 class="font-semibold text-slate-950 dark:text-white">
              {{ group.title }}
            </h3>
            <div class="mt-3 space-y-2">
              <button
                v-for="tool in group.tools"
                :key="tool.id"
                class="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm text-slate-600 transition hover:bg-white hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
                @click="openTool(tool)"
              >
                <component
                  :is="tool.icon"
                  class="h-4 w-4 shrink-0"
                />
                <span class="truncate">{{ t(tool.titleKey) }}</span>
              </button>
            </div>
          </section>
        </div>
      </div>
    </section>
  </div>
</template>
