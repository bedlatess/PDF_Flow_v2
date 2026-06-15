import { describe, expect, it } from 'vitest'
import {
  featuredFooterTools,
  getToolByFeatureKey,
  getToolById,
  pdfTools,
  toolCategories,
  toolRoutes,
  type ToolAccess,
  type ToolSmokeTag,
} from '@/data/pdfTools'

const expectUnique = (values: string[]) => {
  expect(new Set(values).size).toBe(values.length)
}

describe('pdf tools registry', () => {
  it('keeps tool identifiers, paths, and feature keys unique', () => {
    expect(pdfTools.length).toBeGreaterThan(0)
    expectUnique(pdfTools.map((tool) => tool.id))
    expectUnique(pdfTools.map((tool) => tool.slug))
    expectUnique(pdfTools.map((tool) => tool.route))
    expectUnique(pdfTools.map((tool) => tool.routeName))
    expectUnique(pdfTools.map((tool) => tool.featureKey))
  })

  it('keeps route, category, access, and smoke metadata valid', () => {
    const validAccess: ToolAccess[] = ['guest', 'login', 'pro']
    const validSmokeTags: ToolSmokeTag[] = ['upload', 'access-panel']

    for (const tool of pdfTools) {
      expect(tool.route).toBe(`/tools/${tool.slug}`)
      expect(tool.titleKey).toBeTruthy()
      expect(tool.descriptionKey).toBeTruthy()
      expect(toolCategories).toContain(tool.category)
      expect(validAccess).toContain(tool.access)
      expect(validSmokeTags).toContain(tool.smokeTag)
      expect(tool.component).toEqual(expect.any(Function))
    }
  })

  it('generates detail routes directly from the registry', () => {
    expect(toolRoutes).toHaveLength(pdfTools.length)

    for (const tool of pdfTools) {
      const route = toolRoutes.find((item) => item.name === tool.routeName)

      expect(route).toBeTruthy()
      expect(route?.path).toBe(tool.slug)
      expect(route?.component).toBe(tool.component)
      expect(route?.meta).toMatchObject({
        titleKey: tool.titleKey,
        descriptionKey: tool.descriptionKey,
        featureKey: tool.featureKey,
        toolId: tool.id,
        toolAccess: tool.access,
        smokeTag: tool.smokeTag,
      })
    }
  })

  it('resolves lookup helpers and footer tools from the same registry', () => {
    for (const tool of pdfTools) {
      expect(getToolById(tool.id)).toBe(tool)
      expect(getToolByFeatureKey(tool.featureKey)).toBe(tool)
    }

    for (const toolId of featuredFooterTools) {
      expect(getToolById(toolId)).toBeTruthy()
    }
  })

  it('registers PDF to Word as a signed-in convert tool', () => {
    const tool = getToolByFeatureKey('pdf_to_word')

    expect(tool).toMatchObject({
      id: 'pdfToWord',
      slug: 'pdf-to-word',
      routeName: 'pdf-to-word',
      category: 'convert',
      mode: 'cloud',
      access: 'login',
      smokeTag: 'access-panel',
    })
  })

  it('registers PDF to Excel as a signed-in convert tool', () => {
    const tool = getToolByFeatureKey('pdf_to_excel')

    expect(tool).toMatchObject({
      id: 'pdfToExcel',
      slug: 'pdf-to-excel',
      routeName: 'pdf-to-excel',
      category: 'convert',
      mode: 'cloud',
      access: 'login',
      smokeTag: 'access-panel',
    })
  })

  it('registers Batch Convert as a signed-in convert tool', () => {
    const tool = getToolByFeatureKey('batch_convert')

    expect(tool).toMatchObject({
      id: 'batchConvert',
      slug: 'batch-convert',
      routeName: 'batch-convert',
      category: 'convert',
      mode: 'cloud',
      access: 'login',
      smokeTag: 'access-panel',
    })
  })
})
