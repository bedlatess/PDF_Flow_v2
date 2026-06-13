import { localeRegistry } from '../../src/locales/registry'

const mergeTitlesByLocale = {
  zh: '合并 PDF',
  en: 'Merge PDF',
  es: 'Unir PDF',
} as const

export const localeRouteFixtures = localeRegistry.map((locale) => ({
  ...locale,
  mergeTitle: mergeTitlesByLocale[locale.id],
}))

export const expectedLocaleRoutePattern = localeRouteFixtures
  .map((locale) => locale.routePrefix)
  .join('|')

