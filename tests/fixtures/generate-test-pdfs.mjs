/* eslint-env node */

import { writeFileSync } from 'fs'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

async function generateTestPDF(filename, pageCount, title) {
  const pdfDoc = await PDFDocument.create()
  const font = await pdfDoc.embedFont(StandardFonts.TimesRoman)

  for (let index = 0; index < pageCount; index += 1) {
    const page = pdfDoc.addPage([595, 842])
    const { height } = page.getSize()
    const pageNumber = index + 1

    page.drawText(title, {
      x: 50,
      y: height - 50,
      size: 24,
      font,
      color: rgb(0, 0, 0),
    })

    page.drawText(`Page ${pageNumber} of ${pageCount}`, {
      x: 50,
      y: height - 100,
      size: 14,
      font,
      color: rgb(0.5, 0.5, 0.5),
    })

    page.drawText(
      `This is a test PDF file.\n\nGenerated for PDF-Flow regression tests.\n\nPage number: ${pageNumber}`,
      {
        x: 50,
        y: height - 150,
        size: 12,
        font,
        color: rgb(0, 0, 0),
        lineHeight: 20,
      },
    )

    page.drawRectangle({
      x: 50,
      y: 100,
      width: 200,
      height: 100,
      borderColor: rgb(0.31, 0.27, 0.9),
      borderWidth: 2,
    })

    page.drawText('PDF-Flow Test File', {
      x: 70,
      y: 130,
      size: 10,
      font,
      color: rgb(0.31, 0.27, 0.9),
    })
  }

  const pdfBytes = await pdfDoc.save()
  const outputPath = join(__dirname, filename)
  writeFileSync(outputPath, pdfBytes)
  console.log(`Generated ${filename} (${pageCount} pages)`)
}

async function main() {
  console.log('Generating test PDF files...')

  await generateTestPDF('sample1.pdf', 2, 'Sample PDF 1')
  await generateTestPDF('sample2.pdf', 3, 'Sample PDF 2')
  await generateTestPDF('multi-page.pdf', 10, 'Multi-Page Test PDF')
  await generateTestPDF('large.pdf', 50, 'Large Test PDF')

  console.log('All test PDF files generated in tests/fixtures.')
}

main().catch((error) => {
  console.error('Failed to generate test PDFs:', error)
  process.exit(1)
})
