<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { CheckCircle2, Download, SlidersHorizontal } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ToolHeader from '@/components/tools/ToolHeader.vue'
import { useSiteConfigStore } from '@/stores/siteConfig'

type Accent = 'red' | 'blue' | 'amber' | 'cyan' | 'emerald' | 'pink' | 'purple' | 'slate'
type Width = 'md' | 'lg' | 'xl'

withDefaults(defineProps<{
  title: string
  subtitle: string
  badge: string
  accent?: Accent
  pro?: boolean
  width?: Width
}>(), {
  accent: 'red',
  pro: false,
  width: 'lg',
})

const widthClasses: Record<Width, string> = {
  md: 'max-w-5xl',
  lg: 'max-w-6xl',
  xl: 'max-w-7xl',
}

const route = useRoute()
const router = useRouter()
const siteConfigStore = useSiteConfigStore()
const { locale } = useI18n()

const guideItems = computed(() => {
  const language = locale.value.split('-')[0]
  const copy = language === 'zh'
    ? [
        ['\u6dfb\u52a0\u6587\u4ef6', '\u9009\u62e9\u6587\u4ef6\u540e\uff0c\u9875\u9762\u4f1a\u663e\u793a\u4e0b\u4e00\u6b65\u53ef\u64cd\u4f5c\u5185\u5bb9\u3002'],
        ['\u8c03\u6574\u8bbe\u7f6e', '\u6309\u5f53\u524d\u4efb\u52a1\u68c0\u67e5\u987a\u5e8f\u3001\u8303\u56f4\u3001\u683c\u5f0f\u6216\u5bc6\u7801\u7b49\u9009\u9879\u3002'],
        ['\u4fdd\u5b58\u7ed3\u679c', '\u5b8c\u6210\u540e\u4e0b\u8f7d\u65b0\u6587\u4ef6\uff0c\u539f\u6587\u4ef6\u4e0d\u4f1a\u88ab\u66ff\u6362\u3002'],
      ]
    : language === 'es'
      ? [
          ['Agrega archivos', 'Despues de elegir archivos, veras las siguientes acciones disponibles.'],
          ['Ajusta opciones', 'Revisa orden, rango, formato o contrasena segun la tarea.'],
          ['Guarda el resultado', 'Descarga el nuevo archivo cuando termine. El original no se reemplaza.'],
        ]
      : [
          ['Add files', 'After choosing files, the next available actions appear here.'],
          ['Adjust options', 'Review order, ranges, format, or password settings for the task.'],
          ['Save result', 'Download the new file when it is ready. The original is not replaced.'],
        ]

  return [
    { icon: CheckCircle2, title: copy[0][0], text: copy[0][1] },
    { icon: SlidersHorizontal, title: copy[1][0], text: copy[1][1] },
    { icon: Download, title: copy[2][0], text: copy[2][1] },
  ]
})

const enforceFeatureAvailability = async () => {
  const featureKey = route.meta.featureKey as string | undefined
  if (!featureKey) return

  await siteConfigStore.fetchPublicConfig(true)
  const flag = siteConfigStore.getFeatureFlag(featureKey, String(route.meta.titleKey || featureKey))
  if (flag.enabled) return

  router.replace({
    path: '/availability/feature-disabled',
    query: {
      state: 'feature-disabled',
      feature: featureKey,
      message: flag.maintenance_message || 'feature_unavailable',
      returnTo: route.fullPath,
    },
  })
}

onMounted(enforceFeatureAvailability)
watch(() => route.fullPath, enforceFeatureAvailability)
</script>

<template>
  <div class="bg-[#f7f8fb] text-slate-950 dark:bg-[#f7f8fb] dark:text-slate-950">
    <ToolHeader
      :title="title"
      :subtitle="subtitle"
      :badge="badge"
      :accent="accent"
      :pro="pro"
    >
      <template #badgeIcon>
        <slot name="badgeIcon" />
      </template>
      <template #extra>
        <slot name="headerExtra" />
      </template>
    </ToolHeader>

    <section :class="['mx-auto px-4 pb-12 pt-5 sm:px-6 lg:px-8', widthClasses[width]]">
      <slot />

      <div class="mt-5 grid gap-3 md:grid-cols-3">
        <div
          v-for="item in guideItems"
          :key="item.title"
          class="flex min-h-24 items-start gap-3 rounded-lg border border-slate-200 bg-white px-4 py-4 shadow-sm"
        >
          <span class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700">
            <component
              :is="item.icon"
              class="h-5 w-5"
              aria-hidden="true"
            />
          </span>
          <span class="min-w-0">
            <span class="block text-sm font-semibold text-slate-950">
              {{ item.title }}
            </span>
            <span class="mt-1 block text-sm leading-6 text-slate-500">
              {{ item.text }}
            </span>
          </span>
        </div>
      </div>
    </section>
  </div>
</template>
