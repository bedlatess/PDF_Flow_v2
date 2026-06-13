import { expect, test } from '@playwright/test'
import { localeRouteFixtures } from '../fixtures/locale-route-fixtures'

test.describe('Locale SEO metadata', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('pdf-flow-locale', 'en')
    })

    await page.route('**/api/v1/admin/public-config', async (route) => {
      await route.fulfill({
        json: {
          settings: {},
          feature_flags: {},
          content_blocks: {},
        },
      })
    })
  })

  test('emits canonical and hreflang links for locale-prefixed tool pages', async ({ page }) => {
    await page.goto('/en/tools/merge')

    await expect(page).toHaveTitle(/Merge PDF - PDF-Flow/)

    const canonical = page.locator('link[rel="canonical"]')
    await expect(canonical).toHaveAttribute('href', 'http://localhost:4173/en/tools/merge')

    for (const locale of localeRouteFixtures) {
      await expect(
        page.locator(`link[rel="alternate"][hreflang="${locale.hreflang}"]`),
      ).toHaveAttribute('href', `http://localhost:4173/${locale.routePrefix}/tools/merge`)
    }

    await expect(page.locator('link[rel="alternate"][hreflang="x-default"]')).toHaveAttribute(
      'href',
      'http://localhost:4173/zh-cn/tools/merge',
    )
  })

  for (const locale of localeRouteFixtures) {
    test(`renders the merge tool title for ${locale.id}`, async ({ page }) => {
      await page.goto(`/${locale.routePrefix}/tools/merge`)

      await expect(page).toHaveTitle(
        new RegExp(`${locale.mergeTitle} - PDF-Flow`),
      )
      await expect(
        page.getByRole('heading', { name: locale.mergeTitle }),
      ).toBeVisible()
    })
  }
})
