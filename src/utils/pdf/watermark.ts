/**
 * Local PDF watermark utilities.
 *
 * pdf-lib's built-in StandardFonts only support WinAnsi text, so Chinese
 * watermark text fails when drawn directly. We render the text to a browser
 * canvas first, then embed the PNG into the PDF. This keeps processing local
 * while supporting the user's system fonts.
 */

import { PDFDocument, degrees } from 'pdf-lib'
import { pdfBytesToBlob } from './blob'

export type WatermarkPosition = 'center' | 'tile' | 'top' | 'bottom'

export interface WatermarkOptions {
  text: string
  opacity?: number
  rotation?: number
  fontSize?: number
  color?: { r: number; g: number; b: number }
  position?: WatermarkPosition
  pages?: number[]
}

interface WatermarkImage {
  bytes: Uint8Array
  width: number
  height: number
}

export async function addWatermark(
  file: File,
  options: WatermarkOptions
): Promise<Blob> {
  if (!file) {
    throw new Error('No file provided for watermark')
  }

  const {
    text,
    opacity = 0.3,
    rotation = 45,
    fontSize = 40,
    color = { r: 128, g: 128, b: 128 },
    position = 'center',
    pages,
  } = options

  if (!text || !text.trim()) {
    throw new Error('Watermark text is required')
  }

  if (opacity < 0 || opacity > 1) {
    throw new Error('Opacity must be between 0 and 1')
  }

  try {
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await PDFDocument.load(arrayBuffer)
    const totalPages = pdf.getPageCount()
    const pageIndices =
      pages && pages.length > 0
        ? pages.map((num) => num - 1).filter((i) => i >= 0 && i < totalPages)
        : Array.from({ length: totalPages }, (_, i) => i)

    const watermark = await renderWatermarkImage(text.trim(), fontSize, color)
    const embeddedWatermark = await pdf.embedPng(watermark.bytes)
    const allPages = pdf.getPages()

    for (const index of pageIndices) {
      const page = allPages[index]
      const { width, height } = page.getSize()

      if (position === 'tile') {
        drawTiledWatermark(page, {
          image: embeddedWatermark,
          imageWidth: watermark.width,
          imageHeight: watermark.height,
          opacity,
          rotation,
          width,
          height,
        })
      } else {
        const { x, y, rot } = computePosition(
          position,
          rotation,
          width,
          height,
          watermark.width,
          watermark.height
        )
        page.drawImage(embeddedWatermark, {
          x,
          y,
          width: watermark.width,
          height: watermark.height,
          opacity,
          rotate: degrees(rot),
        })
      }
    }

    const pdfBytes = await pdf.save()
    return pdfBytesToBlob(pdfBytes)
  } catch (error) {
    console.error('PDF watermark error:', error)
    throw new Error(
      `Failed to add watermark: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

function renderWatermarkImage(
  text: string,
  fontSize: number,
  color: { r: number; g: number; b: number }
): Promise<WatermarkImage> {
  const scale = Math.max(window.devicePixelRatio || 1, 2)
  const measureCanvas = document.createElement('canvas')
  const measureContext = measureCanvas.getContext('2d')
  if (!measureContext) {
    throw new Error('Canvas is unavailable in this browser')
  }

  const fontFamily = '"Noto Sans SC", "Microsoft YaHei", "PingFang SC", "Source Han Sans SC", sans-serif'
  measureContext.font = `700 ${fontSize * scale}px ${fontFamily}`
  const metrics = measureContext.measureText(text)
  const padding = Math.ceil(fontSize * scale * 0.45)
  const width = Math.ceil(metrics.width + padding * 2)
  const height = Math.ceil(fontSize * scale * 1.45 + padding)

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('Canvas is unavailable in this browser')
  }

  context.clearRect(0, 0, width, height)
  context.font = `700 ${fontSize * scale}px ${fontFamily}`
  context.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`
  context.textBaseline = 'middle'
  context.textAlign = 'center'
  context.fillText(text, width / 2, height / 2)

  return new Promise((resolve, reject) => {
    canvas.toBlob(async (blob) => {
      if (!blob) {
        reject(new Error('Failed to render watermark text'))
        return
      }

      resolve({
        bytes: new Uint8Array(await blob.arrayBuffer()),
        width: width / scale,
        height: height / scale,
      })
    }, 'image/png')
  })
}

function computePosition(
  position: WatermarkPosition,
  rotation: number,
  pageWidth: number,
  pageHeight: number,
  imageWidth: number,
  imageHeight: number
): { x: number; y: number; rot: number } {
  switch (position) {
    case 'top':
      return {
        x: (pageWidth - imageWidth) / 2,
        y: pageHeight - imageHeight - 30,
        rot: 0,
      }
    case 'bottom':
      return {
        x: (pageWidth - imageWidth) / 2,
        y: 30,
        rot: 0,
      }
    case 'center':
    default: {
      const rad = (rotation * Math.PI) / 180
      const offsetX = (imageWidth / 2) * Math.cos(rad)
      const offsetY = (imageWidth / 2) * Math.sin(rad)
      return {
        x: pageWidth / 2 - offsetX,
        y: pageHeight / 2 - offsetY,
        rot: rotation,
      }
    }
  }
}

function drawTiledWatermark(
  page: ReturnType<PDFDocument['getPages']>[number],
  params: {
    image: Awaited<ReturnType<PDFDocument['embedPng']>>
    imageWidth: number
    imageHeight: number
    opacity: number
    rotation: number
    width: number
    height: number
  }
): void {
  const { image, imageWidth, imageHeight, opacity, rotation, width, height } = params
  const stepX = Math.max(imageWidth + 80, 200)
  const stepY = Math.max(imageHeight + 80, 150)

  for (let y = -stepY; y < height + stepY; y += stepY) {
    for (let x = -stepX; x < width + stepX; x += stepX) {
      page.drawImage(image, {
        x,
        y,
        width: imageWidth,
        height: imageHeight,
        opacity,
        rotate: degrees(rotation),
      })
    }
  }
}

export async function addDiagonalWatermark(
  file: File,
  text: string
): Promise<Blob> {
  return addWatermark(file, { text, position: 'center', rotation: 45 })
}
