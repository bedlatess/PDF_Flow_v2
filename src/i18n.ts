import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'
import es from './locales/es.json'
import { localeOverrides, mergeLocaleMessages } from './locales/overrides'

const supportedLocales = ['en', 'zh', 'es'] as const
type SupportedLocale = typeof supportedLocales[number]
const localeStorageKey = 'pdf-flow-locale'

const resolveInitialLocale = (): SupportedLocale => {
  if (typeof window === 'undefined') {
    return 'zh'
  }

  const storedLocale = window.localStorage.getItem(localeStorageKey)
  if (storedLocale && supportedLocales.includes(storedLocale as SupportedLocale)) {
    return storedLocale as SupportedLocale
  }

  return 'zh'
}

const initialLocale = resolveInitialLocale()

const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'zh',
  messages: {
    en: mergeLocaleMessages(en, localeOverrides.en),
    zh: mergeLocaleMessages(zh, localeOverrides.zh),
    es: mergeLocaleMessages(es, localeOverrides.es),
  },
})

export const defaultLocale = initialLocale
export default i18n
