import { beforeEach, describe, expect, it } from 'vitest'
import { resolveCanonicalPath, updateRouteSeo } from '@/utils/seo'

const t = (key: string) => {
  const messages: Record<string, string> = {
    'nav.tools': 'Tools',
    'tools.merge.desc': 'Combine PDF files',
    'app.tagline': 'PDF tools and Pro workflows',
  }
  return messages[key] ?? key
}

describe('route SEO helpers', () => {
  beforeEach(() => {
    document.head.innerHTML = ''
    document.title = ''
    window.history.replaceState({}, '', '/zh-cn/tools/merge')
  })

  it('uses locale-free paths as canonical route identity', () => {
    expect(resolveCanonicalPath({ path: '/zh-cn/tools/merge' })).toBe('/tools/merge')
    expect(resolveCanonicalPath({ path: '/en/' })).toBe('/')
  })

  it('updates title, description, canonical, and hreflang links', () => {
    updateRouteSeo(
      {
        path: '/zh-cn/tools/merge',
        meta: {
          titleKey: 'nav.tools',
          descriptionKey: 'tools.merge.desc',
        },
      },
      'zh',
      t,
    )

    expect(document.title).toBe('Tools - PDF-Flow')
    expect(document.documentElement.lang).toBe('zh-CN')
    expect(document.querySelector('meta[name="description"]')?.getAttribute('content')).toBe(
      'Combine PDF files',
    )
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe(
      'http://localhost:3000/zh-cn/tools/merge',
    )
    expect(document.querySelector('link[rel="alternate"][hreflang="en"]')?.getAttribute('href')).toBe(
      'http://localhost:3000/en/tools/merge',
    )
    expect(
      document.querySelector('link[rel="alternate"][hreflang="x-default"]')?.getAttribute('href'),
    ).toBe('http://localhost:3000/zh-cn/tools/merge')
  })
})
