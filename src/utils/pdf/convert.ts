/**
 * PDF 格式转换工具
 * 图片转 PDF / PDF 转图片
 */

import jsPDF from 'jspdf'
import * as pdfjsLib from 'pdfjs-dist'
import { configurePdfJsWorker } from './configurePdfJs'

// 配置 pdf.js worker（需要在 public/wasm/ 目录下放置 worker 文件）
configurePdfJsWorker()

/**
 * 图片转 PDF
 * @param images - 图片文件数组
 * @param options - 转换选项
 * @returns PDF Blob
 */
export async function imagesToPDF(
  images: File[],
  options?: {
    pageSize?: 'a4' | 'letter' | 'a3'
    orientation?: 'portrait' | 'landscape'
    quality?: number // 0-1
  }
): Promise<Blob> {
  if (!images || images.length === 0) {
    throw new Error('No images provided')
  }

  const { pageSize = 'a4', orientation = 'portrait' } = options || {}

  try {
    const pdf = new jsPDF({
      orientation,
      unit: 'mm',
      format: pageSize,
    })

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()

    for (let i = 0; i < images.length; i++) {
      const image = images[i]

      // 读取图片
      const imageData = await readImageAsDataURL(image)

      // 获取图片尺寸
      const imgDimensions = await getImageDimensions(imageData)

      // 计算适配尺寸（保持宽高比）
      const ratio = Math.min(
        pageWidth / imgDimensions.width,
        pageHeight / imgDimensions.height
      )

      const width = imgDimensions.width * ratio
      const height = imgDimensions.height * ratio

      // 居中放置
      const x = (pageWidth - width) / 2
      const y = (pageHeight - height) / 2

      // 如果不是第一页，添加新页
      if (i > 0) {
        pdf.addPage()
      }

      // 添加图片
      pdf.addImage(imageData, 'JPEG', x, y, width, height, undefined, 'FAST')
    }

    // 输出为 Blob
    const pdfBlob = pdf.output('blob')
    return pdfBlob
  } catch (error) {
    console.error('Images to PDF error:', error)
    throw new Error(`Failed to convert images to PDF: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * PDF 转图片
 * @param file - PDF 文件
 * @param options - 转换选项
 * @returns 图片 Blob 数组
 */
export async function pdfToImages(
  file: File,
  options?: {
    scale?: number // 缩放比例，默认 2.0
    format?: 'png' | 'jpeg'
    quality?: number // JPEG 质量 0-1
  }
): Promise<Blob[]> {
  if (!file) {
    throw new Error('No file provided')
  }

  const { scale = 2.0, format = 'png', quality = 0.95 } = options || {}

  try {
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise

    const images: Blob[] = []

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum)
      const viewport = page.getViewport({ scale })

      // 创建 canvas
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')

      if (!context) {
        throw new Error('Failed to get canvas context')
      }

      canvas.height = viewport.height
      canvas.width = viewport.width

      // 渲染页面
      await page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise

      // 转换为 Blob
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Failed to convert canvas to blob'))
            }
          },
          format === 'jpeg' ? 'image/jpeg' : 'image/png',
          quality
        )
      })

      images.push(blob)
    }

    return images
  } catch (error) {
    console.error('PDF to images error:', error)
    throw new Error(`Failed to convert PDF to images: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * 读取图片为 Data URL
 */
function readImageAsDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        resolve(e.target.result as string)
      } else {
        reject(new Error('Failed to read image'))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read image'))
    reader.readAsDataURL(file)
  })
}

/**
 * 获取图片尺寸
 */
function getImageDimensions(dataURL: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      resolve({ width: img.width, height: img.height })
    }
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = dataURL
  })
}

/**
 * 单张图片转 PDF
 */
export async function imageToPDF(image: File): Promise<Blob> {
  return imagesToPDF([image])
}
