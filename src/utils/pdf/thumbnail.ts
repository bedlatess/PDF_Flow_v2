/**
 * PDF 缩略图生成工具
 * 使用 pdf.js 渲染真实的 PDF 页面缩略图
 */

import * as pdfjsLib from 'pdfjs-dist'
import { configurePdfJsWorker } from './configurePdfJs'

// 配置 pdf.js worker
configurePdfJsWorker()

export interface ThumbnailOptions {
  scale?: number // 缩放比例，默认 0.5
  width?: number // 目标宽度（像素）
  height?: number // 目标高度（像素）
  quality?: number // 图片质量 0-1
}

/**
 * 生成单个 PDF 页面的缩略图
 * @param file - PDF 文件
 * @param pageNumber - 页码（从 1 开始）
 * @param options - 缩略图选项
 * @returns 缩略图 Data URL
 */
export async function generatePageThumbnail(
  file: File,
  pageNumber: number,
  options?: ThumbnailOptions
): Promise<string> {
  const { scale = 0.5, width, height, quality = 0.8 } = options || {}

  try {
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
    const page = await pdf.getPage(pageNumber)

    // 获取视口
    let viewport = page.getViewport({ scale })

    // 如果指定了宽度或高度，重新计算缩放
    if (width || height) {
      const targetWidth = width || (height! * viewport.width) / viewport.height
      const targetHeight = height || (width! * viewport.height) / viewport.width
      const scaleX = targetWidth / viewport.width
      const scaleY = targetHeight / viewport.height
      const finalScale = Math.min(scaleX, scaleY)
      viewport = page.getViewport({ scale: finalScale })
    }

    // 创建 canvas
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')

    if (!context) {
      throw new Error('Failed to get canvas context')
    }

    canvas.width = viewport.width
    canvas.height = viewport.height

    // 渲染页面
    await page.render({
      canvasContext: context,
      viewport: viewport,
    }).promise

    // 转换为 Data URL
    return canvas.toDataURL('image/jpeg', quality)
  } catch (error) {
    console.error('Generate thumbnail error:', error)
    throw new Error(`Failed to generate thumbnail: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * 批量生成 PDF 所有页面的缩略图
 * @param file - PDF 文件
 * @param options - 缩略图选项
 * @returns 缩略图 Data URL 数组
 */
export async function generateAllThumbnails(
  file: File,
  options?: ThumbnailOptions
): Promise<string[]> {
  try {
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
    const numPages = pdf.numPages

    const thumbnails: string[] = []

    for (let i = 1; i <= numPages; i++) {
      const thumbnail = await generatePageThumbnail(file, i, options)
      thumbnails.push(thumbnail)
    }

    return thumbnails
  } catch (error) {
    console.error('Generate all thumbnails error:', error)
    throw new Error('Failed to generate thumbnails')
  }
}

/**
 * 生成指定页面范围的缩略图
 * @param file - PDF 文件
 * @param pages - 页码数组（从 1 开始）
 * @param options - 缩略图选项
 * @returns 缩略图 Data URL 数组
 */
export async function generateThumbnailsByPages(
  file: File,
  pages: number[],
  options?: ThumbnailOptions
): Promise<Map<number, string>> {
  const thumbnailMap = new Map<number, string>()

  try {
    for (const pageNum of pages) {
      const thumbnail = await generatePageThumbnail(file, pageNum, options)
      thumbnailMap.set(pageNum, thumbnail)
    }

    return thumbnailMap
  } catch (error) {
    console.error('Generate thumbnails by pages error:', error)
    throw new Error('Failed to generate thumbnails')
  }
}

/**
 * 缩略图缓存管理
 */
class ThumbnailCache {
  private cache: Map<string, string> = new Map()
  private maxSize: number = 50 // 最多缓存 50 个缩略图

  /**
   * 生成缓存 key
   */
  private getCacheKey(fileId: string, pageNumber: number): string {
    return `${fileId}-${pageNumber}`
  }

  /**
   * 获取缓存的缩略图
   */
  get(fileId: string, pageNumber: number): string | undefined {
    return this.cache.get(this.getCacheKey(fileId, pageNumber))
  }

  /**
   * 设置缓存
   */
  set(fileId: string, pageNumber: number, thumbnail: string): void {
    const key = this.getCacheKey(fileId, pageNumber)

    // 如果缓存已满，删除最早的一个
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }

    this.cache.set(key, thumbnail)
  }

  /**
   * 清除指定文件的缓存
   */
  clear(fileId?: string): void {
    if (fileId) {
      const keysToDelete: string[] = []
      this.cache.forEach((_, key) => {
        if (key.startsWith(`${fileId}-`)) {
          keysToDelete.push(key)
        }
      })
      keysToDelete.forEach((key) => this.cache.delete(key))
    } else {
      this.cache.clear()
    }
  }

  /**
   * 获取缓存大小
   */
  size(): number {
    return this.cache.size
  }
}

// 导出全局缓存实例
export const thumbnailCache = new ThumbnailCache()
