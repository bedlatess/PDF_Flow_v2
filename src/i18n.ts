import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'
import es from './locales/es.json'
import { localeOverrides, mergeLocaleMessages } from './locales/overrides'
import {
  fallbackLocale,
  resolvePreferredLocale,
  type SupportedLocale,
} from './locales/registry'

const initialLocale = resolvePreferredLocale()

const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale,
  messages: {
    en: mergeLocaleMessages(en, localeOverrides.en),
    zh: mergeLocaleMessages(zh, localeOverrides.zh),
    es: mergeLocaleMessages(es, localeOverrides.es),
  },
})

export const defaultLocale = initialLocale
export type { SupportedLocale }
export default i18n
