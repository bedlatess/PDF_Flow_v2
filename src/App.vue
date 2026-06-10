<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { useSettingsStore } from '@/stores/settings'
import { useSiteConfigStore } from '@/stores/siteConfig'

const settingsStore = useSettingsStore()
const siteConfigStore = useSiteConfigStore()
const route = useRoute()
const currentLocale = computed(() => settingsStore.locale)
const maintenanceMessage = computed(() =>
  siteConfigStore.globalAnnouncement || '站点正在维护中，请稍后再试。'
)
const maintenanceBypassPrefixes = ['/auth', '/control-room', '/privacy', '/terms']
const shouldShowMaintenance = computed(() =>
  siteConfigStore.maintenanceMode &&
  !maintenanceBypassPrefixes.some((prefix) => route.path.startsWith(prefix))
)

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
    <Header :key="`header-${currentLocale}`" />
    <section
      v-if="siteConfigStore.globalAnnouncement"
      class="border-b border-amber-200/80 bg-[linear-gradient(90deg,#fffbeb_0%,#fff7ed_50%,#fef3c7_100%)] px-4 py-3 text-sm text-amber-900 shadow-sm dark:border-amber-500/20 dark:bg-[linear-gradient(90deg,rgba(120,53,15,0.35),rgba(127,29,29,0.22))] dark:text-amber-100"
    >
      <div class="mx-auto flex max-w-7xl flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <p class="font-semibold">站点公告</p>
        <p class="leading-6 sm:text-right">{{ siteConfigStore.globalAnnouncement }}</p>
      </div>
    </section>
    <main class="flex-1">
      <div
        v-if="shouldShowMaintenance"
        class="mx-auto flex min-h-[56vh] max-w-4xl items-center px-4 py-16"
      >
        <div class="w-full rounded-[34px] border border-amber-200/80 bg-white/90 p-8 text-center shadow-2xl shadow-amber-100/60 backdrop-blur dark:border-amber-500/20 dark:bg-slate-900/82 dark:shadow-none sm:p-10">
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700 dark:text-amber-300">
            Maintenance
          </p>
          <h1 class="mt-4 text-3xl font-semibold text-slate-950 dark:text-white">
            站点正在维护中
          </h1>
          <p class="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ maintenanceMessage }}
          </p>
          <p class="mt-6 text-xs text-slate-500 dark:text-slate-400">
            管理员仍可通过登录后访问控制台调整维护状态。
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
    <Footer :key="`footer-${currentLocale}`" />
  </div>
</template>
