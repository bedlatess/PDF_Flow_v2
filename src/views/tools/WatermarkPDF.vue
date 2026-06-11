<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText } from 'lucide-vue-next'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import PDFViewer from '@/components/pdf/PDFViewer.vue'
import { memoryManager } from '@/utils/memory-manager'
import { historyManager } from '@/utils/history-manager'
import { addWatermark, type WatermarkPosition } from '@/utils/pdf/watermark'
import ToolHeader from '@/components/tools/ToolHeader.vue'

const { t, locale } = useI18n()

const selectedFile = ref<File | null>(null)
const watermarkText = ref('CONFIDENTIAL')
const opacity = ref(0.3)
const rotation = ref(45)
const fontSize = ref(40)
const position = ref<WatermarkPosition>('center')
const watermarkColor = ref('#808080')

const isProcessing = ref(false)
const processingProgress = ref(0)
const processingStatus = ref('')
const showSuccessModal = ref(false)
const showPDFViewer = ref(false)
const resultUrl = ref('')
const errorMessage = ref('')

const isChinese = computed(() => locale.value.startsWith('zh'))

const copy = computed(() => isChinese.value
  ? {
      badge: '本地工具',
      setupLabel: '水印设置',
      setupTitle: '调整文案和样式',
      setupDesc: '适合为合同、报告、草稿或对外传阅文件添加清晰但不过分抢眼的标记。',
      outputLabel: '导出动作',
      outputTitle: '生成带水印的新文件',
      outputTips: [
        '建议使用简短清晰的水印文字，方便识别文件状态。',
        '透明度高会更醒目，透明度低更适合阅读型文件。',
        '处理完成后会生成新的 PDF 文件，不会修改原文件。',
      ],
      localTitle: '浏览器本地处理',
      localDesc: '水印会在当前浏览器中完成处理，适合快速添加文件状态、版本说明或传阅标记。',
      action: '添加水印',
      successTitle: '水印添加完成',
      successMessage: '带水印的 PDF 已准备好，可以立即下载。',
      placeholder: '例如：草稿 / 已审核 / 仅供预览',
      color: '水印颜色',
      text: '水印文字',
      position: '位置',
      opacity: '透明度',
      rotation: '旋转角度',
      fontSize: '字体大小',
      errorNoText: '请输入水印文字后再继续。',
      errorFailed: '添加水印失败，请稍后重试。',
      processing: '正在生成水印...',
      done: '处理完成',
      defaultText: '仅供预览',
      positions: [
        { value: 'center' as WatermarkPosition, label: '居中' },
        { value: 'tile' as WatermarkPosition, label: '平铺' },
        { value: 'top' as WatermarkPosition, label: '顶部' },
        { value: 'bottom' as WatermarkPosition, label: '底部' },
      ],
    }
  : {
      badge: 'Local tool',
      setupLabel: 'Watermark setup',
      setupTitle: 'Adjust the message and style',
      setupDesc: 'Useful for contracts, reports, drafts, and shared files that need a clear but unobtrusive status mark.',
      outputLabel: 'Output',
      outputTitle: 'Generate a new watermarked file',
      outputTips: [
        'Keep the watermark short and easy to identify.',
        'Higher opacity is more visible, while lower opacity is better for reading-heavy files.',
        'A new PDF is generated after processing. Your original file remains unchanged.',
      ],
      localTitle: 'Local browser processing',
      localDesc: 'The watermark is applied locally in your browser, which fits quick status marks, review labels, and privacy-sensitive documents.',
      action: 'Apply watermark',
      successTitle: 'Watermark applied',
      successMessage: 'Your watermarked PDF is ready to download.',
      placeholder: 'Example: Draft / Reviewed / Preview only',
      color: 'Watermark color',
      text: 'Watermark text',
      position: 'Position',
      opacity: 'Opacity',
      rotation: 'Rotation',
      fontSize: 'Font size',
      errorNoText: 'Enter watermark text before continuing.',
      errorFailed: 'Failed to apply the watermark. Please try again later.',
      processing: 'Applying watermark...',
      done: 'Completed',
      defaultText: 'CONFIDENTIAL',
      positions: [
        { value: 'center' as WatermarkPosition, label: 'Center' },
        { value: 'tile' as WatermarkPosition, label: 'Tile' },
        { value: 'top' as WatermarkPosition, label: 'Top' },
        { value: 'bottom' as WatermarkPosition, label: 'Bottom' },
      ],
    })

watch(isChinese, (zh) => {
  const trimmed = watermarkText.value.trim()
  if (!trimmed || trimmed === 'CONFIDENTIAL' || trimmed === '仅供预览') {
    watermarkText.value = zh ? '仅供预览' : 'CONFIDENTIAL'
  }
}, { immediate: true })

const handleFilesSelected = (files: File[]) => {
  selectedFile.value = files[0]
  errorMessage.value = ''
}

const handleError = (message: string) => {
  errorMessage.value = message
}

const clearAll = () => {
  selectedFile.value = null
  errorMessage.value = ''
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const hexToRgb = (hex: string): { r: number; g: number; b: number } => {
  const normalized = hex.replace('#', '')
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  }
}

const applyWatermark = async () => {
  if (!selectedFile.value) return

  if (!watermarkText.value.trim()) {
    errorMessage.value = copy.value.errorNoText
    return
  }

  isProcessing.value = true
  processingProgress.value = 20
  processingStatus.value = copy.value.processing
  errorMessage.value = ''

  try {
    processingProgress.value = 50
    const blob = await addWatermark(selectedFile.value, {
      text: watermarkText.value,
      opacity: opacity.value,
      rotation: rotation.value,
      fontSize: fontSize.value,
      color: hexToRgb(watermarkColor.value),
      position: position.value,
    })

    processingProgress.value = 100
    processingStatus.value = copy.value.done
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'watermark',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })

    showSuccessModal.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : copy.value.errorFailed
  } finally {
    isProcessing.value = false
    processingProgress.value = 0
    processingStatus.value = ''
  }
}

const downloadResult = () => {
  if (!resultUrl.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = `watermarked-${new Date().toISOString().slice(0, 10)}.pdf`
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
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-pink-50 via-white to-rose-50 dark:from-slate-950 dark:via-slate-950 dark:to-pink-950/20">
    <ToolHeader
      :title="t('tools.watermark.title')"
      :subtitle="t('tools.watermark.desc')"
      :badge="copy.badge"
      accent="pink"
    >
      <template #badgeIcon>
        <FileText class="h-4 w-4" />
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
      <div
        v-if="errorMessage"
        class="mb-4 rounded-lg bg-error-light p-4 text-error-dark dark:bg-error/20 dark:text-error"
      >
        {{ errorMessage }}
      </div>

      <DragDropZone
        v-if="!selectedFile"
        accept="pdf"
        :multiple="false"
        @files-selected="handleFilesSelected"
        @error="handleError"
      />

      <div
        v-else
        class="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]"
      >
        <div class="space-y-6">
          <FilePreview
            :file="selectedFile"
            @remove="clearAll"
            @preview="handlePreview"
          />

          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-pink-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-fuchsia-500">
                  {{ copy.setupLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.setupTitle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.setupDesc }}
                </p>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.text }}
                </label>
                <input
                  v-model="watermarkText"
                  type="text"
                  :placeholder="copy.placeholder"
                  class="w-full rounded-2xl border border-slate-300 px-4 py-3 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.position }}
                </label>
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <button
                    v-for="option in copy.positions"
                    :key="option.value"
                    :class="[
                      'rounded-[18px] border-2 px-3 py-3 text-sm font-medium transition-all',
                      position === option.value
                        ? 'border-primary bg-primary/10 text-primary shadow-sm'
                        : 'border-slate-200 bg-slate-50/70 text-slate-700 hover:border-primary/40 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-300',
                    ]"
                    @click="position = option.value"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.opacity }}: {{ Math.round(opacity * 100) }}%
                </label>
                <input
                  v-model.number="opacity"
                  type="range"
                  min="0.05"
                  max="1"
                  step="0.05"
                  class="w-full accent-primary"
                >
              </div>

              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                    {{ copy.rotation }}: {{ rotation }}°
                  </label>
                  <input
                    v-model.number="rotation"
                    type="range"
                    min="0"
                    max="90"
                    step="5"
                    class="w-full accent-primary"
                  >
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                    {{ copy.fontSize }}: {{ fontSize }}
                  </label>
                  <input
                    v-model.number="fontSize"
                    type="range"
                    min="12"
                    max="100"
                    step="2"
                    class="w-full accent-primary"
                  >
                </div>
              </div>

              <div>
                <label class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.color }}
                </label>
                <input
                  v-model="watermarkColor"
                  type="color"
                  class="h-11 w-24 cursor-pointer rounded-2xl border border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900"
                >
              </div>
            </div>
          </Card>
        </div>

        <div class="space-y-6">
          <div class="rounded-[28px] border border-emerald-100 bg-emerald-50/80 p-5 text-sm leading-6 text-emerald-800 shadow-lg shadow-emerald-100/40 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-300 dark:shadow-none">
            <p class="font-semibold">
              {{ copy.localTitle }}
            </p>
            <p class="mt-2">
              {{ copy.localDesc }}
            </p>
          </div>

          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-pink-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-fuchsia-500">
                  {{ copy.outputLabel }}
                </p>
                <h3 class="mt-2 text-xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.outputTitle }}
                </h3>
              </div>

              <div class="rounded-[24px] border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/40">
                <ul class="space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  <li
                    v-for="tip in copy.outputTips"
                    :key="tip"
                  >
                    {{ tip }}
                  </li>
                </ul>
              </div>

              <ProgressBar
                v-if="isProcessing"
                :progress="processingProgress"
                :label="processingStatus"
                variant="primary"
                size="md"
              />

              <Button
                variant="primary"
                size="lg"
                :loading="isProcessing"
                full-width
                @click="applyWatermark"
              >
                {{ isProcessing ? t('common.processing') : copy.action }}
              </Button>
            </div>
          </Card>
        </div>
      </div>

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

      <Modal
        v-model="showSuccessModal"
        :title="copy.successTitle"
        size="md"
      >
        <div class="text-center">
          <p class="mb-6 text-gray-600 dark:text-gray-300">
            {{ copy.successMessage }}
          </p>
          <Button
            variant="primary"
            size="lg"
            full-width
            @click="downloadResult"
          >
            {{ t('common.download') }}
          </Button>
        </div>
      </Modal>
    </section>
  </div>
</template>
