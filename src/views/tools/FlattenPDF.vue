<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  BadgeCheck,
  Download,
  Layers3,
  ShieldAlert,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { flattenPDF } from '@/utils/pdf/flatten'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { historyManager } from '@/utils/history-manager'
import { memoryManager } from '@/utils/memory-manager'

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
const pageCount = ref(0)
const fieldCount = ref<number | null>(null)
const resultUrl = ref('')
const resultSize = ref(0)

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

const copy = computed<ToolPageCopy>(() => tm('tools.flatten.page') as ToolPageCopy)

const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)
const canFlatten = computed(() => !!selectedFile.value && !isProcessing.value)
const resultStats = computed(() => [
  { label: copy.value.pages, value: pageCount.value || '-' },
  { label: copy.value.fieldLabel, value: fieldCount.value ?? '-' },
  { label: copy.value.outputSize, value: formatFileSize(resultSize.value) },
])

const handleFilesSelected = async (files: File[]) => {
  try {
    clearResult()
    setSelectedFiles(files.slice(0, 1))
    pageCount.value = await getPDFPageCount(files[0])
    fieldCount.value = null
    clearFileError()
    resetProcessing()
  } catch {
    clearSelection()
    pageCount.value = 0
    setFileError(copy.value.errorLoad)
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
  resultSize.value = 0
}

const removeFile = () => {
  clearSelection()
  pageCount.value = 0
  fieldCount.value = null
  resetProcessing()
  clearResult()
}

const flatten = async () => {
  if (!selectedFile.value) return

  startProcessing(copy.value.processing)
  updateProcessing(20, copy.value.processing)
  clearResult()

  try {
    updateProcessing(65, copy.value.processing)
    const result = await flattenPDF(selectedFile.value)
    fieldCount.value = result.fieldCount
    resultSize.value = result.blob.size
    updateProcessing(100, copy.value.done)
    resultUrl.value = memoryManager.createTemporaryURL(result.blob)

    historyManager.addHistory({
      type: 'flatten',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: result.blob.size,
    })
  } catch {
    failProcessing(copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`
}

const downloadResult = () => {
  if (!resultUrl.value || !selectedFile.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = selectedFile.value.name.replace(/\.pdf$/i, '') + '-flattened.pdf'
  link.click()
}

onUnmounted(clearResult)
</script>

<template>
  <ToolPageShell
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="blue"
    width="lg"
  >

      <template #badgeIcon>
        <Layers3 class="h-4 w-4" />
      </template>
      <ToolNoticeBar variant="blue">
        <template #icon>
          <ShieldAlert class="h-5 w-5" />
        </template>
        {{ copy.notice }}
      </ToolNoticeBar>

      <ToolWorkspace
        :error-message="workspaceError"
        layout="wide-secondary"
      >
        <template
          v-if="!selectedFile"
          #upload
        >
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-600 dark:text-slate-300">
                  {{ copy.uploadLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ copy.uploadTitleIdle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.uploadDescriptionIdle }}
                </p>
              </div>

              <DragDropZone
                accept="pdf"
                :multiple="false"
                :max-files="1"
                @files-selected="handleFilesSelected"
                @error="handleError"
              >
                <template #icon>
                  <Layers3 class="h-12 w-12" />
                </template>
                <template #title>
                  {{ copy.dropTitle }}
                </template>
                <template #subtitle>
                  {{ copy.dropSubtitle }}
                </template>
              </DragDropZone>
            </div>
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
                    {{ copy.uploadTitleReady }}
                  </h3>
                  <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ copy.uploadDescriptionReady }}
                  </p>
                </div>
                <div>
                  <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                    {{ copy.localTitle }}
                  </h3>
                  <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ copy.localDesc }}
                  </p>
                </div>
                <div class="grid gap-3">
                  <div
                    v-for="(step, index) in [copy.step1, copy.step2, copy.step3]"
                    :key="step"
                    class="flex items-center gap-3 rounded-md border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                  >
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white dark:bg-slate-100 dark:text-slate-950">
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

        <template
          v-if="selectedFile"
          #secondary
        >
          <ToolActionPanel
            :label="copy.resultLabel"
            :title="resultUrl ? copy.successTitle : copy.waitingTitle"
            :description="resultUrl ? copy.successMessage : copy.waitingBody"
            accent="blue"
            :stats="resultStats"
            :show-progress="isProcessing || !!resultUrl"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.processing : copy.action"
            :loading="isProcessing"
            :disabled="!canFlatten"
            @action="flatten"
          >
            <template #details>
              <div
                v-if="fieldCount === 0 && resultUrl"
                class="rounded-md border border-amber-200 bg-amber-50 p-5 dark:border-amber-500/20 dark:bg-amber-500/10"
              >
                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                  {{ copy.noFieldsTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.noFieldsBody }}
                </p>
              </div>

              <Button
                v-if="resultUrl"
                variant="outline"
                size="lg"
                full-width
                @click="downloadResult"
              >
                <Download class="mr-2 h-4 w-4" />
                {{ copy.download }}
              </Button>
            </template>
          </ToolActionPanel>

          <section
            v-if="resultUrl"
            class="rounded-lg border border-emerald-200 bg-emerald-50/90 p-4 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none sm:p-5"
          >
            <div class="flex items-start gap-4">
              <BadgeCheck class="mt-0.5 h-6 w-6 shrink-0 text-emerald-500" />
              <div>
                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                  {{ copy.successTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.successMessage }}
                </p>
              </div>
            </div>
          </section>
        </template>
      </ToolWorkspace>
  </ToolPageShell>
</template>
