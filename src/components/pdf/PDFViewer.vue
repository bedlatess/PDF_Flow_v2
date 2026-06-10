<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import Button from '@/components/common/Button.vue'
import { configurePdfJsWorker } from '@/utils/pdf/configurePdfJs'

interface PDFViewerProps {
  file: File
  initialPage?: number
}

const props = withDefaults(defineProps<PDFViewerProps>(), {
  initialPage: 1,
})

const emit = defineEmits<{
  close: []
}>()

// PDF 相关
const pdfDoc = ref<pdfjsLib.PDFDocumentProxy | null>(null)
const currentPage = ref(props.initialPage)
const totalPages = ref(0)
const scale = ref(1.0)
const rotation = ref(0)

// UI 状态
const canvas = ref<HTMLCanvasElement | null>(null)
const isLoading = ref(true)
const isRendering = ref(false)
const errorMessage = ref('')
const isFullscreen = ref(false)

// 配置 PDF.js worker
configurePdfJsWorker()

// 缩放选项
const scaleOptions = [
  { label: '50%', value: 0.5 },
  { label: '75%', value: 0.75 },
  { label: '100%', value: 1.0 },
  { label: '125%', value: 1.25 },
  { label: '150%', value: 1.5 },
  { label: '200%', value: 2.0 },
]

// 计算属性
const canGoPrevious = computed(() => currentPage.value > 1)
const canGoNext = computed(() => currentPage.value < totalPages.value)

// 加载 PDF 文档
const loadPDF = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const arrayBuffer = await props.file.arrayBuffer()
    pdfDoc.value = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
    totalPages.value = pdfDoc.value.numPages
    await renderPage(currentPage.value)
  } catch (error) {
    console.error('Failed to load PDF:', error)
    errorMessage.value = 'Failed to load PDF document'
  } finally {
    isLoading.value = false
  }
}

// 渲染页面
const renderPage = async (pageNum: number) => {
  if (!pdfDoc.value || !canvas.value) return
  if (isRendering.value) return

  isRendering.value = true

  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const ctx = canvas.value.getContext('2d')
    if (!ctx) return

    const viewport = page.getViewport({ scale: scale.value, rotation: rotation.value })

    canvas.value.height = viewport.height
    canvas.value.width = viewport.width

    const renderContext = {
      canvasContext: ctx,
      viewport: viewport,
    }

    await page.render(renderContext).promise
    currentPage.value = pageNum
  } catch (error) {
    console.error('Failed to render page:', error)
    errorMessage.value = 'Failed to render page'
  } finally {
    isRendering.value = false
  }
}

// 导航
const goToPreviousPage = () => {
  if (canGoPrevious.value) {
    renderPage(currentPage.value - 1)
  }
}

const goToNextPage = () => {
  if (canGoNext.value) {
    renderPage(currentPage.value + 1)
  }
}

const goToPage = (pageNum: number) => {
  if (pageNum >= 1 && pageNum <= totalPages.value) {
    renderPage(pageNum)
  }
}

// 缩放
const zoomIn = () => {
  if (scale.value < 3.0) {
    scale.value = Math.min(scale.value + 0.25, 3.0)
    renderPage(currentPage.value)
  }
}

const zoomOut = () => {
  if (scale.value > 0.25) {
    scale.value = Math.max(scale.value - 0.25, 0.25)
    renderPage(currentPage.value)
  }
}

// 旋转
const rotateClockwise = () => {
  rotation.value = (rotation.value + 90) % 360
  renderPage(currentPage.value)
}

const rotateCounterClockwise = () => {
  rotation.value = (rotation.value - 90 + 360) % 360
  renderPage(currentPage.value)
}

// 全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

// 键盘快捷键
const handleKeydown = (e: KeyboardEvent) => {
  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault()
      goToPreviousPage()
      break
    case 'ArrowRight':
      e.preventDefault()
      goToNextPage()
      break
    case '+':
    case '=':
      e.preventDefault()
      zoomIn()
      break
    case '-':
    case '_':
      e.preventDefault()
      zoomOut()
      break
    case 'Escape':
      if (isFullscreen.value) {
        toggleFullscreen()
      } else {
        emit('close')
      }
      break
  }
}

// 生命周期
onMounted(() => {
  loadPDF()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => props.file, () => {
  loadPDF()
})
</script>

<template>
  <div
    :class="[
      'pdf-viewer flex flex-col bg-gray-900',
      isFullscreen ? 'fixed inset-0 z-50' : 'h-full',
    ]"
  >
    <!-- Toolbar -->
    <div class="flex-shrink-0 border-b border-gray-700 bg-gray-800 px-4 py-3">
      <div class="flex items-center justify-between gap-4">
        <!-- Left: Navigation -->
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            :disabled="!canGoPrevious"
            @click="goToPreviousPage"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </Button>

          <div class="flex items-center gap-2">
            <input
              :value="currentPage"
              type="number"
              min="1"
              :max="totalPages"
              class="w-16 rounded border border-gray-600 bg-gray-700 px-2 py-1 text-center text-sm text-white"
              @change="(e) => goToPage(Number((e.target as HTMLInputElement).value))"
            >
            <span class="text-sm text-gray-400">/ {{ totalPages }}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            :disabled="!canGoNext"
            @click="goToNextPage"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </Button>
        </div>

        <!-- Center: Zoom -->
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            @click="zoomOut"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </Button>

          <select
            v-model="scale"
            class="rounded border border-gray-600 bg-gray-700 px-2 py-1 text-sm text-white"
            @change="renderPage(currentPage)"
          >
            <option
              v-for="option in scaleOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>

          <Button
            variant="ghost"
            size="sm"
            @click="zoomIn"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
            </svg>
          </Button>
        </div>

        <!-- Right: Actions -->
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            title="Rotate Counter-Clockwise"
            @click="rotateCounterClockwise"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            title="Rotate Clockwise"
            @click="rotateClockwise"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10h-10a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6" />
            </svg>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            :title="isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'"
            @click="toggleFullscreen"
          >
            <svg v-if="!isFullscreen" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
            </svg>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            @click="emit('close')"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </div>
      </div>
    </div>

    <!-- Canvas Container -->
    <div class="flex-1 overflow-auto bg-gray-900 p-4">
      <!-- Loading -->
      <div
        v-if="isLoading"
        class="flex h-full items-center justify-center"
      >
        <div class="text-center">
          <svg
            class="mx-auto h-12 w-12 animate-spin text-primary"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p class="mt-4 text-gray-400">Loading PDF...</p>
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="errorMessage"
        class="flex h-full items-center justify-center"
      >
        <div class="text-center text-error">
          <svg class="mx-auto h-12 w-12" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <p class="mt-4">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- Canvas -->
      <div
        v-else
        class="flex justify-center"
      >
        <canvas
          ref="canvas"
          class="shadow-2xl"
        />
      </div>
    </div>

    <!-- Footer: Keyboard Shortcuts Hint -->
    <div class="flex-shrink-0 border-t border-gray-700 bg-gray-800 px-4 py-2">
      <p class="text-center text-xs text-gray-500">
        💡 使用 ← → 翻页 | +/- 缩放 | ESC 关闭
      </p>
    </div>
  </div>
</template>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}
</style>
