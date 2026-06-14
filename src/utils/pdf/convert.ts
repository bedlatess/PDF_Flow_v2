import jsPDF from 'jspdf'
import * as pdfjsLib from 'pdfjs-dist'
import { configurePdfJsWorker } from './configurePdfJs'

configurePdfJsWorker()

export async function imagesToPDF(
  images: File[],
  options?: {
    pageSize?: 'a4' | 'letter' | 'a3'
    orientation?: 'portrait' | 'landscape'
    quality?: number
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

    for (let index = 0; index < images.length; index += 1) {
      const imageData = await readImageAsDataURL(images[index])
      const normalizedImage = await normalizeImageForPdf(imageData, options?.quality)
      const imgDimensions = normalizedImage.dimensions
      const ratio = Math.min(
        pageWidth / imgDimensions.width,
        pageHeight / imgDimensions.height
      )

      const width = imgDimensions.width * ratio
      const height = imgDimensions.height * ratio
      const x = (pageWidth - width) / 2
      const y = (pageHeight - height) / 2

      if (index > 0) {
        pdf.addPage()
      }

      pdf.addImage(normalizedImage.dataUrl, 'JPEG', x, y, width, height, undefined, 'FAST')
    }

    return pdf.output('blob')
  } catch (error) {
    throw new Error(`Failed to convert images to PDF: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

export async function pdfToImages(
  file: File,
  options?: {
    scale?: number
    format?: 'png' | 'jpeg'
    quality?: number
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

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
      const page = await pdf.getPage(pageNum)
      const viewport = page.getViewport({ scale })
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')

      if (!context) {
        throw new Error('Failed to get canvas context')
      }

      canvas.height = viewport.height
      canvas.width = viewport.width

      await page.render({
        canvasContext: context,
        viewport,
      }).promise

      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (result) => {
            if (result) {
              resolve(result)
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
    throw new Error(`Failed to convert PDF to images: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

function readImageAsDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      if (event.target?.result) {
        resolve(event.target.result as string)
      } else {
        reject(new Error('Failed to read image'))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read image'))
    reader.readAsDataURL(file)
  })
}

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

async function normalizeImageForPdf(
  dataURL: string,
  quality = 0.92
): Promise<{ dataUrl: string; dimensions: { width: number; height: number } }> {
  const dimensions = await getImageDimensions(dataURL)
  const img = await loadImage(dataURL)
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')

  if (!context) {
    throw new Error('Failed to prepare image')
  }

  canvas.width = dimensions.width
  canvas.height = dimensions.height
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  context.drawImage(img, 0, 0)

  return {
    dataUrl: canvas.toDataURL('image/jpeg', quality),
    dimensions,
  }
}

function loadImage(dataURL: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = dataURL
  })
}

export async function imageToPDF(image: File): Promise<Blob> {
  return imagesToPDF([image])
}
