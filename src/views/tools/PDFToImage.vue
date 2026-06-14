<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Button from '@/components/common/Button.vue'
import CloudToggle from '@/components/common/CloudToggle.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
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
const imageFormat = ref<'png' | 'jpeg'>('png')
const useCloud = ref(false)
const resultImages = ref<{ url: string; blob: Blob }[]>([])
const successMessage = ref('')

const { processInCloud } = useCloudProcessing()
const {
  isProcessing,
  processingError,
  startProcessing,
  resetProcessing,
  failProcessing,
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => ({
  ...(tm('tools.pdfToImage.page') as ToolPageCopy),
  readyTitle: t('tools.pdfToImage.page.readyTitle', { count: resultImages.value.length }),
}))
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)

const handleFilesSelected = (files: File[]) => {
  setSelectedFiles(files.slice(0, 1))
  useCloud.value = shouldPreferCloudProcessing(files.slice(0, 1), userStore.canUseCloudFeatures)
  clearFileError()
  resetProcessing()
  successMessage.value = ''
}

const handleError = (message: string) => {
  setFileError(message)
}

const revokeImageUrls = () => {
  resultImages.value.forEach((img) => URL.revokeObjectURL(img.url))
  resultImages.value = []
}

const clearAll = () => {
  clearSelection()
  useCloud.value = false
  resetProcessing()
  successMessage.value = ''
  revokeImageUrls()
}

const convertToImages = async () => {
  if (!selectedFile.value) return

  if (useCloud.value) {
    await convertInCloud()
    return
  }

  startProcessing()
  successMessage.value = ''
  revokeImageUrls()

  try {
    const { pdfToImages } = await import('@/utils/pdf/convert')
    const blobs = await pdfToImages(selectedFile.value, { format: imageFormat.value })
    resultImages.value = blobs.map((blob) => ({
      url: URL.createObjectURL(blob),
      blob,
    }))

    historyManager.addHistory({
      type: 'pdfToImage',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blobs.reduce((sum, blob) => sum + blob.size, 0),
    })
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const convertInCloud = async () => {
  if (!selectedFile.value) return

  startProcessing()
  successMessage.value = ''
  revokeImageUrls()

  try {
    const blob = await processInCloud(selectedFile.value, (fileId) =>
      fileAPI.pdfToImages(fileId, imageFormat.value)
    )

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `pdf-images-${new Date().toISOString().slice(0, 10)}.zip`
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 100)

    historyManager.addHistory({
      type: 'pdfToImage',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })

    successMessage.value = copy.value.successCloud
  } catch (error) {
    failProcessing(error instanceof Error ? error.message : copy.value.errorCloudFailed)
  } finally {
    isProcessing.value = false
  }
}

const downloadImage = (index: number) => {
  const image = resultImages.value[index]
  if (!image) return
  const link = document.createElement('a')
  link.href = image.url
  link.download = `page-${index + 1}.${imageFormat.value}`
  link.click()
}

const downloadAll = () => {
  resultImages.value.forEach((_, index) => downloadImage(index))
}

onUnmounted(() => {
  revokeImageUrls()
})
</script>

<template>
  <ToolPageShell
      :title="t('tools.pdfToImage.title')"
      :subtitle="t('tools.pdfToImage.desc')"
      :badge="copy.badge"
      accent="cyan"
    width="md"
  >

      <template #badgeIcon>
        <FileText class="h-4 w-4" />
      </template>

      <div
        v-if="successMessage"
        class="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-200"
      >
        {{ successMessage }}
      </div>

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
          />

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600 dark:text-sky-300">
                  {{ copy.outputLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ copy.outputTitle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.outputDesc }}
                </p>
              </div>

              <CloudToggle v-model="useCloud" />

              <div class="grid grid-cols-2 gap-3">
                <button
                  v-for="fmt in ['png', 'jpeg']"
                  :key="fmt"
                  :class="[
                    'rounded-md border-2 px-4 py-4 text-sm font-semibold uppercase transition-all',
                    imageFormat === fmt
                      ? 'border-primary bg-primary/10 text-primary shadow-sm'
                      : 'border-slate-200 bg-slate-50/70 text-slate-700 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-300',
                  ]"
                  @click="imageFormat = fmt as 'png' | 'jpeg'"
                >
                  {{ fmt }}
                </button>
              </div>
            </div>
          </section>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600 dark:text-sky-300">
                  {{ copy.resultLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ resultImages.length > 0 ? copy.readyTitle : copy.waitingTitle }}
                </h2>
              </div>

              <Button
                v-if="resultImages.length > 0"
                variant="primary"
                size="sm"
                @click="downloadAll"
              >
                {{ copy.downloadAll }}
              </Button>
            </div>

            <ToolActionPanel
              v-if="resultImages.length === 0"
              :title="copy.action"
              :description="copy.outputDesc"
              accent="blue"
              :action-label="isProcessing ? t('common.processing') : copy.action"
              :loading="isProcessing"
              @action="convertToImages"
            >
              <CloudToggle v-model="useCloud" />
            </ToolActionPanel>

            <div
              v-if="resultImages.length === 0"
              class="rounded-md border border-dashed border-slate-300 bg-slate-50/70 p-6 text-sm leading-6 text-slate-500 dark:border-slate-700 dark:bg-slate-950/30 dark:text-slate-400"
            >
              {{ copy.emptyHint }}
            </div>

            <div
              v-else
              class="grid grid-cols-2 gap-4 sm:grid-cols-3"
            >
              <div
                v-for="(img, index) in resultImages"
                :key="index"
                class="group relative cursor-pointer overflow-hidden rounded-[22px] border border-slate-200 bg-slate-50/70 shadow-sm dark:border-slate-800 dark:bg-slate-950/40"
                @click="downloadImage(index)"
              >
                <img
                  :src="img.url"
                  :alt="`Page ${index + 1}`"
                  class="w-full"
                >
                <div class="absolute inset-0 flex items-center justify-center bg-slate-950/55 opacity-0 transition-opacity group-hover:opacity-100">
                  <span class="text-sm font-medium text-white">
                    {{ copy.downloadPage.replace('{page}', String(index + 1)) }}
                  </span>
                </div>
              </div>
            </div>
            </div>
          </section>
        </template>
      </ToolWorkspace>
  </ToolPageShell>
</template>
