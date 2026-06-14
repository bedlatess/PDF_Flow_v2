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
import {
  compressPDF,
  estimateCompressionRatio,
  type CompressionQuality,
  type CompressionResult,
} from '@/utils/pdf/compress'
import { memoryManager } from '@/utils/memory-manager'
import { usePDFWorker } from '@/composables/usePDFWorker'
import { useCloudProcessing } from '@/composables/useCloudProcessing'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { fileAPI } from '@/services/api'
import CloudToggle from '@/components/common/CloudToggle.vue'
import { historyManager } from '@/utils/history-manager'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
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
const selectedQuality = ref<CompressionQuality>('medium')
const useCloud = ref(false)
const showSuccessModal = ref(false)
const showPDFViewer = ref(false)
const resultUrl = ref('')
const resultFileName = ref('')
const compressionResult = ref<CompressionResult | null>(null)

const { destroyWorker } = usePDFWorker()
const { cloudProgress, cloudPhase, processInCloud } = useCloudProcessing()
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

const copy = computed<ToolPageCopy>(() => tm('tools.compress.page') as ToolPageCopy)
const selectedFile = computed(() => selectedFiles.value[0] || null)

const formatMB = (value: number) => `${(Math.max(value, 0) / (1024 * 1024)).toFixed(2)} MB`

const estimatedRatio = computed(() => {
  if (!selectedFile.value) return 0
  return estimateCompressionRatio(selectedFile.value.size, selectedQuality.value)
})

const estimatedSize = computed(() => {
  if (!selectedFile.value) return 0
  const ratio = estimatedRatio.value / 100
  return selectedFile.value.size * (1 - ratio)
})

const estimatedStats = computed(() => {
  if (!selectedFile.value) return null

  const originalSize = selectedFile.value.size
  const estimatedOutputSize = estimatedSize.value
  const savedSize = Math.max(originalSize - estimatedOutputSize, 0)

  return {
    originalSize: formatMB(originalSize),
    estimatedOutputSize: formatMB(estimatedOutputSize),
    savedSize: formatMB(savedSize),
    ratio: `${estimatedRatio.value.toFixed(0)}%`,
  }
})

const resultStats = computed(() => {
  if (!compressionResult.value) return null

  const originalSize = compressionResult.value.originalSize
  const compressedSize = compressionResult.value.compressedSize
  const savedSize = Math.max(originalSize - compressedSize, 0)
  const ratio = originalSize > 0 ? ((savedSize / originalSize) * 100) : 0

  return {
    originalSize: formatMB(originalSize),
    compressedSize: formatMB(compressedSize),
    savedSize: formatMB(savedSize),
    ratio: `${ratio.toFixed(1)}%`,
    optimized: compressionResult.value.optimized,
  }
})

const handleFilesSelected = (files: File[]) => {
  setSelectedFiles(files.slice(0, 1))
  useCloud.value = shouldPreferCloudProcessing(files.slice(0, 1), userStore.canUseCloudFeatures)
  clearFileError()
  resetProcessing()
  compressionResult.value = null
}

watch(selectedQuality, () => {
  compressionResult.value = null
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
})

const handleError = (message: string) => {
  setFileError(message)
}

const clearAll = () => {
  clearSelection()
  useCloud.value = false
  compressionResult.value = null
  resetProcessing()
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const setResultFileName = () => {
  if (!selectedFile.value) return
  const timestamp = new Date().toISOString().slice(0, 10)
  const originalName = selectedFile.value.name.replace(/\.pdf$/i, '')
  resultFileName.value = `${originalName}-compressed-${timestamp}.pdf`
}

const storeHistory = (result: CompressionResult) => {
  if (!selectedFile.value) return
  historyManager.addHistory({
    type: 'compress',
    fileName: selectedFile.value.name,
    fileSize: result.originalSize,
    resultSize: result.compressedSize,
  })
}

const compressFile = async () => {
  if (!selectedFile.value) return

  if (useCloud.value) {
    await compressInCloud()
    return
  }

  startProcessing(copy.value.statusPreparing)

  try {
    updateProcessing(30, copy.value.statusProcessing)

    const result = await compressPDF(selectedFile.value, {
      quality: selectedQuality.value,
      removeMetadata: true,
    })

    updateProcessing(100, copy.value.statusDone)

    compressionResult.value = result
    resultUrl.value = memoryManager.createTemporaryURL(result.compressedBlob)
    setResultFileName()
    storeHistory(result)
    showSuccessModal.value = true
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const compressInCloud = async () => {
  if (!selectedFile.value) return

  startProcessing(copy.value.statusPreparing)

  try {
    const blob = await processInCloud(selectedFile.value, (fileId) =>
      fileAPI.compressPDF(fileId, selectedQuality.value)
    )

    const originalSize = selectedFile.value.size
    const optimized = blob.size < originalSize
    const outputBlob = optimized ? blob : selectedFile.value
    const result: CompressionResult = {
      originalSize,
      compressedSize: optimized ? blob.size : originalSize,
      compressionRatio: optimized && originalSize > 0 ? (1 - blob.size / originalSize) * 100 : 0,
      compressedBlob: outputBlob,
      optimized,
    }

    resultUrl.value = memoryManager.createTemporaryURL(outputBlob)
    compressionResult.value = result
    setResultFileName()
    storeHistory(result)
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
  link.download = resultFileName.value
  link.click()
  showSuccessModal.value = false
}

const startNew = () => {
  showSuccessModal.value = false
  clearAll()
}

const handlePreview = () => {
  showPDFViewer.value = true
}

const handleCloseViewer = () => {
  showPDFViewer.value = false
}

const estimateStats = computed(() => [
  { label: copy.value.originalSize, value: estimatedStats.value?.originalSize },
  { label: copy.value.estimatedCompression, value: estimatedStats.value?.ratio },
  { label: copy.value.estimatedSize, value: estimatedStats.value?.estimatedOutputSize },
])

const workspaceError = computed(() => fileError.value || processingError.value)

onUnmounted(() => {
  destroyWorker()
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <ToolPageShell
      :title="t('tools.compress.title')"
      :subtitle="t('tools.compress.desc')"
      :badge="copy.badge"
      accent="emerald"
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
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
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

              <div class="rounded-md border border-emerald-100 bg-emerald-50/80 p-4 text-sm leading-6 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-200">
                <p class="font-semibold">
                  {{ copy.freeModeLabel || 'Free mode' }}
                </p>
              </div>

              <div class="space-y-3">
                <button
                  v-for="option in copy.qualityOptions"
                  :key="option.value"
                  :class="[
                    'w-full rounded-md border-2 p-4 text-left transition-all',
                    selectedQuality === option.value
                      ? 'border-primary bg-primary/10 shadow-sm'
                      : 'border-slate-200 bg-slate-50/70 hover:border-primary/40 dark:border-slate-700 dark:bg-slate-950/40',
                  ]"
                  @click="selectedQuality = option.value"
                >
                  <p class="font-semibold text-slate-900 dark:text-white">
                    {{ option.label }}
                  </p>
                  <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    {{ option.description }}
                  </p>
                </button>
              </div>
            </div>
          </section>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <ToolActionPanel
            :label="copy.resultLabel"
            :title="copy.resultTitle"
            :description="copy.estimateHint"
            accent="emerald"
            :stats="estimateStats"
            :show-progress="isProcessing"
            :progress="useCloud ? cloudProgress : processingProgress"
            :progress-label="useCloud ? t(`cloud.${cloudPhase}`, t('common.processing')) : processingStatus"
            :action-label="isProcessing ? t('common.processing') : copy.action"
            :loading="isProcessing"
            @action="compressFile"
          >
            <template #details>
            <div
              v-if="resultStats"
              class="rounded-md border p-5 dark:border-slate-800"
              :class="resultStats.optimized ? 'border-emerald-200 bg-emerald-50/80 dark:bg-emerald-500/10' : 'border-amber-200 bg-amber-50/80 dark:bg-amber-500/10'"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                {{ copy.actualLabel }}
              </p>
              <p class="mt-2 font-semibold text-slate-900 dark:text-white">
                {{ resultStats.optimized ? copy.optimizedDesc : copy.noSavingsTitle }}
              </p>
              <p
                v-if="!resultStats.optimized"
                class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300"
              >
                {{ copy.noSavingsDesc }}
              </p>
            </div>

            <div
              v-if="resultStats || estimatedStats"
              class="rounded-md border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/40"
            >
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p class="text-slate-500 dark:text-slate-400">{{ copy.originalSize }}</p>
                  <p class="mt-1 font-semibold text-slate-900 dark:text-white">
                    {{ resultStats?.originalSize || estimatedStats?.originalSize }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-500 dark:text-slate-400">{{ copy.outputSize }}</p>
                  <p class="mt-1 font-semibold text-slate-900 dark:text-white">
                    {{ resultStats?.compressedSize || estimatedStats?.estimatedOutputSize }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-500 dark:text-slate-400">{{ copy.savedSize }}</p>
                  <p
                    class="mt-1 font-semibold"
                    :class="resultStats && !resultStats.optimized ? 'text-amber-600' : 'text-emerald-600'"
                  >
                    {{ resultStats?.savedSize || estimatedStats?.savedSize }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-500 dark:text-slate-400">{{ copy.ratio }}</p>
                  <p
                    class="mt-1 font-semibold"
                    :class="resultStats && !resultStats.optimized ? 'text-amber-600' : 'text-primary'"
                  >
                    {{ resultStats?.ratio || estimatedStats?.ratio }}
                  </p>
                </div>
              </div>
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
        :primary-label="t('common.download')"
        :secondary-label="copy.compressMore"
        size="md"
        @primary="downloadResult"
        @secondary="startNew"
      >
          <div
            v-if="resultStats"
            class="rounded-md border border-slate-200 bg-slate-50/80 p-5 text-left dark:border-slate-800 dark:bg-slate-950/40"
          >
            <p class="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
              {{ resultStats.optimized ? copy.optimizedDesc : copy.noSavingsDesc }}
            </p>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p class="text-slate-500 dark:text-slate-400">{{ copy.originalSize }}</p>
                <p class="mt-1 font-semibold text-slate-900 dark:text-white">
                  {{ resultStats.originalSize }}
                </p>
              </div>
              <div>
                <p class="text-slate-500 dark:text-slate-400">{{ copy.outputSize }}</p>
                <p class="mt-1 font-semibold text-slate-900 dark:text-white">
                  {{ resultStats.compressedSize }}
                </p>
              </div>
              <div>
                <p class="text-slate-500 dark:text-slate-400">{{ copy.savedSize }}</p>
                <p
                  class="mt-1 font-semibold"
                  :class="resultStats.optimized ? 'text-emerald-600' : 'text-amber-600'"
                >
                  {{ resultStats.savedSize }}
                </p>
              </div>
              <div>
                <p class="text-slate-500 dark:text-slate-400">{{ copy.ratio }}</p>
                <p
                  class="mt-1 font-semibold"
                  :class="resultStats.optimized ? 'text-primary' : 'text-amber-600'"
                >
                  {{ resultStats.ratio }}
                </p>
              </div>
            </div>
          </div>
      </ToolResultPanel>
  </ToolPageShell>
</template>
