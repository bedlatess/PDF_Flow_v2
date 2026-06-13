import { useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import {
  getLocaleByRoutePrefix,
  resolvePreferredLocale,
  withLocalePrefix,
  type SupportedLocale,
} from '@/locales/registry'

export const useLocalePath = () => {
  const route = useRoute()
  const settingsStore = useSettingsStore()

  const currentLocale = (): SupportedLocale => {
    const localeParam = route.params.locale
    const prefix = Array.isArray(localeParam) ? localeParam[0] : localeParam
    return (
      (typeof prefix === 'string' && getLocaleByRoutePrefix(prefix)) ||
      settingsStore.locale ||
      resolvePreferredLocale()
    )
  }

  const localePath = (path: string, locale = currentLocale()) =>
    withLocalePrefix(path, locale)

  return {
    currentLocale,
    localePath,
  }
}
