<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ClipboardCopy,
  Download,
  FileText,
  ScanText,
  Sparkles,
  TextCursorInput,
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
import { extractTextFromPDF, type ExtractedTextResult } from '@/utils/pdf/textExtraction'

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
const result = ref<ExtractedTextResult | null>(null)
const copied = ref(false)

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

const copy = computed<ToolPageCopy>(() => tm('tools.extractText.page') as ToolPageCopy)

const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)
const hasText = computed(() => result.value?.pages.some((page) => page.text.trim().length > 0) ?? false)
const canExtract = computed(() => !!selectedFile.value && !isProcessing.value)
const actionStats = computed(() => [
  { label: copy.value.pageCount, value: result.value?.pageCount || '-' },
  { label: copy.value.characters, value: result.value?.characterCount || '-' },
  { label: copy.value.fileSize, value: selectedFile.value ? formatFileSize(selectedFile.value.size) : '-' },
])

const handleFilesSelected = (files: File[]) => {
  const file = files[0]
  if (!file) return

  setSelectedFiles([file])
  result.value = null
  clearFileError()
  resetProcessing()
  copied.value = false
}

const removeFile = () => {
  clearSelection()
  result.value = null
  resetProcessing()
  copied.value = false
}

const handleError = (message: string) => {
  setFileError(message)
}

const extractText = async () => {
  if (!selectedFile.value) return

  startProcessing(copy.value.processing)
  updateProcessing(20, copy.value.processing)
  clearFileError()
  copied.value = false

  try {
    updateProcessing(60, copy.value.processing)
    const extracted = await extractTextFromPDF(selectedFile.value, {
      pageLabel: (pageNumber) => t('tools.extractText.page.pageLabel', { page: pageNumber }),
    })
    result.value = extracted
    updateProcessing(100, copy.value.ready)

    historyManager.addHistory({
      type: 'extractText',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: new Blob([extracted.text], { type: 'text/plain;charset=utf-8' }).size,
    })
  } catch {
    result.value = null
    failProcessing(copy.value.errorFailed)
  } finally {
    isProcessing.value = false
  }
}

const copyResult = async () => {
  if (!result.value?.text) return

  try {
    await navigator.clipboard.writeText(result.value.text)
    copied.value = true
    window.setTimeout(() => {
      copied.value = false
    }, 1800)
  } catch {
    failProcessing(copy.value.copyFailed)
  }
}

const downloadResult = () => {
  if (!selectedFile.value || !result.value?.text) return

  const blob = new Blob([result.value.text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = selectedFile.value.name.replace(/\.pdf$/i, '') + '-text.txt'
  link.click()
  URL.revokeObjectURL(url)
}

onUnmounted(() => {
  copied.value = false
})
</script>

<template>
  <ToolPageShell
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="cyan"
    width="lg"
  >

      <template #badgeIcon>
        <TextCursorInput class="h-4 w-4" />
      </template>
      <ToolNoticeBar variant="blue">
        <template #icon>
          <ScanText class="h-5 w-5" />
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
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-600">
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
                  <FileText class="h-12 w-12" />
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
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-600 text-sm font-bold text-white">
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
            :label="copy.textPreview"
            :title="result ? copy.resultTitle : copy.action"
            :description="result ? copy.resultBody : copy.notice"
            accent="blue"
            :stats="actionStats"
            :show-progress="isProcessing || !!result"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.processing : copy.action"
            :loading="isProcessing"
            :disabled="!canExtract"
            @action="extractText"
          >
            <template #details>
              <div class="flex flex-col gap-3 sm:flex-row">
                <Button
                  v-if="hasText"
                  variant="outline"
                  size="lg"
                  full-width
                  @click="copyResult"
                >
                  <ClipboardCopy class="mr-2 h-4 w-4" />
                  {{ copied ? copy.copied : copy.copyText }}
                </Button>
                <Button
                  v-if="hasText"
                  variant="primary"
                  size="lg"
                  full-width
                  @click="downloadResult"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ copy.download }}
                </Button>
              </div>
            </template>
          </ToolActionPanel>

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-5">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-600">
                    {{ copy.textPreview }}
                  </p>
                  <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                    {{ result ? copy.resultTitle : copy.textPreview }}
                  </h2>
                  <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ result ? copy.resultBody : copy.notice }}
                  </p>
                </div>
                <div
                  v-if="result"
                  class="flex shrink-0 gap-2"
                >
                  <Button
                    v-if="hasText"
                    variant="outline"
                    size="sm"
                    @click="copyResult"
                  >
                    <ClipboardCopy class="mr-2 h-4 w-4" />
                    {{ copied ? copy.copied : copy.copyText }}
                  </Button>
                  <Button
                    v-if="hasText"
                    variant="primary"
                    size="sm"
                    @click="downloadResult"
                  >
                    <Download class="mr-2 h-4 w-4" />
                    {{ copy.download }}
                  </Button>
                </div>
              </div>

              <div
                v-if="result && !hasText"
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
                v-else-if="hasText"
                class="max-h-[620px] overflow-auto rounded-md border border-slate-200 bg-slate-950 p-5 text-slate-100 shadow-inner dark:border-slate-800"
              >
                <pre class="whitespace-pre-wrap break-words text-sm leading-7">{{ result?.text }}</pre>
              </div>

              <div
                v-else
                class="rounded-md border border-dashed border-slate-300 bg-slate-50/70 p-10 text-center dark:border-slate-700 dark:bg-slate-950/35"
              >
                <FileText class="mx-auto h-12 w-12 text-cyan-500" />
                <p class="mx-auto mt-4 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {{ copy.uploadDescriptionReady }}
                </p>
              </div>
            </div>
          </section>
        </template>
      </ToolWorkspace>
  </ToolPageShell>
</template>
