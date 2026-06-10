import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { siteConfigAPI, type PublicFeatureFlag, type PublicSiteConfig } from '@/services/api'

type PublicContentBlock = PublicSiteConfig['content_blocks'][string]

const defaultFlag = (label: string): PublicFeatureFlag => ({
  label,
  description: null,
  enabled: true,
  requires_login: false,
  requires_pro: false,
  maintenance_message: null,
})

export const useSiteConfigStore = defineStore('site-config', () => {
  const config = ref<PublicSiteConfig | null>(null)
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref<string | null>(null)

  const featureFlags = computed(() => config.value?.feature_flags ?? {})
  const settings = computed(() => config.value?.settings ?? {})
  const contentBlocks = computed(() => config.value?.content_blocks ?? {})

  const fetchPublicConfig = async (force = false) => {
    if (loading.value) return config.value
    if (loaded.value && !force) return config.value

    loading.value = true
    error.value = null

    try {
      config.value = await siteConfigAPI.getPublicConfig()
      loaded.value = true
      return config.value
    } catch {
      error.value = '无法读取站点配置，已使用默认可用状态。'
      loaded.value = false
      return config.value
    } finally {
      loading.value = false
    }
  }

  const getFeatureFlag = (key: string, fallbackLabel = key) =>
    featureFlags.value[key] ?? defaultFlag(fallbackLabel)

  const isFeatureEnabled = (key: string) => getFeatureFlag(key).enabled

  const getSettingValue = (key: string, fallback = '') =>
    settings.value[key]?.value || fallback

  const resolveLocale = (locale: string) => {
    if (locale.startsWith('zh')) return 'zh'
    return 'en'
  }

  const getContentBlock = (
    key: string,
    locale: string,
    fallback?: PublicContentBlock
  ) => {
    const normalizedLocale = resolveLocale(locale)
    return (
      contentBlocks.value[`${key}:${normalizedLocale}`] ||
      contentBlocks.value[`${key}:zh`] ||
      contentBlocks.value[`${key}:en`] ||
      fallback ||
      null
    )
  }

  return {
    config,
    loading,
    loaded,
    error,
    featureFlags,
    settings,
    contentBlocks,
    fetchPublicConfig,
    getFeatureFlag,
    isFeatureEnabled,
    getSettingValue,
    getContentBlock,
  }
})
