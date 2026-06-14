<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import PageSelector from '@/components/pdf/PageSelector.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import CloudToggle from '@/components/common/CloudToggle.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { extractPDFPages } from '@/utils/pdf/split'
import { memoryManager } from '@/utils/memory-manager'
import { usePDFWorker } from '@/composables/usePDFWorker'
import { useCloudProcessing } from '@/composables/useCloudProcessing'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { fileAPI } from '@/services/api'
import { historyManager } from '@/utils/history-manager'
import { useUserStore } from '@/stores/user'
import { shouldPreferCloudProcessing } from '@/utils/cloud-recommendation'

const { t, tm } = useI18n()
const userStore = useUserStore()

type ToolPageCopy = Record<string, any>

const {
  selectedItems: selectedFiles,
  fileError,
  setItems: setSelectedFiles,
  clearSelection,
  setFileError,
  clearFileError,
} = useToolFileSelection<File>()
const totalPages = ref(0)
const pageRanges = ref('')
const useVisualSelector = ref(false)
const useCloud = ref(false)
const showPageSelector = ref(false)
const showPDFViewer = ref(false)
const showSuccessModal = ref(false)
const resultUrl = ref('')

const { destroyWorker } = usePDFWorker()
const { processInCloud } = useCloudProcessing()
const {
  isProcessing,
  processingProgress,
  processingStatus,
  processingError,
  startProcessing,
  updateProcessing,
  resetProcessing,
  failProcessing,
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => ({
  ...(tm('tools.split.page') as ToolPageCopy),
  rangeLabel: t('tools.split.page.rangeLabel', { count: totalPages.value }),
}))
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)

const handleFilesSelected = async (files: File[]) => {
  try {
    setSelectedFiles(files.slice(0, 1))
    useCloud.value = shouldPreferCloudProcessing(files.slice(0, 1), userStore.canUseCloudFeatures)
    totalPages.value = await getPDFPageCount(files[0])
    clearFileError()
    resetProcessing()
  } catch (error) {
    clearSelection()
    setFileError(error instanceof Error ? error.message : copy.value.errorLoad)
  }
}

const handleError = (message: string) => {
  setFileError(message)
}

const clearAll = () => {
  clearSelection()
  useCloud.value = false
  totalPages.value = 0
  pageRanges.value = ''
  useVisualSelector.value = false
  showPageSelector.value = false
  resetProcessing()
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
    failProcessing(copy.value.errorNoPages)
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
    failProcessing(copy.value.errorNoRange)
    return
  }

  if (useCloud.value) {
    await splitInCloud()
    return
  }

  startProcessing(copy.value.statusPreparing)

  try {
    updateProcessing(35, copy.value.statusProcessing)
    const blob = await extractPDFPages(selectedFile.value, pageRanges.value)

    updateProcessing(100, copy.value.statusDone)
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'split',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const splitInCloud = async () => {
  if (!selectedFile.value) return

  startProcessing(copy.value.statusPreparing)

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
    failProcessing(error instanceof Error ? error.message : copy.value.errorCloudFailed)
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
  <ToolPageShell
      :title="t('tools.split.title')"
      :subtitle="t('tools.split.desc')"
      :badge="copy.badge"
      accent="cyan"
    width="md"
  >

      <template #badgeIcon>
        <FileText class="h-4 w-4" />
      </template>

      <ToolWorkspace
        :error-message="workspaceError"
        layout="wide-secondary"
      >
        <template
          v-if="!selectedFile"
          #upload
        >
          <DragDropZone
            accept="pdf"
            :multiple="false"
            @files-selected="handleFilesSelected"
            @error="handleError"
          />
        </template>

        <template
          v-if="selectedFile"
          #primary
        >
          <FilePreview
            :file="selectedFile"
            @remove="clearAll"
            @preview="handlePreview"
          />

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-600 dark:text-cyan-300">
                  {{ copy.setupLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
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
                      'flex-1 rounded-md border px-4 py-3 focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/10 dark:bg-slate-900 dark:text-white',
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
          </section>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <ToolActionPanel
            :label="copy.actionLabel"
            :title="copy.actionTitle"
            accent="blue"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? t('common.processing') : copy.extract"
            :loading="isProcessing"
            @action="extractPages"
          >
            <CloudToggle v-model="useCloud" />
            <template #details>
            <div class="rounded-md border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/40">
              <ul class="space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li
                  v-for="tip in copy.actionTips"
                  :key="tip"
                >
                  {{ tip }}
                </li>
              </ul>
            </div>
            </template>
          </ToolActionPanel>
        </template>
      </ToolWorkspace>

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

      <ToolResultPanel
        v-model="showSuccessModal"
        :title="copy.successTitle"
        :message="copy.successMessage"
        :primary-label="t('common.download')"
        size="md"
        @primary="downloadResult"
      >
      </ToolResultPanel>
  </ToolPageShell>
</template>
