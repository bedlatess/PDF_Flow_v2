import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  siteConfigAPI,
  type PublicFeatureFlag,
  type PublicOAuthProviderKey,
  type PublicSiteConfig,
} from '@/services/api'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { resolveContentLocale } from '@/locales/registry'

type PublicContentBlock = PublicSiteConfig['content_blocks'][string]

const defaultFlag = (label: string): PublicFeatureFlag => ({
  label,
  description: null,
  enabled: true,
  is_public: true,
  requires_login: false,
  requires_pro: false,
  maintenance_message: null,
  free_daily_limit: null,
  free_max_file_size_mb: null,
  free_batch_file_limit: null,
  pro_daily_limit: null,
  pro_max_file_size_mb: null,
  pro_batch_file_limit: null,
  pro_unlimited: false,
})

export const useSiteConfigStore = defineStore('site-config', () => {
  const config = ref<PublicSiteConfig | null>(null)
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref<FormattedUserError | null>(null)
  let pendingRequest: Promise<PublicSiteConfig | null> | null = null

  const featureFlags = computed(() => config.value?.feature_flags ?? {})
  const settings = computed(() => config.value?.settings ?? {})
  const contentBlocks = computed(() => config.value?.content_blocks ?? {})
  const oauthProviders = computed(() => config.value?.oauth_providers ?? {})
  const canRenderPublicFeatureLists = computed(() => loaded.value || Boolean(error.value))

  const fetchPublicConfig = async (force = false) => {
    if (pendingRequest) return pendingRequest
    if (loaded.value && !force) return config.value

    loading.value = true
    error.value = null

    pendingRequest = siteConfigAPI.getPublicConfig()
      .then((publicConfig) => {
        config.value = publicConfig
        loaded.value = true
        return config.value
      })
      .catch((err) => {
        error.value = formatUserFacingError(err, {
          area: 'GENERAL',
          fallbackTitle: 'Site settings could not be loaded',
          fallbackMessage: 'PDF-Flow is running with default public settings until the configuration service responds.',
        })
        loaded.value = false
        return config.value
      })
      .finally(() => {
        loading.value = false
        pendingRequest = null
      })

    return pendingRequest
  }

  const getFeatureFlag = (key: string, fallbackLabel = key) =>
    featureFlags.value[key] ?? defaultFlag(fallbackLabel)

  const isFeatureEnabled = (key: string) => getFeatureFlag(key).enabled
  const isFeaturePublic = (key: string) => getFeatureFlag(key).is_public
  const isFeatureVisible = (key: string, fallbackLabel = key) => {
    if (!canRenderPublicFeatureLists.value) return false
    const flag = getFeatureFlag(key, fallbackLabel)
    return flag.enabled && flag.is_public
  }

  const isOAuthProviderEnabled = (provider: PublicOAuthProviderKey) =>
    oauthProviders.value[provider]?.enabled === true

  const getSettingValue = (key: string, fallback = '') =>
    settings.value[key]?.value || fallback

  const getBooleanSetting = (key: string, fallback = false) => {
    const value = getSettingValue(key)
    if (!value) return fallback
    return ['1', 'true', 'yes', 'on'].includes(value.trim().toLowerCase())
  }

  const globalAnnouncement = computed(() =>
    getSettingValue('global_announcement').trim()
  )

  const maintenanceMode = computed(() =>
    getBooleanSetting('maintenance_mode', false)
  )

  const getContentBlock = (
    key: string,
    locale: string,
    fallback?: PublicContentBlock
  ) => {
    const normalizedLocale = resolveContentLocale(locale)
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
    oauthProviders,
    canRenderPublicFeatureLists,
    globalAnnouncement,
    maintenanceMode,
    fetchPublicConfig,
    getFeatureFlag,
    isFeatureEnabled,
    isFeaturePublic,
    isFeatureVisible,
    isOAuthProviderEnabled,
    getSettingValue,
    getBooleanSetting,
    getContentBlock,
  }
})
