import { expect, test, type Page } from '@playwright/test'
import { writeFile } from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'
import { waitForPageReady } from '../helpers/test-utils'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const samplePdf = path.join(__dirname, '../fixtures/sample1.pdf')

type UserRole = 'guest' | 'free' | 'pro'

const users = {
  free: {
    id: 701,
    email: 'free-regression@pdf-flow.test',
    full_name: 'Free Regression User',
    role: 'free',
    is_active: true,
    is_verified: true,
    created_at: '2026-06-12T08:00:00.000Z',
  },
  pro: {
    id: 702,
    email: 'pro-regression@pdf-flow.test',
    full_name: 'Pro Regression User',
    role: 'pro',
    is_active: true,
    is_verified: true,
    created_at: '2026-06-12T08:00:00.000Z',
  },
}

async function mockToolShell(page: Page, role: UserRole = 'guest') {
  await page.addInitScript((selectedRole) => {
    window.localStorage.setItem('pdf-flow-locale', 'en')

    if (selectedRole === 'guest') {
      window.localStorage.removeItem('access_token')
      window.localStorage.removeItem('refresh_token')
      return
    }

    window.localStorage.setItem('access_token', `${selectedRole}-flow-regression-token`)
    window.localStorage.setItem('refresh_token', `${selectedRole}-flow-regression-refresh-token`)
  }, role)

  await page.route('**/api/v1/admin/public-config', async (route) => {
    await route.fulfill({ json: { settings: {}, feature_flags: {}, content_blocks: {} } })
  })

  await page.route('**/api/v1/auth/me', async (route) => {
    if (role === 'guest') {
      await route.fulfill({ status: 401, json: { detail: 'Not authenticated' } })
      return
    }

    await route.fulfill({ json: users[role] })
  })

  await page.route('**/api/v1/users/me/stats', async (route) => {
    await route.fulfill({
      json: {
        total_requests: 20,
        requests_today: 2,
        storage_used: 0,
        quota_remaining: role === 'pro' ? 498 : 18,
        quota_limit: role === 'pro' ? 500 : 20,
        role,
      },
    })
  })
}

async function openTool(page: Page, route: string, role: UserRole = 'guest') {
  await mockToolShell(page, role)
  await page.goto(route)
  await waitForPageReady(page)
}

async function expectOnlyAccessPanel(page: Page) {
  await expect(page.locator('[data-testid="tool-access-panel"]')).toBeVisible()
  await expect(page.locator('[data-testid="drag-drop-zone"]')).toHaveCount(0)
  await expect(page.locator('[data-testid="file-preview"]')).toHaveCount(0)
}

async function selectFile(page: Page, filePath: string) {
  await page.locator('[data-testid="drag-drop-zone"]').first().waitFor({ state: 'visible' })
  await page.locator('input[type="file"]').first().setInputFiles(filePath)
  await expect(page.getByText(path.basename(filePath)).first()).toBeVisible({ timeout: 20000 })
}

async function expectButtonHidden(page: Page, name: string | RegExp) {
  await expect(page.getByRole('button', { name }).first()).toBeHidden()
}

async function expectButtonVisible(page: Page, name: string | RegExp) {
  await expect(page.getByRole('button', { name }).first()).toBeVisible({ timeout: 20000 })
}

test.describe('Tool flow regressions', () => {
  test('keeps free local mode copy separate from locked Pro cloud copy', async ({ page }) => {
    await openTool(page, '/tools/compress')
    await selectFile(page, samplePdf)

    await expect(page.getByText('Free mode')).toBeVisible()
    await expect(page.getByText('Good for quick everyday files.')).toBeVisible()
    await expect(page.getByText('Use Pro for bigger files, OCR, Office, AI, and longer jobs.')).toBeHidden()
    await expect(page.getByText('Pro unlocks bigger files, OCR, Office, AI, and longer jobs.')).toBeVisible()
  })

  test('keeps gated tools closed for guests and free users without leaking workspaces', async ({ page }) => {
    const guestTools = [
      '/tools/repair',
      '/tools/protect',
      '/tools/unlock',
      '/tools/office-to-pdf',
      '/tools/ocr',
      '/tools/ai-analyzer',
      '/tools/fill-form',
      '/tools/annotate',
    ]

    for (const route of guestTools) {
      await openTool(page, route)
      await expectOnlyAccessPanel(page)
    }

    for (const route of ['/tools/ocr', '/tools/ai-analyzer', '/tools/fill-form', '/tools/annotate']) {
      await openTool(page, route, 'free')
      await expectOnlyAccessPanel(page)
      await expect(page.locator('[data-testid="tool-access-panel"]')).toContainText('Upgrade required')
    }
  })

  test('shows only upload entry before file selection on authenticated cloud tools', async ({ page }, testInfo) => {
    const officeFile = testInfo.outputPath('flow-sample.docx')
    await writeFile(officeFile, 'PDF-Flow office flow regression fixture')

    const tools = [
      {
        route: '/tools/repair',
        role: 'free' as const,
        uploadPath: samplePdf,
        assertHiddenBeforeUpload: async () => {
          await expectButtonHidden(page, 'Repair PDF')
        },
        assertVisibleAfterUpload: async () => {
          await expectButtonVisible(page, 'Repair PDF')
        },
      },
      {
        route: '/tools/protect',
        role: 'free' as const,
        uploadPath: samplePdf,
        assertHiddenBeforeUpload: async () => {
          await expect(page.getByLabel('Open password')).toBeHidden()
        },
        assertVisibleAfterUpload: async () => {
          await expect(page.getByLabel('Open password')).toBeVisible()
          await expectButtonVisible(page, 'Create protected PDF')
        },
      },
      {
        route: '/tools/unlock',
        role: 'free' as const,
        uploadPath: samplePdf,
        assertHiddenBeforeUpload: async () => {
          await expect(page.getByLabel('Current open password')).toBeHidden()
        },
        assertVisibleAfterUpload: async () => {
          await expect(page.getByLabel('Current open password')).toBeVisible()
          await expectButtonVisible(page, 'Create unlocked copy')
        },
      },
      {
        route: '/tools/office-to-pdf',
        role: 'free' as const,
        uploadPath: officeFile,
        assertHiddenBeforeUpload: async () => {
          await expectButtonHidden(page, 'Convert to PDF')
          await expect(page.getByText('Conversion workspace')).toBeHidden()
        },
        assertVisibleAfterUpload: async () => {
          await expectButtonVisible(page, 'Convert to PDF')
          await expect(page.getByText('Conversion workspace')).toBeVisible()
        },
      },
      {
        route: '/tools/ocr',
        role: 'pro' as const,
        uploadPath: samplePdf,
        assertHiddenBeforeUpload: async () => {
          await expect(page.getByText('OCR workspace')).toBeHidden()
          await expectButtonHidden(page, 'Start OCR')
        },
        assertVisibleAfterUpload: async () => {
          await expect(page.getByText('OCR workspace')).toBeVisible()
          await expectButtonVisible(page, 'Start OCR')
        },
      },
      {
        route: '/tools/ai-analyzer',
        role: 'pro' as const,
        uploadPath: samplePdf,
        assertHiddenBeforeUpload: async () => {
          await expect(page.getByLabel('Summary Length')).toBeHidden()
          await expectButtonHidden(page, 'Generate Summary')
        },
        assertVisibleAfterUpload: async () => {
          await expect(page.getByLabel('Summary Length')).toBeVisible()
          await expectButtonVisible(page, 'Generate Summary')
        },
      },
      {
        route: '/tools/fill-form',
        role: 'pro' as const,
        uploadPath: samplePdf,
        setupRoutes: async () => {
          await page.route('**/api/v1/advanced/form/fields', async (route) => {
            await route.fulfill({
              json: {
                fields: [
                  { name: 'Full name', type: 'text', required: true, default_value: '' },
                ],
              },
            })
          })
        },
        assertHiddenBeforeUpload: async () => {
          await expect(page.getByText('Review fields')).toBeHidden()
          await expectButtonHidden(page, 'Fill Form')
        },
        assertVisibleAfterUpload: async () => {
          await expect(page.getByText('Review fields')).toBeVisible({ timeout: 20000 })
          await expectButtonVisible(page, 'Fill Form')
        },
      },
      {
        route: '/tools/annotate',
        role: 'pro' as const,
        uploadPath: samplePdf,
        assertHiddenBeforeUpload: async () => {
          await expect(page.getByText('Configure annotation')).toBeHidden()
          await expectButtonHidden(page, 'Add Annotation')
        },
        assertVisibleAfterUpload: async () => {
          await expect(page.getByText('Configure annotation')).toBeVisible()
          await expectButtonVisible(page, 'Add Annotation')
        },
      },
    ]

    for (const tool of tools) {
      await openTool(page, tool.route, tool.role)
      await tool.setupRoutes?.()

      await expect(page.locator('[data-testid="tool-access-panel"]')).toHaveCount(0)
      await expect(page.locator('[data-testid="drag-drop-zone"]').first()).toBeVisible()
      await tool.assertHiddenBeforeUpload()

      await selectFile(page, tool.uploadPath)
      await tool.assertVisibleAfterUpload()
    }
  })

  test('keeps local staged tools focused on the next required input', async ({ page }) => {
    await openTool(page, '/tools/crop')
    await expect(page.locator('[data-testid="drag-drop-zone"]').first()).toBeVisible()
    await expect(page.getByText('Set crop margins')).toBeHidden()
    await selectFile(page, samplePdf)
    await expect(page.getByText('Set crop margins')).toBeVisible({ timeout: 20000 })
    await expect(page.getByText('Create cropped PDF')).toBeVisible()

    await openTool(page, '/tools/sign')
    await expect(page.locator('[data-testid="drag-drop-zone"]')).toHaveCount(1)
    await expect(page.getByText('Adjust the signature position')).toBeHidden()
    await selectFile(page, samplePdf)
    await expect(page.locator('[data-testid="drag-drop-zone"]').first()).toBeVisible({ timeout: 20000 })
    await expect(page.getByText('Adjust the signature position')).toBeHidden()
  })
})
