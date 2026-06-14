<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Hash } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import Modal from '@/components/common/Modal.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { addPageNumbers, type PageNumberPosition } from '@/utils/pdf/pageNumbers'
import { memoryManager } from '@/utils/memory-manager'
import { historyManager } from '@/utils/history-manager'

const { tm } = useI18n()

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
const position = ref<PageNumberPosition>('bottom-center')
const startNumber = ref(1)
const startOnPage = ref(1)
const prefix = ref('')
const suffix = ref('')
const includeTotal = ref(false)
const fontSize = ref(12)
const opacity = ref(0.9)
const pageNumberColor = ref('#3f3f46')

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
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => tm('tools.pageNumbers.page') as ToolPageCopy)
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)

watch(copy, (nextCopy, previousCopy) => {
  const previousPrefix = previousCopy?.placeholders?.defaultPrefix ?? ''
  const previousSuffix = previousCopy?.placeholders?.defaultSuffix ?? ''
  if (!selectedFile.value && (!prefix.value || prefix.value === previousPrefix) && (!suffix.value || suffix.value === previousSuffix)) {
    prefix.value = nextCopy.placeholders?.defaultPrefix ?? ''
    suffix.value = nextCopy.placeholders?.defaultSuffix ?? ''
  }
}, { immediate: true })
const stampedPageCount = computed(() =>
  Math.max(totalPages.value - startOnPage.value + 1, 0)
)

const sampleText = computed(() => {
  const number = startNumber.value || 1
  return includeTotal.value
    ? `${prefix.value}${number} / ${stampedPageCount.value || totalPages.value || 1}${suffix.value}`
    : `${prefix.value}${number}${suffix.value}`
})

const selectedPositionLabel = computed(() =>
  copy.value.positions.find((item) => item.value === position.value)?.label || ''
)
const actionStats = computed(() => [
  { label: copy.value.pages ?? 'Pages', value: totalPages.value || '-' },
  { label: copy.value.startOnPage, value: startOnPage.value },
])

const handleFilesSelected = async (files: File[]) => {
  try {
    clearResult()
    setSelectedFiles(files.slice(0, 1))
    totalPages.value = await getPDFPageCount(files[0])
    startOnPage.value = Math.min(startOnPage.value, totalPages.value)
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

const clearResult = () => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const clearAll = () => {
  clearSelection()
  totalPages.value = 0
  showPDFViewer.value = false
  resetProcessing()
  clearResult()
}

const hexToRgb = (hex: string): { r: number; g: number; b: number } => {
  const normalized = hex.replace('#', '')
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  }
}

const validateSettings = () => {
  if (startOnPage.value > totalPages.value) {
    failProcessing(copy.value.errorStartPage)
    return false
  }

  return true
}

const applyPageNumbers = async () => {
  if (!selectedFile.value || !validateSettings()) return

  startProcessing(copy.value.statusPreparing)
  clearResult()

  try {
    updateProcessing(45, copy.value.statusProcessing)
    const blob = await addPageNumbers(selectedFile.value, {
      startNumber: startNumber.value,
      startOnPage: startOnPage.value,
      prefix: prefix.value,
      suffix: suffix.value,
      includeTotal: includeTotal.value,
      fontSize: fontSize.value,
      opacity: opacity.value,
      color: hexToRgb(pageNumberColor.value),
      position: position.value,
    })

    updateProcessing(100, copy.value.statusDone)
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'pageNumbers',
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

const downloadResult = () => {
  if (!resultUrl.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = `numbered-${new Date().toISOString().slice(0, 10)}.pdf`
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
      accent="blue"
    width="md"
  >

      <template #badgeIcon>
        <Hash class="h-4 w-4" />
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
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
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
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.position }}
                </label>
                <div class="grid gap-2 sm:grid-cols-2">
                  <button
                    v-for="option in copy.positions"
                    :key="option.value"
                    type="button"
                    :class="[
                      'rounded-md border px-4 py-3 text-left text-sm font-semibold transition',
                      position === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-sm dark:border-blue-300 dark:bg-blue-500/10 dark:text-blue-100'
                        : 'border-slate-200 bg-white/70 text-slate-600 hover:border-blue-200 dark:border-slate-700 dark:bg-slate-950/30 dark:text-slate-300',
                    ]"
                    @click="position = option.value"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.startNumber }}</span>
                  <input
                    v-model.number="startNumber"
                    type="number"
                    min="0"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.startOnPage }}</span>
                  <input
                    v-model.number="startOnPage"
                    type="number"
                    min="1"
                    :max="totalPages"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.prefix }}</span>
                  <input
                    v-model="prefix"
                    type="text"
                    :placeholder="copy.placeholders.prefix"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.suffix }}</span>
                  <input
                    v-model="suffix"
                    type="text"
                    :placeholder="copy.placeholders.suffix"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
              </div>

              <label class="flex items-center gap-3 rounded-md border border-slate-200 bg-slate-50/70 px-4 py-3 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200">
                <input
                  v-model="includeTotal"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                >
                {{ copy.includeTotal }}
              </label>

              <div class="grid gap-4 sm:grid-cols-3">
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.fontSize }}</span>
                  <input
                    v-model.number="fontSize"
                    type="number"
                    min="8"
                    max="36"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.opacity }}</span>
                  <input
                    v-model.number="opacity"
                    type="number"
                    min="0.1"
                    max="1"
                    step="0.1"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.color }}</span>
                  <input
                    v-model="pageNumberColor"
                    type="color"
                    class="h-[50px] w-full rounded-md border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-900"
                  >
                </label>
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
            accent="blue"
            :stats="actionStats"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.statusProcessing : copy.generate"
            :loading="isProcessing"
            @action="applyPageNumbers"
          >
            <template #details>
            <div class="rounded-lg border border-blue-100 bg-gradient-to-br from-blue-50 to-cyan-50 p-5 dark:border-blue-500/20 dark:from-blue-500/10 dark:to-cyan-500/10">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-200">
                {{ copy.sample }}
              </p>
              <div class="mt-4 rounded-[22px] border border-white/80 bg-white/85 p-5 shadow-inner dark:border-white/10 dark:bg-slate-950/45">
                <div class="relative mx-auto aspect-[3/4] max-w-[220px] rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
                  <span
                    :class="[
                      'absolute rounded-full bg-white/80 px-2 py-1 text-center font-semibold shadow-sm dark:bg-slate-800/90',
                      position.includes('bottom') ? 'bottom-4' : 'top-4',
                      position.endsWith('left') ? 'left-4' : position.endsWith('right') ? 'right-4' : 'left-1/2 -translate-x-1/2',
                    ]"
                    :style="{ color: pageNumberColor, opacity, fontSize: `${Math.min(fontSize, 18)}px` }"
                  >
                    {{ sampleText }}
                  </span>
                </div>
              </div>
              <p class="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ selectedPositionLabel }} - {{ stampedPageCount }} / {{ totalPages }} {{ copy.stampedSummary }}
              </p>
            </div>

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
