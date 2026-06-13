export const localeStorageKey = 'pdf-flow-locale'

export const localeRegistry = [
  {
    id: 'zh',
    routePrefix: 'zh-cn',
    label: '简体中文',
    htmlLang: 'zh-CN',
    hreflang: 'zh-CN',
    contentLocale: 'zh',
  },
  {
    id: 'en',
    routePrefix: 'en',
    label: 'English',
    htmlLang: 'en',
    hreflang: 'en',
    contentLocale: 'en',
  },
  {
    id: 'es',
    routePrefix: 'es',
    label: 'Español',
    htmlLang: 'es',
    hreflang: 'es',
    contentLocale: 'en',
  },
] as const

export type SupportedLocale = (typeof localeRegistry)[number]['id']
export type LocaleRoutePrefix = (typeof localeRegistry)[number]['routePrefix']

export const defaultLocale: SupportedLocale = 'zh'
export const fallbackLocale: SupportedLocale = 'zh'

const localeAliases: Record<string, SupportedLocale> = {
  zh: 'zh',
  'zh-cn': 'zh',
  'zh-hans': 'zh',
  cn: 'zh',
  en: 'en',
  'en-us': 'en',
  'en-gb': 'en',
  es: 'es',
  'es-es': 'es',
  'es-mx': 'es',
}

export const supportedLocales = localeRegistry.map((locale) => locale.id) as SupportedLocale[]
export const localeRoutePrefixes = localeRegistry.map((locale) => locale.routePrefix) as LocaleRoutePrefix[]
export const localeRoutePattern = localeRoutePrefixes.join('|')

export const isSupportedLocale = (value: string): value is SupportedLocale =>
  supportedLocales.includes(value as SupportedLocale)

export const normalizeLocale = (value?: string | null): SupportedLocale | null => {
  if (!value) return null
  return localeAliases[value.trim().toLowerCase()] ?? null
}

export const getLocaleConfig = (locale: SupportedLocale) =>
  localeRegistry.find((item) => item.id === locale) ?? localeRegistry[0]

export const getLocaleByRoutePrefix = (prefix?: string | null): SupportedLocale | null => {
  if (!prefix) return null
  const normalizedPrefix = prefix.trim().toLowerCase()
  return localeRegistry.find((item) => item.routePrefix === normalizedPrefix)?.id ?? null
}

export const getRoutePrefixForLocale = (locale: SupportedLocale) =>
  getLocaleConfig(locale).routePrefix

export const getStoredLocale = (): SupportedLocale | null => {
  if (typeof window === 'undefined') return null
  return normalizeLocale(window.localStorage.getItem(localeStorageKey))
}

export const getBrowserLocale = (): SupportedLocale | null => {
  if (typeof navigator === 'undefined') return null

  const languages = navigator.languages?.length ? navigator.languages : [navigator.language]
  for (const language of languages) {
    const normalized = normalizeLocale(language)
    if (normalized) return normalized
  }

  return null
}

export const resolvePreferredLocale = (): SupportedLocale =>
  getStoredLocale() ?? getBrowserLocale() ?? defaultLocale

export const persistLocale = (locale: SupportedLocale) => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(localeStorageKey, locale)
}

export const splitLocaleFromPath = (path: string) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const parts = normalizedPath.split('/')
  const candidatePrefix = parts[1]
  const locale = getLocaleByRoutePrefix(candidatePrefix)

  if (!locale) {
    return {
      locale: null,
      pathWithoutLocale: normalizedPath,
      hasLocalePrefix: false,
    }
  }

  const rest = `/${parts.slice(2).join('/')}`.replace(/\/+$/, '') || '/'

  return {
    locale,
    pathWithoutLocale: rest,
    hasLocalePrefix: true,
  }
}

export const withLocalePrefix = (path: string, locale: SupportedLocale) => {
  const pathInfo = splitLocaleFromPath(path)
  const basePath = pathInfo.pathWithoutLocale === '/' ? '' : pathInfo.pathWithoutLocale
  return `/${getRoutePrefixForLocale(locale)}${basePath}`
}

export const resolveContentLocale = (locale: string) => {
  const normalizedLocale = normalizeLocale(locale)
  return getLocaleConfig(normalizedLocale ?? fallbackLocale).contentLocale
}
