<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight,
  FileStack,
  LifeBuoy,
  Mail,
  ShieldCheck,
} from 'lucide-vue-next'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { useLocalePath } from '@/composables/useLocalePath'
import { featuredFooterTools, pdfTools } from '@/data/pdfTools'

const { t } = useI18n()
const siteConfigStore = useSiteConfigStore()
const { localePath } = useLocalePath()
const currentYear = new Date().getFullYear()

const brandName = computed(() => siteConfigStore.getSettingValue('site_name', t('app.title')))
const supportEmail = computed(() => siteConfigStore.getSettingValue('support_email', 'support@pdf-flow.com'))
const footerTools = computed(() =>
  featuredFooterTools
    .map((toolId) => pdfTools.find((tool) => tool.id === toolId))
    .filter((tool) => Boolean(tool))
)
const toolLinks = computed(() => [
  { label: t('nav.tools'), to: '/tools', featureKey: null },
  ...footerTools.value.map((tool) => ({
    label: t(tool.titleKey),
    to: tool.route,
    featureKey: tool.featureKey,
  })),
])

const visibleToolLinks = computed(() =>
  toolLinks.value.filter((link) =>
    link.featureKey ? siteConfigStore.getFeatureFlag(link.featureKey, link.label).enabled : true
  )
)

const productLinks = computed(() => [
  { label: t('nav.home'), to: '/' },
  { label: t('nav.features'), to: '/features' },
  { label: t('nav.pricing'), to: '/pricing' },
  { label: t('auth.login'), to: '/auth/login' },
])

const legalLinks = computed(() => [
  { label: t('footer.privacyPolicy'), to: '/privacy' },
  { label: t('footer.termsOfService'), to: '/terms' },
])

onMounted(() => {
  siteConfigStore.fetchPublicConfig()
})
</script>

<template>
  <footer class="border-t border-slate-200 bg-white text-slate-700 dark:border-slate-200 dark:bg-white dark:text-slate-700">
    <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div class="grid grid-cols-2 gap-x-5 gap-y-7 lg:grid-cols-[1.15fr_1fr_0.9fr] lg:gap-8">
        <section class="col-span-2 lg:col-span-1">
          <RouterLink
            :to="localePath('/')"
            class="flex w-fit items-center gap-3"
            aria-label="PDF-Flow home"
          >
            <span class="flex h-10 w-10 items-center justify-center rounded-md bg-red-600 text-white shadow-sm shadow-red-200 dark:shadow-none">
              <FileStack class="h-5 w-5" />
            </span>
            <span>
              <span class="block text-base font-semibold text-slate-950 dark:text-slate-950">{{ brandName }}</span>
              <span class="block text-xs font-semibold text-red-600 dark:text-red-600">
                {{ t('footer.eyebrow') }}
              </span>
            </span>
          </RouterLink>

          <p class="mt-4 max-w-md text-sm leading-7 text-slate-600 dark:text-slate-600">
            {{ t('footer.brandDescription') }}
          </p>
        </section>

        <section class="col-span-2 grid grid-cols-2 gap-5 lg:col-span-1">
          <div>
            <div class="text-sm font-semibold text-slate-950 dark:text-slate-950">
              {{ t('footer.toolsTitle') }}
            </div>
            <ul class="mt-3 space-y-1">
              <li
                v-for="link in visibleToolLinks"
                :key="link.to"
              >
                <RouterLink
                  :to="localePath(link.to)"
                  class="group flex min-h-9 items-center justify-between rounded-md px-2 text-sm font-medium text-slate-700 transition hover:bg-red-50 hover:text-red-700 dark:text-slate-700 dark:hover:bg-red-50 dark:hover:text-red-700"
                >
                  <span>{{ link.label }}</span>
                  <ArrowRight class="h-4 w-4 opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100" />
                </RouterLink>
              </li>
            </ul>
          </div>

          <div>
            <div class="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-slate-950">
              <ShieldCheck class="h-4 w-4 text-red-600 dark:text-red-600" />
              {{ t('footer.productTitle') }}
            </div>
            <ul class="mt-3 space-y-1">
              <li
                v-for="link in productLinks"
                :key="link.to"
              >
                <RouterLink
                  :to="localePath(link.to)"
                  class="group flex min-h-9 items-center justify-between rounded-md px-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-700 dark:hover:bg-slate-100 dark:hover:text-slate-950"
                >
                  <span>{{ link.label }}</span>
                  <ArrowRight class="h-4 w-4 opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100" />
                </RouterLink>
              </li>
            </ul>
          </div>
        </section>

        <section class="col-span-2 lg:col-span-1">
          <div class="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-slate-950">
            <LifeBuoy class="h-4 w-4 text-red-600 dark:text-red-600" />
            {{ t('footer.supportTitle') }}
          </div>

          <div class="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-200 dark:bg-slate-50">
            <p class="text-sm font-semibold text-slate-950 dark:text-slate-950">
              {{ t('footer.contactTitle') }}
            </p>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-600">
              {{ t('footer.contactDescription') }}
            </p>
            <a
              :href="`mailto:${supportEmail}`"
              class="mt-4 inline-flex min-h-10 items-center gap-2 rounded-md bg-red-600 px-3 text-sm font-semibold text-white transition hover:bg-red-700"
            >
              <Mail class="h-4 w-4" />
              {{ supportEmail }}
            </a>
          </div>

          <ul class="mt-4 flex flex-wrap gap-2">
            <li
              v-for="link in legalLinks"
              :key="link.to"
            >
              <RouterLink
                :to="localePath(link.to)"
                class="inline-flex min-h-9 items-center rounded-md border border-slate-200 px-3 text-sm font-medium text-slate-600 transition hover:border-red-200 hover:text-red-700 dark:border-slate-200 dark:text-slate-600 dark:hover:border-red-200 dark:hover:text-red-700"
              >
                {{ link.label }}
              </RouterLink>
            </li>
          </ul>
        </section>
      </div>

      <div class="mt-7 flex flex-col gap-2 border-t border-slate-200 pt-5 text-xs leading-6 text-slate-500 dark:border-slate-200 dark:text-slate-500 sm:mt-10 sm:flex-row sm:items-center sm:justify-between">
        <p>&copy; {{ currentYear }} {{ brandName }}. {{ t('footer.copyright') }}</p>
        <p>{{ t('footer.bottomLine') }}</p>
      </div>
    </div>
  </footer>
</template>
