<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const currentLocale = computed(() => settingsStore.locale)

onMounted(() => {
  settingsStore.initTheme()
  settingsStore.initLocale()
})
</script>

<template>
  <div
    id="app"
    class="flex min-h-screen flex-col"
    :data-locale="currentLocale"
  >
    <Header :key="`header-${currentLocale}`" />
    <main class="flex-1">
      <RouterView v-slot="{ Component, route }">
        <component
          :is="Component"
          :key="`${route.fullPath}:${currentLocale}`"
        />
      </RouterView>
    </main>
    <Footer :key="`footer-${currentLocale}`" />
  </div>
</template>
