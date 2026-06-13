<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import FeedbackWidget from '@/components/common/FeedbackWidget.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { splitLocaleFromPath } from '@/locales/registry'

const settingsStore = useSettingsStore()
const siteConfigStore = useSiteConfigStore()
const route = useRoute()
const { t } = useI18n()
const currentLocale = computed(() => settingsStore.locale)
const maintenanceMessage = computed(() =>
  siteConfigStore.globalAnnouncement || t('appShell.maintenanceMessage')
)
const maintenanceBypassPrefixes = ['/auth', '/privacy', '/terms']
const routePathWithoutLocale = computed(() => splitLocaleFromPath(route.path).pathWithoutLocale)
const shouldShowMaintenance = computed(() =>
  siteConfigStore.maintenanceMode &&
  !maintenanceBypassPrefixes.some((prefix) => routePathWithoutLocale.value.startsWith(prefix))
)
const shouldShowFeedback = computed(() =>
  !routePathWithoutLocale.value.startsWith('/auth') &&
  !shouldShowMaintenance.value
)

const retryPublicConfig = () => {
  siteConfigStore.fetchPublicConfig(true)
}

onMounted(() => {
  settingsStore.initTheme()
  settingsStore.initLocale()
  siteConfigStore.fetchPublicConfig(true)
})
</script>

<template>
  <div
    id="app"
    class="flex min-h-screen flex-col"
    :data-locale="currentLocale"
  >
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-slate-950 focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lg dark:focus:bg-sky-500"
    >
      {{ t('appShell.skipToContent') }}
    </a>
    <Header :key="`header-${currentLocale}`" />
    <section
      v-if="siteConfigStore.globalAnnouncement"
      class="border-b border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/25 dark:text-amber-100"
    >
      <div class="mx-auto flex max-w-7xl flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <p class="font-semibold">{{ t('appShell.announcement') }}</p>
        <p class="leading-6 sm:text-right">{{ siteConfigStore.globalAnnouncement }}</p>
      </div>
    </section>
    <section
      v-if="siteConfigStore.error && !shouldShowMaintenance"
      class="border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-950"
    >
      <div class="mx-auto flex max-w-7xl flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <DiagnosticAlert
          class="flex-1"
          :title="t('appShell.configUnavailableTitle')"
          :message="t('appShell.configUnavailableMessage')"
          :diagnostic-code="siteConfigStore.error.diagnosticCode"
          :support-hint="t('appShell.configUnavailableHint')"
          tone="warning"
        />
        <button
          class="inline-flex shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-200 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
          :disabled="siteConfigStore.loading"
          @click="retryPublicConfig"
        >
          {{ siteConfigStore.loading ? t('appShell.configRetrying') : t('appShell.configRetry') }}
        </button>
      </div>
    </section>
    <main
      id="main-content"
      class="flex-1"
      tabindex="-1"
    >
      <div
        v-if="shouldShowMaintenance"
        class="mx-auto flex min-h-[56vh] max-w-5xl items-center px-4 py-16"
      >
        <div class="w-full rounded-lg border border-amber-200 bg-white p-8 text-center shadow-sm dark:border-amber-900/40 dark:bg-slate-900 sm:p-10">
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700 dark:text-amber-300">
            {{ t('appShell.maintenanceBadge') }}
          </p>
          <h1 class="mt-4 text-3xl font-semibold text-slate-950 dark:text-white">
            {{ t('appShell.maintenanceTitle') }}
          </h1>
          <p class="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ maintenanceMessage }}
          </p>
          <p class="mt-6 text-xs text-slate-500 dark:text-slate-400">
            {{ t('appShell.maintenanceAdminHint') }}
          </p>
        </div>
      </div>
      <RouterView
        v-else
        v-slot="{ Component, route }"
      >
        <component
          :is="Component"
          :key="`${route.fullPath}:${currentLocale}`"
        />
      </RouterView>
    </main>
    <FeedbackWidget v-if="shouldShowFeedback" />
    <Footer :key="`footer-${currentLocale}`" />
  </div>
</template>
