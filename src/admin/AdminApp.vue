<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

onMounted(() => {
  settingsStore.setTheme('light')
  document.documentElement.lang = 'zh-CN'
  document.documentElement.classList.add('pdf-flow-admin')
})
</script>

<template>
  <div id="admin-app" class="min-h-screen bg-slate-50 text-slate-950">
    <RouterView />
  </div>
</template>
