import { describe, expect, it } from 'vitest'
import en from '@/locales/en.json'
import zh from '@/locales/zh.json'
import es from '@/locales/es.json'
import { localeOverrides, mergeLocaleMessages } from '@/locales/overrides'

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

describe('locale baseline messages', () => {
  it('keeps migrated public copy in baseline locale JSON files', () => {
    for (const messages of [en, zh, es]) {
      for (const namespace of requiredNamespaces) {
        expect(messages).toHaveProperty(namespace)
      }
    }

    expect(zh.footer.brandDescription).toContain('PDF 工具')
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
