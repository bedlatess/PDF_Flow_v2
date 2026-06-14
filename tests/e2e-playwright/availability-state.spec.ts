import { expect, type Page, test } from '@playwright/test'

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    bodyScrollWidth: document.body.scrollWidth,
    bodyClientWidth: document.body.clientWidth,
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
  }))

  expect(metrics.bodyScrollWidth).toBeLessThanOrEqual(metrics.bodyClientWidth + 2)
  expect(metrics.docScrollWidth).toBeLessThanOrEqual(metrics.docClientWidth + 2)
}

async function mockAvailabilityShell(
  page: Page,
  options: { disabledMerge?: boolean; hiddenMerge?: boolean } = {},
) {
  await page.addInitScript(() => {
    window.localStorage.setItem('pdf-flow-locale', 'en')
    window.localStorage.removeItem('access_token')
    window.localStorage.removeItem('refresh_token')
  })

  await page.route('**/api/v1/admin/public-config', async (route) => {
    await route.fulfill({
      json: {
        settings: {},
        feature_flags: options.disabledMerge
          ? {
              merge_pdf: {
                label: 'Merge PDF',
                description: 'Combine PDFs',
                enabled: false,
                is_public: true,
                requires_login: false,
                requires_pro: false,
                maintenance_message: 'Merge is paused for maintenance.',
              },
            }
          : options.hiddenMerge
            ? {
                merge_pdf: {
                  label: 'Merge PDF',
                  description: 'Combine PDFs',
                  enabled: true,
                  is_public: false,
                  requires_login: false,
                  requires_pro: false,
                  maintenance_message: null,
                },
              }
          : {},
        content_blocks: {},
      },
    })
  })

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({ status: 401, json: { detail: 'Not authenticated' } })
  })
}

test.describe('Availability and route edge states', () => {
  test('shows a dedicated feature-disabled state instead of silently returning home', async ({ page }) => {
    await mockAvailabilityShell(page, { disabledMerge: true })

    await page.goto('/tools/merge')

    await expect(page).toHaveURL(/\/availability\/feature-disabled/)
    await expect(page.getByRole('heading', { name: 'This tool is temporarily unavailable' })).toBeVisible()
    await expect(page.getByText('Merge is paused for maintenance.')).toBeVisible()
    await expect(page.getByText('Merge PDF')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Back to tools' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Try this tool again' })).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })

  test('hides a non-public tool from listings but keeps direct route gating separate', async ({ page }) => {
    await mockAvailabilityShell(page, { hiddenMerge: true })

    await page.goto('/tools')

    await expect(page.getByRole('heading', { name: 'Every PDF tool in one place' })).toBeVisible()
    await expect(page.locator('[data-testid="tool-card"]').filter({ hasText: 'Merge PDF' })).toHaveCount(0)

    await page.goto('/tools/merge')

    await expect(page).toHaveURL(/\/en\/tools\/merge/)
    await expect(page.getByRole('heading', { name: 'Merge PDF' })).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })

  test('renders a clear not-found state for unknown routes', async ({ page }) => {
    await mockAvailabilityShell(page)
    await page.setViewportSize({ width: 390, height: 900 })

    await page.goto('/missing/deep/path?from=test')

    await expect(page).toHaveURL(/\/en\/missing\/deep\/path\?from=test/)
    await expect(page.getByRole('heading', { name: 'We could not find that page' })).toBeVisible()
    await expect(page.getByText('/en/missing/deep/path?from=test', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Back home' })).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })
})
