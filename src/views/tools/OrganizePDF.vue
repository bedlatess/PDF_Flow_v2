<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Layers3 } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import PageThumbnail from '@/components/pdf/PageThumbnail.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolResultPanel from '@/components/tools/ToolResultPanel.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { reorderPDFPages } from '@/utils/pdf/split'
import { memoryManager } from '@/utils/memory-manager'
import { historyManager } from '@/utils/history-manager'

interface PageItem {
  pageNumber: number
}

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
const pageItems = ref<PageItem[]>([])
const draggingIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
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
  clearProcessingError,
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => tm('tools.organize.page') as ToolPageCopy)

const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)
const totalPages = computed(() => pageItems.value.length)
const orderedPages = computed(() => pageItems.value.map((item) => item.pageNumber))
const hasOrderChanged = computed(() =>
  orderedPages.value.some((pageNumber, index) => pageNumber !== index + 1)
)
const actionStats = computed(() => [
  { label: copy.value.pageCount, value: totalPages.value },
  { label: copy.value.firstPage, value: orderedPages.value[0] || '-' },
  { label: copy.value.lastPage, value: orderedPages.value[orderedPages.value.length - 1] || '-' },
])

const clearResult = () => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const handleFilesSelected = async (files: File[]) => {
  try {
    clearResult()
    setSelectedFiles(files.slice(0, 1))
    const count = await getPDFPageCount(files[0])
    pageItems.value = Array.from({ length: count }, (_, index) => ({ pageNumber: index + 1 }))
    clearFileError()
    resetProcessing()
  } catch (error) {
    clearSelection()
    pageItems.value = []
    setFileError(error instanceof Error ? error.message : copy.value.errorLoad)
  }
}

const handleError = (message: string) => {
  setFileError(message)
}

const clearAll = () => {
  clearSelection()
  pageItems.value = []
  draggingIndex.value = null
  dragOverIndex.value = null
  showPDFViewer.value = false
  resetProcessing()
  clearResult()
}

const moveItem = (fromIndex: number, toIndex: number) => {
  if (fromIndex === toIndex || toIndex < 0 || toIndex >= pageItems.value.length) return

  const nextItems = [...pageItems.value]
  const [item] = nextItems.splice(fromIndex, 1)
  nextItems.splice(toIndex, 0, item)
  pageItems.value = nextItems
  clearProcessingError()
}

const handleDragStart = (event: DragEvent, index: number) => {
  draggingIndex.value = index
  event.dataTransfer?.setData('text/plain', String(index))
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

const handleDragEnter = (event: DragEvent, index: number) => {
  event.preventDefault()
  if (draggingIndex.value !== null && draggingIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const handleDrop = (event: DragEvent, targetIndex: number) => {
  event.preventDefault()
  if (draggingIndex.value === null) return

  moveItem(draggingIndex.value, targetIndex)
  draggingIndex.value = null
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  draggingIndex.value = null
  dragOverIndex.value = null
}

const reverseOrder = () => {
  pageItems.value = [...pageItems.value].reverse()
  clearProcessingError()
}

const resetOrder = () => {
  pageItems.value = pageItems.value
    .map((item) => item.pageNumber)
    .sort((a, b) => a - b)
    .map((pageNumber) => ({ pageNumber }))
  clearProcessingError()
}

const organizePages = async () => {
  if (!selectedFile.value) return

  if (!hasOrderChanged.value) {
    failProcessing(copy.value.errorNoChange)
    return
  }

  startProcessing(copy.value.statusPreparing)
  clearResult()

  try {
    updateProcessing(45, copy.value.statusProcessing)
    const blob = await reorderPDFPages(selectedFile.value, orderedPages.value)

    updateProcessing(100, copy.value.statusDone)
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'organize',
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
  link.download = `organized-${new Date().toISOString().slice(0, 10)}.pdf`
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
      accent="emerald"
    width="lg"
  >

      <template #badgeIcon>
        <Layers3 class="h-4 w-4" />
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
          <div class="space-y-5">
            <FilePreview
              :file="selectedFile"
              @remove="clearAll"
              @preview="showPDFViewer = true"
            />

            <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
              <div class="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
                  {{ copy.workspaceLabel }}
                </p>
                <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                  {{ copy.workspaceTitle }}
                </h2>
                <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.workspaceDesc }}
                </p>
              </div>

              <div class="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  @click="reverseOrder"
                >
                  {{ copy.reverse }}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  @click="resetOrder"
                >
                  {{ copy.reset }}
                </Button>
              </div>
              </div>

              <p class="mb-4 rounded-md border border-emerald-100 bg-emerald-50/70 px-4 py-3 text-sm leading-6 text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-100">
                {{ copy.dragHint }}
              </p>

              <div class="grid max-h-[680px] grid-cols-2 gap-4 overflow-y-auto pr-1 sm:grid-cols-3 xl:grid-cols-4">
              <article
                v-for="(item, index) in pageItems"
                :key="item.pageNumber"
                :class="[
                  'rounded-md border p-3 transition-all duration-200',
                  dragOverIndex === index ? 'border-emerald-400 bg-emerald-50 shadow-sm shadow-emerald-100 dark:border-emerald-300 dark:bg-emerald-500/10' : 'border-slate-200 bg-white/80 dark:border-slate-800 dark:bg-slate-950/40',
                  draggingIndex === index ? 'scale-95 opacity-60' : 'opacity-100',
                ]"
                draggable="true"
                @dragstart="handleDragStart($event, index)"
                @dragenter="handleDragEnter($event, index)"
                @dragover="handleDragOver"
                @drop="handleDrop($event, index)"
                @dragend="handleDragEnd"
              >
                <PageThumbnail
                  :file="selectedFile"
                  :page-number="item.pageNumber"
                  draggable
                  @dragstart="handleDragStart($event, index)"
                  @dragend="handleDragEnd"
                />

                <div class="mt-3 flex items-center justify-between gap-2">
                  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {{ copy.page.replace('{page}', String(item.pageNumber)) }}
                  </span>
                  <div class="flex gap-1">
                    <button
                      class="rounded-full border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 transition hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-300"
                      :disabled="index === 0"
                      type="button"
                      @click="moveItem(index, index - 1)"
                    >
                      {{ copy.moveUp }}
                    </button>
                    <button
                      class="rounded-full border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 transition hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-300"
                      :disabled="index === pageItems.length - 1"
                      type="button"
                      @click="moveItem(index, index + 1)"
                    >
                      {{ copy.moveDown }}
                    </button>
                  </div>
                </div>
              </article>
              </div>
            </section>
          </div>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <ToolActionPanel
            :label="copy.outputLabel"
            :title="copy.outputTitle"
            accent="emerald"
            :stats="actionStats"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.statusProcessing : copy.generate"
            :loading="isProcessing"
            @action="organizePages"
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
