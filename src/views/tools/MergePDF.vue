<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText, GripVertical, Trash2 } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import PageThumbnail from '@/components/pdf/PageThumbnail.vue'
import Button from '@/components/common/Button.vue'
import CloudToggle from '@/components/common/CloudToggle.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { memoryManager } from '@/utils/memory-manager'
import { useDragSort } from '@/composables/useDragSort'
import { usePDFThumbnail } from '@/composables/usePDFThumbnail'
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

interface FileWithPages {
  file: File
  pageCount: number
  pages: number[]
}

const {
  selectedItems: selectedFiles,
  fileError,
  appendItems: appendSelectedFiles,
  clearSelection,
  setFileError,
  clearFileError,
} = useToolFileSelection<FileWithPages>()
const useCloud = ref(false)
const showSuccessModal = ref(false)
const resultUrl = ref('')
const resultFileName = ref('')
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

const {
  items: sortedFiles,
  setItems,
  handleDragStart,
  handleDragEnter,
  handleDragOver,
  handleDrop,
  handleDragEnd,
  isDragOver,
} = useDragSort<FileWithPages>()
const { generateMultipleThumbnails, clearThumbnails } = usePDFThumbnail()
const { submitTask, getTask, waitForTask, destroyWorker } = usePDFWorker()
const { processInCloud } = useCloudProcessing()

watch(selectedFiles, (newFiles) => {
  setItems(newFiles)
}, { immediate: true, deep: true })

const handleFilesSelected = async (files: File[]) => {
  try {
    const filesWithPages: FileWithPages[] = []

    for (const file of files) {
      const pageCount = await getPDFPageCount(file)
      const pages = Array.from({ length: pageCount }, (_, i) => i + 1)
      filesWithPages.push({ file, pageCount, pages })
      generateMultipleThumbnails(file, pages.slice(0, 5), { width: 200 })
    }

    appendSelectedFiles(filesWithPages)
    useCloud.value = shouldPreferCloudProcessing(
      selectedFiles.value.map((item) => item.file),
      userStore.canUseCloudFeatures,
    )
    clearFileError()
    resetProcessing()
  } catch (error) {
    setFileError(error instanceof Error ? error.message : copy.value.errorLoad)
  }
}

const handleError = (message: string) => {
  setFileError(message)
}

const removeFile = (index: number) => {
  const fileToRemove = sortedFiles.value[index]
  if (fileToRemove) {
    clearThumbnails(fileToRemove.file)
  }
  sortedFiles.value.splice(index, 1)
  selectedFiles.value = [...sortedFiles.value]
}

const clearAll = () => {
  sortedFiles.value.forEach((item) => clearThumbnails(item.file))
  clearSelection()
  useCloud.value = false
  resetProcessing()

  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const mergePDFFiles = async () => {
  if (sortedFiles.value.length < 2) {
    failProcessing(copy.value.errorMinFiles)
    return
  }

  if (useCloud.value) {
    await mergeInCloud()
    return
  }

  startProcessing(copy.value.statusPreparing)

  try {
    const filesToMerge = sortedFiles.value.map((item) => item.file)
    updateProcessing(0, t('tools.merge.page.statusProcessing', { count: filesToMerge.length }))
    const taskId = await submitTask('merge', { files: filesToMerge })

    const progressInterval = setInterval(() => {
      const task = getTask(taskId)
      if (task) {
        processingProgress.value = task.progress
        if (task.progress < 100) {
          processingStatus.value = t('tools.merge.page.statusProgress', { progress: Math.round(task.progress) })
        }
      }
    }, 100)

    const mergedBlob = await waitForTask(taskId) as Blob
    clearInterval(progressInterval)

    updateProcessing(100, copy.value.statusDone)

    resultUrl.value = memoryManager.createTemporaryURL(mergedBlob)
    const timestamp = new Date().toISOString().slice(0, 10)
    resultFileName.value = `merged-${timestamp}.pdf`

    historyManager.addHistory({
      type: 'merge',
      fileName: `${sortedFiles.value.length} files`,
      fileSize: sortedFiles.value.reduce((sum, f) => sum + f.file.size, 0),
      resultSize: mergedBlob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const mergeInCloud = async () => {
  if (sortedFiles.value.length < 2) return
  startProcessing(copy.value.statusPreparing)

  try {
    const fileIds: string[] = []
    for (const item of sortedFiles.value) {
      const uploaded = await fileAPI.uploadFile(item.file)
      fileIds.push(uploaded.file_id)
    }

    const blob = await processInCloud(sortedFiles.value[0].file, () =>
      fileAPI.mergePDFs(fileIds)
    )

    const timestamp = new Date().toISOString().slice(0, 10)
    resultFileName.value = `merged-${timestamp}.pdf`
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'merge',
      fileName: `${sortedFiles.value.length} files`,
      fileSize: sortedFiles.value.reduce((sum, f) => sum + f.file.size, 0),
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
  link.download = resultFileName.value
  link.click()
  showSuccessModal.value = false
}

const startNew = () => {
  showSuccessModal.value = false
  clearAll()
}

const totalPages = computed(() => {
  return sortedFiles.value.reduce((sum, item) => sum + item.pageCount, 0)
})

const actionStats = computed(() => [
  { label: copy.value.fileCount, value: sortedFiles.value.length },
  { label: copy.value.pageCount, value: totalPages.value },
])

const workspaceError = computed(() => fileError.value || processingError.value)

const copy = computed<ToolPageCopy>(() => ({
  ...(tm('tools.merge.page') as ToolPageCopy),
  queueDesc: t('tools.merge.page.queueDesc', { pages: totalPages.value }),
}))

onUnmounted(() => {
  destroyWorker()
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <ToolPageShell
      :title="t('tools.merge.title')"
      :subtitle="t('tools.merge.desc')"
      :badge="copy.badge"
      accent="blue"
    width="lg"
  >

      <template #badgeIcon>
        <FileText class="h-4 w-4" />
      </template>

      <ToolWorkspace
        :error-message="workspaceError"
        layout="wide-primary"
      >
        <template
          v-if="selectedFiles.length === 0"
          #upload
        >
          <DragDropZone
            accept="pdf"
            :multiple="true"
            :max-files="20"
            @files-selected="handleFilesSelected"
            @error="handleError"
          />
        </template>

        <template
          v-if="selectedFiles.length > 0"
          #primary
        >
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
                  {{ copy.queueLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ copy.queueTitle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.queueDesc }}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                class="self-start"
                @click="clearAll"
              >
                {{ copy.clear }}
              </Button>
            </div>

            <div class="space-y-3">
              <div
                v-for="(item, index) in sortedFiles"
                :key="`${item.file.name}-${index}`"
                data-testid="file-preview"
                :class="[
                  'rounded-md border p-4 shadow-sm transition-all dark:bg-slate-950/40',
                  isDragOver(index)
                    ? 'border-blue-300 bg-blue-50/80 shadow-blue-100'
                    : 'border-slate-200 bg-slate-50/80 dark:border-slate-800',
                ]"
                draggable="true"
                @dragstart="handleDragStart($event, index)"
                @dragenter="handleDragEnter($event, index)"
                @dragover="handleDragOver"
                @drop="handleDrop($event, index)"
                @dragend="handleDragEnd"
              >
                <div class="flex items-center gap-4">
                  <div class="cursor-move text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <GripVertical class="h-5 w-5" />
                  </div>

                  <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-blue-600 text-sm font-bold text-white shadow-sm shadow-blue-200">
                    {{ index + 1 }}
                  </div>

                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                      {{ item.file.name }}
                    </p>
                    <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {{ item.pageCount }} {{ copy.pagesSuffix }}
                    </p>
                  </div>

                  <button
                    class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-error dark:hover:bg-slate-800"
                    :aria-label="`Remove ${item.file.name}`"
                    @click="removeFile(index)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>

                <div
                  v-if="item.pages.length > 0"
                  class="mt-4"
                >
                  <div class="grid grid-cols-5 gap-2">
                    <PageThumbnail
                      v-for="pageNum in item.pages.slice(0, 5)"
                      :key="pageNum"
                      :file="item.file"
                      :page-number="pageNum"
                    />
                  </div>
                  <p
                    v-if="item.pages.length > 5"
                    class="mt-2 text-center text-xs text-slate-500 dark:text-slate-400"
                  >
                    {{ copy.morePages.replace('{count}', String(item.pages.length - 5)) }}
                  </p>
                </div>
              </div>
            </div>

            <DragDropZone
              accept="pdf"
              :multiple="true"
              :max-files="20"
              @files-selected="handleFilesSelected"
              @error="handleError"
            >
              <p class="text-sm text-slate-500 dark:text-slate-400">
                {{ copy.addMore }}
              </p>
            </DragDropZone>
          </section>
        </template>

        <template
          v-if="selectedFiles.length > 0"
          #secondary
        >
          <ToolActionPanel
            :label="copy.actionLabel"
            :title="copy.actionTitle"
            :description="copy.actionDesc"
            accent="blue"
            :stats="actionStats"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? t('common.processing') : copy.merge"
            :loading="isProcessing"
            :disabled="sortedFiles.length < 2"
            @action="mergePDFFiles"
          >
            <CloudToggle v-model="useCloud" />
          </ToolActionPanel>
        </template>
      </ToolWorkspace>

      <ToolResultPanel
        v-model="showSuccessModal"
        :title="copy.successTitle"
        :message="copy.successMessage.replace('{count}', String(sortedFiles.length)).replace('{pages}', String(totalPages))"
        :primary-label="t('common.download')"
        :secondary-label="copy.mergeMore"
        size="md"
        @primary="downloadResult"
        @secondary="startNew"
      >
      </ToolResultPanel>
  </ToolPageShell>
</template>
