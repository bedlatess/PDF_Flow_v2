import { PDFDocument } from 'pdf-lib'
import { pdfBytesToBlob } from './blob'

export interface CropMargins {
  topPercent: number
  rightPercent: number
  bottomPercent: number
  leftPercent: number
}

export async function cropPDF(file: File, margins: CropMargins): Promise<Blob> {
  if (!file) {
    throw new Error('No PDF file provided')
  }

  const arrayBuffer = await file.arrayBuffer()
  const pdf = await PDFDocument.load(arrayBuffer)

  for (const page of pdf.getPages()) {
    const cropBox = page.getCropBox()
    const left = cropBox.width * clamp(margins.leftPercent, 0, 45) / 100
    const right = cropBox.width * clamp(margins.rightPercent, 0, 45) / 100
    const bottom = cropBox.height * clamp(margins.bottomPercent, 0, 45) / 100
    const top = cropBox.height * clamp(margins.topPercent, 0, 45) / 100
    const width = cropBox.width - left - right
    const height = cropBox.height - top - bottom

    if (width <= cropBox.width * 0.1 || height <= cropBox.height * 0.1) {
      throw new Error('Crop area is too small')
    }

    page.setCropBox(
      cropBox.x + left,
      cropBox.y + bottom,
      width,
      height
    )
  }

  const pdfBytes = await pdf.save()
  return pdfBytesToBlob(pdfBytes)
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}
