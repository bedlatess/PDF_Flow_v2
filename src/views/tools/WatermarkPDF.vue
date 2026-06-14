<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Modal from '@/components/common/Modal.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { memoryManager } from '@/utils/memory-manager'
import { historyManager } from '@/utils/history-manager'
import { addWatermark, type WatermarkPosition } from '@/utils/pdf/watermark'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'

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
const watermarkText = ref('CONFIDENTIAL')
const opacity = ref(0.3)
const rotation = ref(45)
const fontSize = ref(40)
const position = ref<WatermarkPosition>('center')
const watermarkColor = ref('#808080')

const showSuccessModal = ref(false)
const showPDFViewer = ref(false)
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

const copy = computed<ToolPageCopy>(() => tm('tools.watermark.page') as ToolPageCopy)
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)

const clearResult = () => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
  showSuccessModal.value = false
}

watch(copy, (nextCopy, previousCopy) => {
  const previousDefault = previousCopy?.defaultText ?? ''
  const trimmed = watermarkText.value.trim()
  if (!trimmed || trimmed === previousDefault) {
    watermarkText.value = nextCopy.defaultText
  }
}, { immediate: true })
const handleFilesSelected = (files: File[]) => {
  setSelectedFiles(files.slice(0, 1))
  clearFileError()
  resetProcessing()
  clearResult()
}

const handleError = (message: string) => {
  setFileError(message)
}

const clearAll = () => {
  clearSelection()
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

const applyWatermark = async () => {
  if (!selectedFile.value) return

  if (!watermarkText.value.trim()) {
    failProcessing(copy.value.errorNoText)
    return
  }

  startProcessing(copy.value.processing)
  updateProcessing(20, copy.value.processing)

  try {
    updateProcessing(50, copy.value.processing)
    const blob = await addWatermark(selectedFile.value, {
      text: watermarkText.value,
      opacity: opacity.value,
      rotation: rotation.value,
      fontSize: fontSize.value,
      color: hexToRgb(watermarkColor.value),
      position: position.value,
    })

    updateProcessing(100, copy.value.done)
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'watermark',
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
  link.download = `watermarked-${new Date().toISOString().slice(0, 10)}.pdf`
  link.click()
  showSuccessModal.value = false
}

const handlePreview = () => {
  showPDFViewer.value = true
}

const handleCloseViewer = () => {
  showPDFViewer.value = false
}

onUnmounted(() => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <ToolPageShell
      :title="t('tools.watermark.title')"
      :subtitle="t('tools.watermark.desc')"
      :badge="copy.badge"
      accent="pink"
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
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-fuchsia-600 dark:text-fuchsia-300">
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
                  for="watermark-text"
                  class="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                >
                  {{ copy.text }}
                </label>
                <input
                  id="watermark-text"
                  v-model="watermarkText"
                  type="text"
                  :placeholder="copy.placeholder"
                  class="w-full rounded-md border border-slate-300 px-4 py-3 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.position }}
                </label>
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <button
                    v-for="option in copy.positions"
                    :key="option.value"
                    :class="[
                      'rounded-[18px] border-2 px-3 py-3 text-sm font-medium transition-all',
                      position === option.value
                        ? 'border-primary bg-primary/10 text-primary shadow-sm'
                        : 'border-slate-200 bg-slate-50/70 text-slate-700 hover:border-primary/40 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-300',
                    ]"
                    @click="position = option.value"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.opacity }}: {{ Math.round(opacity * 100) }}%
                </label>
                <input
                  v-model.number="opacity"
                  type="range"
                  min="0.05"
                  max="1"
                  step="0.05"
                  class="w-full accent-primary"
                >
              </div>

              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                    {{ copy.rotation }}: {{ rotation }} deg
                  </label>
                  <input
                    v-model.number="rotation"
                    type="range"
                    min="0"
                    max="90"
                    step="5"
                    class="w-full accent-primary"
                  >
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                    {{ copy.fontSize }}: {{ fontSize }}
                  </label>
                  <input
                    v-model.number="fontSize"
                    type="range"
                    min="12"
                    max="100"
                    step="2"
                    class="w-full accent-primary"
                  >
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.color }}
                </label>
                <input
                  v-model="watermarkColor"
                  type="color"
                  class="h-11 w-24 cursor-pointer rounded-md border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900"
                >
              </div>
            </div>
          </section>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <div class="rounded-lg border border-emerald-100 bg-emerald-50/80 p-5 text-sm leading-6 text-emerald-800 shadow-sm dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-300 dark:shadow-none">
            <p class="font-semibold">
              {{ copy.localTitle }}
            </p>
            <p class="mt-2">
              {{ copy.localDesc }}
            </p>
          </div>

          <ToolActionPanel
            :label="copy.outputLabel"
            :title="copy.outputTitle"
            accent="purple"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? t('common.processing') : copy.action"
            :loading="isProcessing"
            @action="applyWatermark"
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
