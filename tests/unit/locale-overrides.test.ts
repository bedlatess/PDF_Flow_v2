import { describe, expect, it } from 'vitest'
import en from '@/locales/en.json'
import zh from '@/locales/zh.json'
import es from '@/locales/es.json'
import { localeOverrides, mergeLocaleMessages } from '@/locales/overrides'
import { localeMessagesById } from '../fixtures/locale-fixtures'
import { localeRouteFixtures } from '../fixtures/locale-route-fixtures'

const requiredNamespaces = [
  'nav',
  'footer',
  'history',
  'appShell',
  'feedbackWidget',
  'availability',
  'payment',
  'legal',
  'tools',
  'cloud',
  'account',
  'enterprise',
  'ai',
]

const collectObjectKeys = (value: unknown, prefix = ''): string[] => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return []

  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key
    return [path, ...collectObjectKeys(child, path)]
  })
}

describe('locale baseline messages', () => {
  it('has a baseline message file for every supported locale', () => {
    for (const locale of localeRouteFixtures) {
      expect(localeMessagesById).toHaveProperty(locale.id)
      expect(localeMessagesById[locale.id].nav).toBeTruthy()
      expect(localeMessagesById[locale.id].tools).toBeTruthy()
    }
  })

  it('keeps every supported locale aligned with the English baseline keys', () => {
    const englishKeys = collectObjectKeys(en)

    for (const locale of localeRouteFixtures) {
      const localeKeys = new Set(collectObjectKeys(localeMessagesById[locale.id]))
      const missingKeys = englishKeys.filter((key) => !localeKeys.has(key))

      expect(missingKeys, `${locale.id} is missing locale keys`).toEqual([])
    }
  })

  it('keeps migrated public copy in baseline locale JSON files', () => {
    for (const messages of [en, zh, es]) {
      for (const namespace of requiredNamespaces) {
        expect(messages).toHaveProperty(namespace)
      }
    }

    expect(zh.footer.brandDescription).toContain('PDF 工具')
    expect(zh.home.toolsTitle).toBe('常用 PDF 工具')
    expect(es.nav.features).toBe('Funciones')
    expect(en.history.panel.itemMeta).toBe('{tool} · {time}')
  })

  it('keeps localeOverrides as a small compatibility layer', () => {
    expect(localeOverrides).toEqual({
      en: {},
      zh: {},
      es: {},
    })
  })

  it('preserves deep merge behavior for future targeted overrides', () => {
    const merged = mergeLocaleMessages(
      {
        nav: {
          home: 'Home',
          tools: 'Tools',
        },
      },
      {
        nav: {
          tools: 'PDF tools',
        },
      },
    )

    expect(merged).toEqual({
      nav: {
        home: 'Home',
        tools: 'PDF tools',
      },
    })
  })
})
