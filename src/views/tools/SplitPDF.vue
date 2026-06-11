<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import PageSelector from '@/components/pdf/PageSelector.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import CloudToggle from '@/components/common/CloudToggle.vue'
import ToolHeader from '@/components/tools/ToolHeader.vue'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { extractPDFPages } from '@/utils/pdf/split'
import { memoryManager } from '@/utils/memory-manager'
import { usePDFWorker } from '@/composables/usePDFWorker'
import { useCloudProcessing } from '@/composables/useCloudProcessing'
import { fileAPI } from '@/services/api'
import { historyManager } from '@/utils/history-manager'

const { t, locale } = useI18n()

const selectedFile = ref<File | null>(null)
const totalPages = ref(0)
const pageRanges = ref('')
const useVisualSelector = ref(false)
const useCloud = ref(false)
const showPageSelector = ref(false)
const showPDFViewer = ref(false)
const isProcessing = ref(false)
const processingProgress = ref(0)
const processingStatus = ref('')
const showSuccessModal = ref(false)
const resultUrl = ref('')
const errorMessage = ref('')

const { destroyWorker } = usePDFWorker()
const { processInCloud } = useCloudProcessing()

const copy = computed(() => locale.value.startsWith('zh')
  ? {
      badge: '本地工具',
      setupLabel: '页面提取',
      setupTitle: '选择要导出的页面',
      setupDesc: '你可以直接输入页码范围，也可以打开可视化选择器，更直观地挑选需要保留的页面。',
      rangeLabel: `页面范围，共 ${totalPages.value} 页`,
      rangePlaceholder: '例如：1-3,5,7-9',
      rangeHint: '用逗号分隔单页或范围，例如 1-3,5 表示提取第 1、2、3、5 页。',
      visualSelect: '可视化选择',
      actionLabel: '输出动作',
      actionTitle: '确认范围后生成新文件',
      actionTips: [
        '先确认页码范围，再点击提取。',
        '页码较多时，建议使用可视化选择以减少输入错误。',
        '处理完成后会生成一个新的 PDF 文件，不会修改原文件。',
      ],
      extract: '提取页面',
      modalTitle: '选择要提取的页面',
      successTitle: '提取完成',
      successMessage: '选定页面已经准备好，可以立即下载。',
      errorLoad: '加载 PDF 失败，请重新选择文件后再试。',
      errorNoPages: '请至少选择一个页面。',
      errorNoRange: '请输入要提取的页面范围，例如 1-3,5,7-9。',
      statusPreparing: '正在准备处理...',
      statusProcessing: '正在提取页面...',
      statusProgress: '处理中... {progress}%',
      statusDone: '处理完成',
      errorFailed: '页面提取失败，请稍后重试。',
      errorCloudFailed: '云端提取失败，请稍后再试。',
    }
  : {
      badge: 'Local tool',
      setupLabel: 'Page extraction',
      setupTitle: 'Choose the pages to export',
      setupDesc: 'Enter page ranges directly or open the visual selector for a clearer way to pick the pages you want to keep.',
      rangeLabel: `${totalPages.value} pages available`,
      rangePlaceholder: 'Example: 1-3,5,7-9',
      rangeHint: 'Separate single pages or ranges with commas. For example, 1-3,5 keeps pages 1, 2, 3, and 5.',
      visualSelect: 'Visual selector',
      actionLabel: 'Output',
      actionTitle: 'Confirm the range, then generate a new file',
      actionTips: [
        'Confirm the page range before extracting.',
        'For longer documents, the visual selector helps reduce typing mistakes.',
        'A new PDF is created after processing. Your original file stays unchanged.',
      ],
      extract: 'Extract pages',
      modalTitle: 'Choose pages to extract',
      successTitle: 'Extraction complete',
      successMessage: 'The selected pages are ready to download.',
      errorLoad: 'Failed to load the PDF. Please reselect the file and try again.',
      errorNoPages: 'Select at least one page.',
      errorNoRange: 'Enter the pages to extract, for example 1-3,5,7-9.',
      statusPreparing: 'Preparing...',
      statusProcessing: 'Extracting pages...',
      statusProgress: 'Processing... {progress}%',
      statusDone: 'Completed',
      errorFailed: 'Failed to extract pages. Please try again later.',
      errorCloudFailed: 'Cloud extraction failed. Please try again later.',
    })

const handleFilesSelected = async (files: File[]) => {
  try {
    selectedFile.value = files[0]
    totalPages.value = await getPDFPageCount(files[0])
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : copy.value.errorLoad
  }
}

const handleError = (message: string) => {
  errorMessage.value = message
}

const clearAll = () => {
  selectedFile.value = null
  totalPages.value = 0
  pageRanges.value = ''
  useVisualSelector.value = false
  showPageSelector.value = false
  errorMessage.value = ''
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const openPageSelector = () => {
  showPageSelector.value = true
}

const formatPagesAsRanges = (pages: number[]): string => {
  if (pages.length === 0) return ''

  const sorted = [...pages].sort((a, b) => a - b)
  const ranges: string[] = []
  let start = sorted[0]
  let end = sorted[0]

  for (let i = 1; i <= sorted.length; i += 1) {
    if (i < sorted.length && sorted[i] === end + 1) {
      end = sorted[i]
    } else {
      if (start === end) {
        ranges.push(`${start}`)
      } else if (end === start + 1) {
        ranges.push(`${start},${end}`)
      } else {
        ranges.push(`${start}-${end}`)
      }

      if (i < sorted.length) {
        start = sorted[i]
        end = sorted[i]
      }
    }
  }

  return ranges.join(',')
}

const handlePageSelect = (pages: number[]) => {
  if (pages.length === 0) {
    errorMessage.value = copy.value.errorNoPages
    return
  }

  pageRanges.value = formatPagesAsRanges(pages)
  showPageSelector.value = false
  useVisualSelector.value = true
}

const handlePageSelectCancel = () => {
  showPageSelector.value = false
}

const handlePreview = () => {
  showPDFViewer.value = true
}

const handleCloseViewer = () => {
  showPDFViewer.value = false
}

const extractPages = async () => {
  if (!selectedFile.value) return

  if (!pageRanges.value.trim()) {
    errorMessage.value = copy.value.errorNoRange
    return
  }

  if (useCloud.value) {
    await splitInCloud()
    return
  }

  isProcessing.value = true
  processingProgress.value = 0
  processingStatus.value = copy.value.statusPreparing
  errorMessage.value = ''

  try {
    processingProgress.value = 35
    processingStatus.value = copy.value.statusProcessing
    const blob = await extractPDFPages(selectedFile.value, pageRanges.value)

    processingProgress.value = 100
    processingStatus.value = copy.value.statusDone
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'split',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : copy.value.errorFailed
  } finally {
    isProcessing.value = false
    processingProgress.value = 0
    processingStatus.value = ''
  }
}

const splitInCloud = async () => {
  if (!selectedFile.value) return

  isProcessing.value = true
  errorMessage.value = ''

  try {
    const ranges = pageRanges.value.split(',').map((range) => {
      const parts = range.trim().split('-').map(Number)
      return parts.length === 1 ? [parts[0], parts[0]] : parts
    })

    const blob = await processInCloud(selectedFile.value, (fileId) =>
      fileAPI.splitPDF(fileId, ranges)
    )

    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'split',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : copy.value.errorCloudFailed
  } finally {
    isProcessing.value = false
  }
}

const downloadResult = () => {
  if (!resultUrl.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = `split-${new Date().toISOString().slice(0, 10)}.pdf`
  link.click()
  showSuccessModal.value = false
}

onUnmounted(() => {
  destroyWorker()
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-cyan-50 via-white to-sky-50 dark:from-slate-950 dark:via-slate-950 dark:to-cyan-950/20">
    <ToolHeader
      :title="t('tools.split.title')"
      :subtitle="t('tools.split.desc')"
      :badge="copy.badge"
      accent="cyan"
    >
      <template #badgeIcon>
        <FileText class="h-4 w-4" />
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
      <div
        v-if="errorMessage"
        class="mb-4 rounded-lg bg-error-light p-4 text-error-dark dark:bg-error/20 dark:text-error"
      >
        {{ errorMessage }}
      </div>

      <DragDropZone
        v-if="!selectedFile"
        accept="pdf"
        :multiple="false"
        @files-selected="handleFilesSelected"
        @error="handleError"
      />

      <div
        v-else
        class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]"
      >
        <div class="space-y-6">
          <FilePreview
            :file="selectedFile"
            @remove="clearAll"
            @preview="handlePreview"
          />

          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-cyan-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-500">
                  {{ copy.setupLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.setupTitle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.setupDesc }}
                </p>
              </div>

              <CloudToggle v-model="useCloud" />

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.rangeLabel }}
                </label>
                <div class="flex gap-2">
                  <input
                    v-model="pageRanges"
                    type="text"
                    :placeholder="copy.rangePlaceholder"
                    :class="[
                      'flex-1 rounded-2xl border px-4 py-3 focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/10 dark:bg-slate-900 dark:text-white',
                      useVisualSelector ? 'border-primary bg-primary/5' : 'border-slate-300 dark:border-slate-700',
                    ]"
                  >
                  <Button
                    variant="outline"
                    size="md"
                    @click="openPageSelector"
                  >
                    {{ copy.visualSelect }}
                  </Button>
                </div>
                <p class="mt-3 text-xs leading-6 text-slate-500 dark:text-slate-400">
                  {{ copy.rangeHint }}
                </p>
              </div>
            </div>
          </Card>
        </div>

        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-cyan-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-5">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-500">
                {{ copy.actionLabel }}
              </p>
              <h3 class="mt-2 text-xl font-semibold text-slate-900 dark:text-white">
                {{ copy.actionTitle }}
              </h3>
            </div>

            <div class="rounded-[24px] border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/40">
              <ul class="space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li
                  v-for="tip in copy.actionTips"
                  :key="tip"
                >
                  {{ tip }}
                </li>
              </ul>
            </div>

            <ProgressBar
              v-if="isProcessing"
              :progress="processingProgress"
              :label="processingStatus"
              variant="primary"
              size="md"
            />

            <Button
              variant="primary"
              size="lg"
              :loading="isProcessing"
              full-width
              @click="extractPages"
            >
              {{ isProcessing ? t('common.processing') : copy.extract }}
            </Button>
          </div>
        </Card>
      </div>

      <Modal
        v-model="showPageSelector"
        :title="copy.modalTitle"
        size="xl"
      >
        <PageSelector
          v-if="selectedFile && showPageSelector"
          :file="selectedFile"
          :total-pages="totalPages"
          @confirm="handlePageSelect"
          @cancel="handlePageSelectCancel"
        />
      </Modal>

      <Modal
        v-model="showPDFViewer"
        title=""
        size="full"
      >
        <PDFViewer
          v-if="selectedFile && showPDFViewer"
          :file="selectedFile"
          @close="handleCloseViewer"
        />
      </Modal>

      <Modal
        v-model="showSuccessModal"
        :title="copy.successTitle"
        size="md"
      >
        <div class="text-center">
          <p class="mb-6 text-gray-600 dark:text-gray-300">
            {{ copy.successMessage }}
          </p>
          <Button
            variant="primary"
            size="lg"
            full-width
            @click="downloadResult"
          >
            {{ t('common.download') }}
          </Button>
        </div>
      </Modal>
    </section>
  </div>
</template>
