import type { ComposerTranslation } from 'vue-i18n'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import {
  defaultLocale,
  getLocaleConfig,
  localeRegistry,
  splitLocaleFromPath,
  withLocalePrefix,
  type SupportedLocale,
} from '@/locales/registry'

type Translate = ComposerTranslation<Record<string, unknown>, string>

const siteName = 'PDF-Flow'
const defaultDescription =
  'PDF-Flow provides everyday PDF tools, browser-first processing, and Pro document workflows.'

const ensureMeta = (selector: string, attrs: Record<string, string>) => {
  let element = document.head.querySelector<HTMLMetaElement>(selector)
  if (!element) {
    element = document.createElement('meta')
    document.head.appendChild(element)
  }

  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, value)
  }

  return element
}

const ensureLink = (selector: string, attrs: Record<string, string>) => {
  let element = document.head.querySelector<HTMLLinkElement>(selector)
  if (!element) {
    element = document.createElement('link')
    document.head.appendChild(element)
  }

  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, value)
  }

  return element
}

export const resolveCanonicalPath = (route: Pick<RouteLocationNormalizedLoaded, 'path'>) => {
  const pathWithoutLocale = splitLocaleFromPath(route.path).pathWithoutLocale
  return pathWithoutLocale === '/' ? '/' : pathWithoutLocale.replace(/\/+$/, '')
}

export const buildLocalizedUrl = (
  path: string,
  locale: SupportedLocale,
  origin = window.location.origin,
) => `${origin}${withLocalePrefix(path, locale)}`

export const updateRouteSeo = (
  route: Pick<RouteLocationNormalizedLoaded, 'path' | 'meta'>,
  locale: SupportedLocale,
  t: Translate,
) => {
  if (typeof document === 'undefined') {
    return
  }

  const titleKey = route.meta.titleKey as string | undefined
  const descriptionKey = route.meta.descriptionKey as string | undefined
  const fallbackTitle = route.meta.title as string | undefined
  const title = titleKey ? t(titleKey) : fallbackTitle
  const description = descriptionKey ? t(descriptionKey) : defaultDescription
  const documentTitle = title ? `${title} - ${siteName}` : `${siteName} - ${t('app.tagline')}`
  const canonicalPath = resolveCanonicalPath(route)
  const localeConfig = getLocaleConfig(locale)

  document.title = documentTitle
  document.documentElement.lang = localeConfig.htmlLang

  ensureMeta('meta[name="description"]', {
    name: 'description',
    content: String(description || defaultDescription),
  })
  ensureMeta('meta[property="og:title"]', {
    property: 'og:title',
    content: documentTitle,
  })
  ensureMeta('meta[property="og:description"]', {
    property: 'og:description',
    content: String(description || defaultDescription),
  })
  ensureMeta('meta[property="og:url"]', {
    property: 'og:url',
    content: buildLocalizedUrl(canonicalPath, locale),
  })
  ensureMeta('meta[property="og:locale"]', {
    property: 'og:locale',
    content: localeConfig.htmlLang.replace('-', '_'),
  })

  ensureLink('link[rel="canonical"]', {
    rel: 'canonical',
    href: buildLocalizedUrl(canonicalPath, locale),
  })

  for (const localeItem of localeRegistry) {
    ensureLink(`link[rel="alternate"][hreflang="${localeItem.hreflang}"]`, {
      rel: 'alternate',
      hreflang: localeItem.hreflang,
      href: buildLocalizedUrl(canonicalPath, localeItem.id),
    })
  }

  ensureLink('link[rel="alternate"][hreflang="x-default"]', {
    rel: 'alternate',
    hreflang: 'x-default',
    href: buildLocalizedUrl(canonicalPath, defaultLocale),
  })
}
