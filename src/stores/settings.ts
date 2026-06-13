import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'
import {
  getLocaleConfig,
  persistLocale,
  resolvePreferredLocale,
  type SupportedLocale,
} from '@/locales/registry'

const themeStorageKey = 'pdf-flow-theme'

export const useSettingsStore = defineStore('settings', () => {
  const locale = ref<SupportedLocale>(resolvePreferredLocale())
  const theme = ref<'light' | 'dark'>('light')

  const setLocale = (newLocale: typeof locale.value) => {
    locale.value = newLocale
    if (i18n.global.locale.value !== newLocale) {
      i18n.global.locale.value = newLocale
    }
    persistLocale(newLocale)
    document.documentElement.lang = getLocaleConfig(newLocale).htmlLang
  }

  const setTheme = (newTheme: typeof theme.value) => {
    theme.value = newTheme
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(themeStorageKey, newTheme)
    }
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const initTheme = () => {
    setTheme('light')
  }

  const initLocale = () => {
    if (i18n.global.locale.value !== locale.value) {
      i18n.global.locale.value = locale.value
    }
    document.documentElement.lang = getLocaleConfig(locale.value).htmlLang
  }

  return {
    locale,
    theme,
    setLocale,
    setTheme,
    initTheme,
    initLocale,
  }
})
