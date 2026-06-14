<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import CloudToggle from '@/components/common/CloudToggle.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { memoryManager } from '@/utils/memory-manager'
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
  appendItems: appendSelectedFiles,
  removeAt: removeSelectedFile,
  clearSelection,
  setFileError,
  clearFileError,
} = useToolFileSelection<File>()
const pageSize = ref<'a4' | 'letter' | 'a3'>('a4')
const orientation = ref<'portrait' | 'landscape'>('portrait')
const useCloud = ref(false)
const showSuccessModal = ref(false)
const resultUrl = ref('')

const { processInCloud } = useCloudProcessing()
const {
  isProcessing,
  processingError,
  startProcessing,
  resetProcessing,
  failProcessing,
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => ({
  ...(tm('tools.imageToPdf.page') as ToolPageCopy),
  filesTitle: t('tools.imageToPdf.page.filesTitle', { count: selectedFiles.value.length }),
}))
const workspaceError = computed(() => fileError.value || processingError.value)
const actionStats = computed(() => [
  { label: copy.value.filesLabel, value: selectedFiles.value.length },
])

const handleFilesSelected = (files: File[]) => {
  appendSelectedFiles(files)
  useCloud.value = shouldPreferCloudProcessing(selectedFiles.value, userStore.canUseCloudFeatures)
  clearFileError()
  resetProcessing()
}

const handleError = (message: string) => {
  setFileError(message)
}

const removeFile = (index: number) => {
  removeSelectedFile(index)
  useCloud.value = shouldPreferCloudProcessing(selectedFiles.value, userStore.canUseCloudFeatures)
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

const convertToPDF = async () => {
  if (selectedFiles.value.length === 0) return

  if (useCloud.value) {
    await convertInCloud()
    return
  }

  startProcessing()

  try {
    const { imagesToPDF } = await import('@/utils/pdf/convert')
    const blob = await imagesToPDF(selectedFiles.value, {
      pageSize: pageSize.value,
      orientation: orientation.value,
    })

    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'imageToPdf',
      fileName: `${selectedFiles.value.length} images`,
      fileSize: selectedFiles.value.reduce((sum, file) => sum + file.size, 0),
      resultSize: blob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const convertInCloud = async () => {
  if (selectedFiles.value.length === 0) return

  startProcessing()

  try {
    const fileIds: string[] = []

    for (const file of selectedFiles.value) {
      const uploaded = await fileAPI.uploadFile(file)
      fileIds.push(uploaded.file_id)
    }

    const blob = await processInCloud(selectedFiles.value[0], () =>
      fileAPI.imagesToPDF(fileIds)
    )

    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'imageToPdf',
      fileName: `${selectedFiles.value.length} images`,
      fileSize: selectedFiles.value.reduce((sum, file) => sum + file.size, 0),
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
  link.download = `images-${new Date().toISOString().slice(0, 10)}.pdf`
  link.click()
  showSuccessModal.value = false
}
</script>

<template>
  <ToolPageShell
      :title="t('tools.imageToPdf.title')"
      :subtitle="t('tools.imageToPdf.desc')"
      :badge="copy.badge"
      accent="blue"
    width="md"
  >

      <template #badgeIcon>
        <FileText class="h-4 w-4" />
      </template>

      <ToolWorkspace
        :error-message="workspaceError"
        layout="balanced"
      >
        <template
          v-if="selectedFiles.length === 0"
          #upload
        >
          <DragDropZone
            accept="image"
            :multiple="true"
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
                  {{ copy.filesLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ copy.filesTitle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.filesDesc }}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                @click="clearAll"
              >
                {{ copy.clear }}
              </Button>
            </div>

            <div class="space-y-3">
              <FilePreview
                v-for="(file, index) in selectedFiles"
                :key="`${file.name}-${index}`"
                :file="file"
                @remove="removeFile(index)"
              />
            </div>

            <DragDropZone
              accept="image"
              :multiple="true"
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
            :label="copy.outputLabel"
            :title="copy.outputTitle"
            :description="copy.outputDesc"
            accent="blue"
            :stats="actionStats"
            :action-label="isProcessing ? t('common.processing') : copy.action"
            :loading="isProcessing"
            @action="convertToPDF"
          >
            <CloudToggle v-model="useCloud" />

            <template #details>
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label
                  for="image-to-pdf-page-size"
                  class="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                >
                  {{ copy.pageSize }}
                </label>
                <select
                  id="image-to-pdf-page-size"
                  v-model="pageSize"
                  class="w-full rounded-md border border-slate-300 px-4 py-3 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                >
                  <option value="a4">A4</option>
                  <option value="letter">Letter</option>
                  <option value="a3">A3</option>
                </select>
              </div>
              <div>
                <label
                  for="image-to-pdf-orientation"
                  class="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                >
                  {{ copy.orientation }}
                </label>
                <select
                  id="image-to-pdf-orientation"
                  v-model="orientation"
                  class="w-full rounded-md border border-slate-300 px-4 py-3 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                >
                  <option value="portrait">{{ copy.portrait }}</option>
                  <option value="landscape">{{ copy.landscape }}</option>
                </select>
              </div>
            </div>
            </template>
          </ToolActionPanel>
        </template>
      </ToolWorkspace>

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
