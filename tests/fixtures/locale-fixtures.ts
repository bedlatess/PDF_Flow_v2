import en from '../../src/locales/en.json'
import zh from '../../src/locales/zh.json'
import es from '../../src/locales/es.json'
import { type SupportedLocale } from '../../src/locales/registry'

type LocaleMessages = typeof en

export const localeMessagesById = {
  en,
  zh,
  es,
} satisfies Record<SupportedLocale, LocaleMessages>
