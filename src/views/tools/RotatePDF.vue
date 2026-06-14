<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Modal from '@/components/common/Modal.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import CloudToggle from '@/components/common/CloudToggle.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { memoryManager } from '@/utils/memory-manager'
import { usePDFWorker } from '@/composables/usePDFWorker'
import { useCloudProcessing } from '@/composables/useCloudProcessing'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { fileAPI } from '@/services/api'
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
const selectedAngle = ref<90 | 180 | 270>(90)
const useCloud = ref(false)
const showSuccessModal = ref(false)
const showPDFViewer = ref(false)
const resultUrl = ref('')

const { submitTask, getTask, waitForTask, destroyWorker } = usePDFWorker()
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

const copy = computed<ToolPageCopy>(() => tm('tools.rotate.page') as ToolPageCopy)
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)

const handleFilesSelected = (files: File[]) => {
  setSelectedFiles(files.slice(0, 1))
  useCloud.value = shouldPreferCloudProcessing(files.slice(0, 1), userStore.canUseCloudFeatures)
  clearFileError()
  resetProcessing()
}

const handleError = (message: string) => {
  setFileError(message)
}

const clearAll = () => {
  clearSelection()
  useCloud.value = false
  resetProcessing()
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const rotatePages = async () => {
  if (!selectedFile.value) return

  if (useCloud.value) {
    await rotateInCloud()
    return
  }

  startProcessing(copy.value.statusPreparing)

  try {
    updateProcessing(0, copy.value.statusProcessing)
    const taskId = await submitTask('rotate', {
      file: selectedFile.value,
      options: { angle: selectedAngle.value },
    })

    const progressInterval = setInterval(() => {
      const task = getTask(taskId)
      if (task) {
        processingProgress.value = task.progress
        if (task.progress < 100) {
          processingStatus.value = copy.value.statusProgress.replace('{progress}', String(Math.round(task.progress)))
        }
      }
    }, 100)

    const blob = await waitForTask(taskId) as Blob
    clearInterval(progressInterval)

    updateProcessing(100, copy.value.statusDone)
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'rotate',
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

const rotateInCloud = async () => {
  if (!selectedFile.value) return

  startProcessing(copy.value.statusPreparing)

  try {
    const blob = await processInCloud(selectedFile.value, (fileId) =>
      fileAPI.rotatePDF(fileId, selectedAngle.value)
    )

    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'rotate',
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
  link.download = `rotated-${new Date().toISOString().slice(0, 10)}.pdf`
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
  destroyWorker()
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <ToolPageShell
      :title="t('tools.rotate.title')"
      :subtitle="t('tools.rotate.desc')"
      :badge="copy.badge"
      accent="amber"
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
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-amber-600 dark:text-amber-300">
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

              <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <button
                  v-for="option in copy.angleOptions"
                  :key="option.value"
                  :class="[
                    'rounded-[22px] border-2 px-4 py-4 text-left transition-all',
                    selectedAngle === option.value
                      ? 'border-primary bg-primary/10 shadow-sm'
                      : 'border-slate-200 bg-slate-50/70 hover:border-primary/40 dark:border-slate-700 dark:bg-slate-950/40',
                  ]"
                  @click="selectedAngle = option.value"
                >
                  <p class="text-sm font-semibold text-slate-900 dark:text-white">
                    {{ option.label }}
                  </p>
                  <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {{ option.hint }}
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
            :label="copy.actionLabel"
            :title="copy.actionTitle"
            accent="amber"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? t('common.processing') : copy.action"
            :loading="isProcessing"
            @action="rotatePages"
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
