import { expect, test, type Page } from '@playwright/test'
import { writeFile } from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'
import { waitForPageReady, uploadFile, uploadMultipleFiles } from '../helpers/test-utils'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const samplePdf = path.join(__dirname, '../fixtures/sample1.pdf')
const PNG_1X1_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII='

async function mockPublicApp(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem('pdf-flow-locale', 'en')
    window.localStorage.removeItem('access_token')
    window.localStorage.removeItem('refresh_token')
  })

  await page.route('**/api/v1/admin/public-config', async (route) => {
    await route.fulfill({ json: { settings: {}, feature_flags: {}, content_blocks: {} } })
  })

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({ status: 401, json: { detail: 'Not authenticated' } })
  })
}

async function openTool(page: Page, route: string) {
  await mockPublicApp(page)
  await page.goto(route)
  await waitForPageReady(page)
}

async function createImageFixture(filePath: string) {
  await writeFile(filePath, Buffer.from(PNG_1X1_BASE64, 'base64'))
}

test.describe('Local PDF tool workflows', () => {
  test('rotates a PDF and shows the download dialog', async ({ page }) => {
    await openTool(page, '/tools/rotate')

    await expect(page.getByRole('heading', { name: 'Rotate PDF', level: 1 })).toBeVisible()
    await uploadFile(page, samplePdf)

    await expect(page.locator('[data-testid="file-preview"]')).toContainText('sample1.pdf')
    await page.getByRole('button', { name: /Counterclockwise/ }).click()
    await page.getByRole('button', { name: 'Rotate PDF' }).click()

    await expect(page.getByRole('dialog', { name: 'Rotation complete' })).toBeVisible({
      timeout: 20000,
    })
    await expect(page.getByRole('button', { name: 'Download' })).toBeVisible()
  })

  test('converts a PDF into page images', async ({ page }) => {
    await openTool(page, '/tools/pdf-to-image')

    await expect(page.getByRole('heading', { name: 'PDF to Image', level: 1 })).toBeVisible()
    await uploadFile(page, samplePdf)

    await expect(page.getByRole('heading', { name: 'Choose the image format' })).toBeVisible()
    await page.getByRole('button', { name: 'jpeg' }).click()
    await page.getByRole('button', { name: 'Convert to images' }).click()

    await expect(page.getByRole('heading', { name: '2 images generated' })).toBeVisible({
      timeout: 30000,
    })
    await expect(page.getByAltText('Page 1')).toBeVisible()
    await expect(page.getByAltText('Page 2')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Download all' })).toBeVisible()
  })

  test('converts uploaded images into a PDF', async ({ page }, testInfo) => {
    const imageOne = testInfo.outputPath('image-one.png')
    const imageTwo = testInfo.outputPath('image-two.png')
    await createImageFixture(imageOne)
    await createImageFixture(imageTwo)

    await openTool(page, '/tools/image-to-pdf')

    await expect(page.getByRole('heading', { name: 'Image to PDF', level: 1 })).toBeVisible()
    await uploadMultipleFiles(page, [imageOne, imageTwo])

    await expect(page.getByRole('heading', { name: '2 images selected' })).toBeVisible()
    await page.getByLabel('Page size').selectOption('letter')
    await page.getByLabel('Orientation').selectOption('landscape')
    await page.getByRole('button', { name: 'Convert to PDF' }).click()

    await expect(page.getByRole('dialog', { name: 'Conversion complete' })).toBeVisible({
      timeout: 20000,
    })
    await expect(page.getByRole('button', { name: 'Download' })).toBeVisible()
  })

  test('deletes selected pages from a PDF', async ({ page }) => {
    await openTool(page, '/tools/delete-pages')

    await expect(page.getByRole('heading', { name: 'Delete PDF Pages', level: 1 })).toBeVisible()
    await uploadFile(page, samplePdf)

    await expect(page.getByRole('heading', { name: 'Choose pages to remove' })).toBeVisible()
    await page.getByLabel('2 pages available').fill('2')
    await expect(page.getByRole('main').getByText('Keep').locator('..')).toContainText('1')
    await page.getByRole('button', { name: 'Delete selected pages' }).click()

    await expect(page.getByRole('dialog', { name: 'Pages deleted' })).toBeVisible({
      timeout: 20000,
    })
    await expect(page.getByRole('button', { name: 'Download result' })).toBeVisible()
  })

  test('reorders a PDF and generates an organized copy', async ({ page }) => {
    await openTool(page, '/tools/organize')

    await expect(page.getByRole('heading', { name: 'Organize PDF Pages', level: 1 })).toBeVisible()
    await uploadFile(page, samplePdf)

    await expect(page.getByRole('heading', { name: 'Drag pages into order' })).toBeVisible()
    await expect(page.getByText('Page 1').first()).toBeVisible()
    await expect(page.getByText('Page 2').first()).toBeVisible()
    await page.getByRole('button', { name: 'Reverse order' }).click()
    await expect(page.getByText('First page').locator('..')).toContainText('2')

    await page.getByRole('button', { name: 'Generate organized PDF' }).click()

    await expect(page.getByRole('dialog', { name: 'Pages organized' })).toBeVisible({
      timeout: 20000,
    })
    await expect(page.getByRole('button', { name: 'Download result' })).toBeVisible()
  })

  test('flattens a PDF and exposes the flattened download action', async ({ page }) => {
    await openTool(page, '/tools/flatten')

    await expect(page.getByRole('heading', { name: 'Flatten PDF', level: 1 })).toBeVisible()
    await uploadFile(page, samplePdf)

    await expect(page.getByRole('heading', { name: 'File is ready' })).toBeVisible()
    await expect(page.getByText('Pages').locator('..')).toContainText('2')
    await page.getByRole('button', { name: 'Create flattened PDF' }).click()

    await expect(page.getByRole('heading', { name: 'Flatten complete' }).first()).toBeVisible({
      timeout: 20000,
    })
    await expect(page.getByRole('button', { name: 'Download flattened PDF' }).first()).toBeVisible()
  })
})
