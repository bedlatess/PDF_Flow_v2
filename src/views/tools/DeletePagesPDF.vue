<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Scissors } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import PageSelector from '@/components/pdf/PageSelector.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { deletePDFPages, parsePageRanges } from '@/utils/pdf/split'
import { memoryManager } from '@/utils/memory-manager'
import { historyManager } from '@/utils/history-manager'

const { t, tm } = useI18n()

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
const selectedFromVisual = ref(false)
const showPageSelector = ref(false)
const showPDFViewer = ref(false)
const showSuccessModal = ref(false)
const resultUrl = ref('')

const {
  isProcessing,
  processingProgress,
  processingStatus,
  processingError,
  startProcessing,
  updateProcessing,
  resetProcessing,
  failProcessing,
  clearProcessingError,
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => ({
  ...(tm('tools.deletePages.page') as ToolPageCopy),
  rangeLabel: t('tools.deletePages.page.rangeLabel', { count: totalPages.value }),
}))
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)

const selectedPageNumbers = computed(() =>
  totalPages.value > 0 ? parsePageRanges(pageRanges.value, totalPages.value) : []
)

const remainingPages = computed(() =>
  Math.max(totalPages.value - selectedPageNumbers.value.length, 0)
)

const actionStats = computed(() => [
  { label: copy.value.removeLabel, value: selectedPageNumbers.value.length },
  { label: copy.value.keepLabel, value: remainingPages.value },
])

const clearResult = () => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const handleFilesSelected = async (files: File[]) => {
  try {
    clearResult()
    setSelectedFiles(files.slice(0, 1))
    totalPages.value = await getPDFPageCount(files[0])
    pageRanges.value = ''
    selectedFromVisual.value = false
    clearFileError()
    resetProcessing()
  } catch (error) {
    clearSelection()
    totalPages.value = 0
    setFileError(error instanceof Error ? error.message : copy.value.errorLoad)
  }
}

const handleError = (message: string) => {
  setFileError(message)
}

const clearAll = () => {
  clearSelection()
  totalPages.value = 0
  pageRanges.value = ''
  selectedFromVisual.value = false
  showPageSelector.value = false
  showPDFViewer.value = false
  resetProcessing()
  clearResult()
}

const formatPagesAsRanges = (pages: number[]) => {
  if (pages.length === 0) return ''

  const sorted = [...pages].sort((a, b) => a - b)
  const ranges: string[] = []
  let start = sorted[0]
  let end = sorted[0]

  for (let index = 1; index <= sorted.length; index += 1) {
    if (index < sorted.length && sorted[index] === end + 1) {
      end = sorted[index]
      continue
    }

    ranges.push(start === end ? `${start}` : `${start}-${end}`)

    if (index < sorted.length) {
      start = sorted[index]
      end = sorted[index]
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
  selectedFromVisual.value = true
  showPageSelector.value = false
  clearProcessingError()
}

const validateSelection = () => {
  if (!pageRanges.value.trim()) {
    failProcessing(copy.value.errorNoRange)
    return false
  }

  if (selectedPageNumbers.value.length === 0) {
    failProcessing(copy.value.errorNoPages)
    return false
  }

  if (selectedPageNumbers.value.length >= totalPages.value) {
    failProcessing(copy.value.errorAllPages)
    return false
  }

  return true
}

const deletePages = async () => {
  if (!selectedFile.value || !validateSelection()) return

  startProcessing(copy.value.statusPreparing)
  clearResult()

  try {
    updateProcessing(45, copy.value.statusProcessing)
    const blob = await deletePDFPages(selectedFile.value, selectedPageNumbers.value)

    updateProcessing(100, copy.value.statusDone)
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'deletePages',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorFailed)
  } finally {
    isProcessing.value = false
    processingProgress.value = 0
    processingStatus.value = ''
  }
}

const downloadResult = () => {
  if (!resultUrl.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = `pages-removed-${new Date().toISOString().slice(0, 10)}.pdf`
  link.click()
  showSuccessModal.value = false
}

onUnmounted(clearResult)
</script>

<template>
  <ToolPageShell
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="pink"
    width="md"
  >

      <template #badgeIcon>
        <Scissors class="h-4 w-4" />
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
            @preview="showPDFViewer = true"
          />

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-rose-600 dark:text-rose-300">
                  {{ copy.setupLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ copy.setupTitle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.setupDesc }}
                </p>
              </div>

              <div>
                <label
                  for="delete-pages-range"
                  class="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                >
                  {{ copy.rangeLabel }}
                </label>
                <div class="flex gap-2">
                  <input
                    id="delete-pages-range"
                    v-model="pageRanges"
                    type="text"
                    :placeholder="copy.rangePlaceholder"
                    :class="[
                      'flex-1 rounded-md border px-4 py-3 focus:border-rose-500 focus:outline-none focus:ring-4 focus:ring-rose-500/10 dark:bg-slate-900 dark:text-white',
                      selectedFromVisual ? 'border-rose-500 bg-rose-50/70 dark:bg-rose-500/10' : 'border-slate-300 dark:border-slate-700',
                    ]"
                    @input="selectedFromVisual = false"
                  >
                  <Button
                    variant="outline"
                    size="md"
                    @click="showPageSelector = true"
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
            :label="copy.outputLabel"
            :title="copy.outputTitle"
            accent="amber"
            :stats="actionStats"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.statusProcessing : copy.delete"
            action-variant="danger"
            :loading="isProcessing"
            @action="deletePages"
          >
            <template #details>
            <div class="rounded-md border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/40">
              <ul class="space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li
                  v-for="tip in copy.outputTips"
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
          @cancel="showPageSelector = false"
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
          @close="showPDFViewer = false"
        />
      </Modal>

      <ToolResultPanel
        v-model="showSuccessModal"
        :title="copy.successTitle"
        :message="copy.successMessage"
        :primary-label="copy.download"
        size="md"
        @primary="downloadResult"
      >
      </ToolResultPanel>
  </ToolPageShell>
</template>
