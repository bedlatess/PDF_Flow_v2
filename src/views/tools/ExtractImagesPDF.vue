<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Download,
  FileImage,
  ImagePlus,
  Sparkles,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { formatFileSize } from '@/utils/file-validator'
import { historyManager } from '@/utils/history-manager'
import { extractImagesFromPDF, type ExtractedPDFImage } from '@/utils/pdf/imageExtraction'

const { t, tm } = useI18n()

interface ImagePreview extends ExtractedPDFImage {
  url: string
}

type ToolPageCopy = Record<string, any>

const {
  selectedItems: selectedFiles,
  fileError,
  setItems: setSelectedFiles,
  clearSelection,
  setFileError,
  clearFileError,
} = useToolFileSelection<File>()
const resultImages = ref<ImagePreview[]>([])

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

const copy = computed<ToolPageCopy>(() => tm('tools.extractImages.page') as ToolPageCopy)

const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)
const canExtract = computed(() => !!selectedFile.value && !isProcessing.value)
const totalResultSize = computed(() =>
  resultImages.value.reduce((sum, image) => sum + image.blob.size, 0)
)
const actionStats = computed(() => [
  { label: copy.value.resultLabel, value: resultImages.value.length || '-' },
  { label: copy.value.fileSize, value: resultImages.value.length > 0 ? formatFileSize(totalResultSize.value) : '-' },
])

const handleFilesSelected = (files: File[]) => {
  const file = files[0]
  if (!file) return

  clearImageUrls()
  setSelectedFiles([file])
  clearFileError()
  resetProcessing()
}

const handleError = (message: string) => {
  setFileError(message)
}

const clearImageUrls = () => {
  resultImages.value.forEach((image) => URL.revokeObjectURL(image.url))
  resultImages.value = []
}

const removeFile = () => {
  clearSelection()
  resetProcessing()
  clearImageUrls()
}

const extractImages = async () => {
  if (!selectedFile.value) return

  startProcessing(copy.value.processing)
  updateProcessing(18, copy.value.processing)
  clearFileError()
  clearImageUrls()

  try {
    updateProcessing(58, copy.value.processing)
    const extracted = await extractImagesFromPDF(selectedFile.value)
    resultImages.value = extracted.map((image) => ({
      ...image,
      url: URL.createObjectURL(image.blob),
    }))
    updateProcessing(100, copy.value.ready)

    historyManager.addHistory({
      type: 'extractImages',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: totalResultSize.value,
    })
  } catch {
    failProcessing(copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const resultFileName = (image: ImagePreview) => {
  const baseName = selectedFile.value?.name.replace(/\.pdf$/i, '') || 'pdf'
  return `${baseName}-page-${image.pageNumber}-image-${image.imageNumber}.png`
}

const downloadImage = (image: ImagePreview) => {
  const link = document.createElement('a')
  link.href = image.url
  link.download = resultFileName(image)
  link.click()
}

const downloadAll = () => {
  resultImages.value.forEach((image, index) => {
    window.setTimeout(() => downloadImage(image), index * 120)
  })
}

onUnmounted(() => {
  clearImageUrls()
})
</script>

<template>
  <ToolPageShell
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="amber"
    width="lg"
  >

      <template #badgeIcon>
        <ImagePlus class="h-4 w-4" />
      </template>
      <ToolNoticeBar variant="amber">
        <template #icon>
          <FileImage class="h-5 w-5" />
        </template>
        {{ copy.notice }}
      </ToolNoticeBar>

      <ToolWorkspace
        class="mt-6"
        :error-message="workspaceError"
        layout="wide-secondary"
      >
        <template
          v-if="!selectedFile"
          #upload
        >
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-orange-600">
                  {{ copy.uploadLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.uploadTitleIdle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.uploadDescriptionIdle }}
                </p>
              </div>

              <DragDropZone
                class="mt-6"
                accept="pdf"
                :multiple="false"
                :max-files="1"
                @files-selected="handleFilesSelected"
                @error="handleError"
              >
                <template #icon>
                  <FileImage class="h-12 w-12" />
                </template>
                <template #title>
                  {{ copy.dropTitle }}
                </template>
                <template #subtitle>
                  {{ copy.dropSubtitle }}
                </template>
              </DragDropZone>
          </section>
        </template>

        <template
          v-if="selectedFile"
          #primary
        >
              <FilePreview
                :file="selectedFile"
                @remove="removeFile"
              />

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
                <div>
                  <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                    {{ copy.localTitle }}
                  </h3>
                  <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ copy.localBody }}
                  </p>
                </div>
                <div class="grid gap-3">
                  <div
                    v-for="(step, index) in [copy.step1, copy.step2, copy.step3]"
                    :key="step"
                    class="flex items-center gap-3 rounded-md border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                  >
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orange-600 text-sm font-bold text-white">
                      {{ index + 1 }}
                    </span>
                    <span class="text-sm font-medium text-slate-700 dark:text-slate-200">
                      {{ step }}
                    </span>
                  </div>
                </div>
            </div>
          </section>
        </template>

        <template #secondary>
          <ToolActionPanel
            v-if="selectedFile"
            :label="copy.resultLabel"
            :title="resultImages.length > 0 ? t('tools.extractImages.page.readyTitle', { count: resultImages.length }) : copy.action"
            :description="resultImages.length > 0 ? `${copy.fileSize}: ${formatFileSize(totalResultSize)}` : copy.emptyHint"
            accent="amber"
            :stats="actionStats"
            :show-progress="isProcessing || resultImages.length > 0"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.processing : copy.action"
            :loading="isProcessing"
            :disabled="!canExtract"
            @action="extractImages"
          >
            <template #details>
              <Button
                v-if="resultImages.length > 0"
                variant="primary"
                size="lg"
                full-width
                @click="downloadAll"
              >
                <Download class="mr-2 h-4 w-4" />
                {{ copy.downloadAll }}
              </Button>
            </template>
          </ToolActionPanel>

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.22em] text-orange-600">
                    {{ copy.resultLabel }}
                  </p>
                  <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                    {{ resultImages.length > 0 ? t('tools.extractImages.page.readyTitle', { count: resultImages.length }) : copy.waitingTitle }}
                  </h2>
                  <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ resultImages.length > 0 ? `${copy.fileSize}: ${formatFileSize(totalResultSize)}` : copy.emptyHint }}
                  </p>
                </div>
                <Button
                  v-if="resultImages.length > 0"
                  variant="primary"
                  size="sm"
                  @click="downloadAll"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ copy.downloadAll }}
                </Button>
              </div>

              <div
                v-if="selectedFile && !isProcessing && processingProgress === 100 && resultImages.length === 0"
                class="rounded-md border border-amber-200 bg-amber-50 p-6 dark:border-amber-500/20 dark:bg-amber-500/10"
              >
                <div class="flex items-start gap-3">
                  <Sparkles class="mt-1 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-200" />
                  <div>
                    <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                      {{ copy.emptyTitle }}
                    </h3>
                    <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ copy.emptyBody }}
                    </p>
                  </div>
                </div>
              </div>

              <div
                v-else-if="resultImages.length === 0"
                class="rounded-md border border-dashed border-slate-300 bg-slate-50/70 p-10 text-center dark:border-slate-700 dark:bg-slate-950/35"
              >
                <FileImage class="mx-auto h-12 w-12 text-orange-500" />
                <p class="mx-auto mt-4 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {{ copy.emptyHint }}
                </p>
              </div>

              <div
                v-else
                class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
              >
                <article
                  v-for="image in resultImages"
                  :key="image.url"
                  class="group overflow-hidden rounded-md border border-slate-200 bg-slate-50/80 shadow-sm transition hover:-translate-y-0.5 hover:shadow-sm dark:border-slate-800 dark:bg-slate-950/40"
                >
                  <div class="flex aspect-square items-center justify-center bg-white p-3 dark:bg-slate-900">
                    <img
                      :src="image.url"
                      alt=""
                      class="max-h-full max-w-full object-contain"
                    >
                  </div>
                  <div class="space-y-3 p-4">
                    <div class="grid gap-1 text-xs text-slate-500 dark:text-slate-400">
                      <span>{{ copy.page }} {{ image.pageNumber }}</span>
                      <span>{{ copy.size }} {{ image.width }} x {{ image.height }}</span>
                      <span>{{ copy.fileSize }} {{ formatFileSize(image.blob.size) }}</span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      full-width
                      @click="downloadImage(image)"
                    >
                      <Download class="mr-2 h-4 w-4" />
                      {{ copy.download }}
                    </Button>
                  </div>
                </article>
              </div>
            </div>
          </section>
        </template>
      </ToolWorkspace>
  </ToolPageShell>
</template>
