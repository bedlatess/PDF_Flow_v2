import { describe, expect, it } from 'vitest'
import {
  getBrowserLocale,
  getLocaleByRoutePrefix,
  localeRoutePattern,
  normalizeLocale,
  splitLocaleFromPath,
  withLocalePrefix,
} from '@/locales/registry'
import { expectedLocaleRoutePattern, localeRouteFixtures } from '../fixtures/locale-route-fixtures'

describe('locale registry', () => {
  it('normalizes locale aliases used by browsers and URLs', () => {
    expect(normalizeLocale('zh-CN')).toBe('zh')
    expect(normalizeLocale('en-US')).toBe('en')
    expect(normalizeLocale('es-MX')).toBe('es')
    expect(normalizeLocale('ja')).toBeNull()
  })

  it('maps public route prefixes to internal locale ids', () => {
    for (const locale of localeRouteFixtures) {
      expect(getLocaleByRoutePrefix(locale.routePrefix)).toBe(locale.id)
    }

    expect(getLocaleByRoutePrefix('zh')).toBeNull()
    expect(localeRoutePattern).toBe(expectedLocaleRoutePattern)
  })

  it('splits and rewrites locale-prefixed paths', () => {
    expect(splitLocaleFromPath('/zh-cn/tools/merge')).toMatchObject({
      locale: 'zh',
      pathWithoutLocale: '/tools/merge',
      hasLocalePrefix: true,
    })

    expect(splitLocaleFromPath('/tools/merge')).toMatchObject({
      locale: null,
      pathWithoutLocale: '/tools/merge',
      hasLocalePrefix: false,
    })

    expect(withLocalePrefix('/tools/merge', 'en')).toBe('/en/tools/merge')
    expect(withLocalePrefix('/zh-cn/tools/merge', 'es')).toBe('/es/tools/merge')
    expect(withLocalePrefix('/', 'zh')).toBe('/zh-cn')
  })

  it('resolves browser language preferences from navigator languages', () => {
    const descriptor = Object.getOwnPropertyDescriptor(window.navigator, 'languages')
    Object.defineProperty(window.navigator, 'languages', {
      configurable: true,
      value: ['fr-FR', 'es-MX', 'en-US'],
    })

    expect(getBrowserLocale()).toBe('es')

    if (descriptor) {
      Object.defineProperty(window.navigator, 'languages', descriptor)
    }
  })
})
