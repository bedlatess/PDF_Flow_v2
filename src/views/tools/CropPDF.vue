<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  BadgeCheck,
  Crop,
  Download,
  Eye,
  ShieldAlert,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import ToolHeader from '@/components/tools/ToolHeader.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { cropPDF } from '@/utils/pdf/crop'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { historyManager } from '@/utils/history-manager'
import { memoryManager } from '@/utils/memory-manager'

const { locale } = useI18n()

const selectedFile = ref<File | null>(null)
const pageCount = ref(0)
const topPercent = ref(4)
const rightPercent = ref(4)
const bottomPercent = ref(4)
const leftPercent = ref(4)
const isProcessing = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const errorMessage = ref('')

const isZh = computed(() => locale.value.toLowerCase().startsWith('zh'))
const isEs = computed(() => locale.value.toLowerCase().startsWith('es'))

const copy = computed(() => {
  if (isZh.value) {
    return {
      title: '裁剪 PDF',
      subtitle: '去掉页面边缘空白、扫描黑边或多余留白，让文档阅读、打印和分享更干净。',
      badge: '本地工具',
      notice: '裁剪只调整 PDF 的可视区域，不等于永久删除敏感信息。不要用它遮盖身份证号、手机号或合同金额；真正脱敏请等待后续“涂黑敏感信息”工具。',
      uploadLabel: 'PDF 文件',
      uploadTitleIdle: '选择需要裁剪的 PDF',
      uploadTitleReady: '文件已准备好',
      uploadDescriptionIdle: '适合去除白边、扫描边框和页面四周多余区域。原文件不会被修改。',
      uploadDescriptionReady: '设置上下左右裁剪比例后，会生成新的裁剪副本。',
      dropTitle: '拖放 PDF 到这里',
      dropSubtitle: '或点击选择文件',
      settingsLabel: '裁剪设置',
      settingsTitle: '设置四周裁剪比例',
      top: '上边',
      right: '右边',
      bottom: '下边',
      left: '左边',
      quick: '快速方案',
      small: '轻微去白边',
      scan: '扫描黑边',
      reset: '重置',
      previewLabel: '可视预览',
      previewTitle: '保留区域',
      previewHint: '预览用于确认大致边距，最终效果以导出的 PDF 为准。',
      action: '生成裁剪 PDF',
      processing: '正在应用裁剪...',
      done: '裁剪副本已生成',
      download: '下载裁剪 PDF',
      successTitle: '裁剪完成',
      successMessage: '新的 PDF 已应用可视区域裁剪，可以下载检查。',
      localTitle: '适合整理版面，不适合脱敏',
      localDesc: '裁剪能让页面更紧凑，但被裁掉的区域可能仍存在于 PDF 文件结构中。涉及隐私或敏感内容时，请使用真正的脱敏工具。',
      pages: '页数',
      errorLoad: '无法读取这份 PDF，请重新选择文件后再试。',
      errorFailed: '裁剪失败，请检查裁剪比例后再试。',
    }
  }

  if (isEs.value) {
    return {
      title: 'Recortar PDF',
      subtitle: 'Quita bordes, margenes grandes o sombras de escaneo para que el documento se vea mas limpio.',
      badge: 'Herramienta local',
      notice: 'Recortar solo ajusta el area visible del PDF; no elimina informacion sensible de forma segura. Para ocultar datos privados, usa una herramienta de redaccion real.',
      uploadLabel: 'Archivo PDF',
      uploadTitleIdle: 'Elige el PDF para recortar',
      uploadTitleReady: 'Archivo listo',
      uploadDescriptionIdle: 'Ideal para quitar bordes blancos, sombras de escaneo y margenes innecesarios.',
      uploadDescriptionReady: 'Define los margenes y crea una copia recortada.',
      dropTitle: 'Arrastra tu PDF aqui',
      dropSubtitle: 'o haz clic para elegir un archivo',
      settingsLabel: 'Recorte',
      settingsTitle: 'Ajusta los margenes',
      top: 'Arriba',
      right: 'Derecha',
      bottom: 'Abajo',
      left: 'Izquierda',
      quick: 'Preajustes',
      small: 'Margen ligero',
      scan: 'Borde escaneado',
      reset: 'Restablecer',
      previewLabel: 'Vista previa',
      previewTitle: 'Area conservada',
      previewHint: 'La vista previa es aproximada; el PDF exportado es el resultado final.',
      action: 'Crear PDF recortado',
      processing: 'Aplicando recorte...',
      done: 'Copia recortada lista',
      download: 'Descargar PDF recortado',
      successTitle: 'Recorte listo',
      successMessage: 'La nueva copia recortada esta lista para revisar.',
      localTitle: 'Para limpiar bordes, no para redaccion segura',
      localDesc: 'El recorte mejora la vista, pero el contenido recortado puede seguir dentro de la estructura PDF.',
      pages: 'Paginas',
      errorLoad: 'No se pudo leer este PDF. Elige el archivo de nuevo.',
      errorFailed: 'No se pudo recortar el PDF. Revisa los margenes e intenta de nuevo.',
    }
  }

  return {
    title: 'Crop PDF',
    subtitle: 'Remove page edges, scan shadows, and extra whitespace for cleaner reading, printing, and sharing.',
    badge: 'Local tool',
    notice: 'Cropping only changes the visible PDF area. It is not secure redaction. Do not use it to hide ID numbers, phone numbers, or contract values; use a true redaction workflow for sensitive content.',
    uploadLabel: 'PDF file',
    uploadTitleIdle: 'Choose the PDF to crop',
    uploadTitleReady: 'File is ready',
    uploadDescriptionIdle: 'Best for trimming whitespace, scan borders, and extra page edges. The original file is not modified.',
    uploadDescriptionReady: 'Set the top, right, bottom, and left crop margins to export a new copy.',
    dropTitle: 'Drop your PDF here',
    dropSubtitle: 'or click to choose a file',
    settingsLabel: 'Crop setup',
    settingsTitle: 'Set crop margins',
    top: 'Top',
    right: 'Right',
    bottom: 'Bottom',
    left: 'Left',
    quick: 'Presets',
    small: 'Light trim',
    scan: 'Scan border',
    reset: 'Reset',
    previewLabel: 'Visual preview',
    previewTitle: 'Kept area',
    previewHint: 'The preview confirms approximate margins; the exported PDF is the final result.',
    action: 'Create cropped PDF',
    processing: 'Applying crop...',
    done: 'Cropped copy is ready',
    download: 'Download cropped PDF',
    successTitle: 'Crop complete',
    successMessage: 'Your new cropped PDF is ready to review.',
    localTitle: 'For layout cleanup, not redaction',
    localDesc: 'Cropping makes pages cleaner, but cropped content may still exist in the PDF structure. Use true redaction for sensitive information.',
    pages: 'Pages',
    errorLoad: 'Could not read this PDF. Please choose the file again.',
    errorFailed: 'Failed to crop the PDF. Please check the margins and try again.',
  }
})

const canCrop = computed(() => !!selectedFile.value && !isProcessing.value)

const cropStyle = computed(() => ({
  left: `${leftPercent.value}%`,
  right: `${rightPercent.value}%`,
  top: `${topPercent.value}%`,
  bottom: `${bottomPercent.value}%`,
}))

const handleFilesSelected = async (files: File[]) => {
  try {
    clearResult()
    selectedFile.value = files[0]
    pageCount.value = await getPDFPageCount(files[0])
    errorMessage.value = ''
  } catch {
    selectedFile.value = null
    pageCount.value = 0
    errorMessage.value = copy.value.errorLoad
  }
}

const handleError = (message: string) => {
  errorMessage.value = message
}

const clearResult = () => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const removeFile = () => {
  selectedFile.value = null
  pageCount.value = 0
  errorMessage.value = ''
  clearResult()
}

const setPreset = (value: number) => {
  topPercent.value = value
  rightPercent.value = value
  bottomPercent.value = value
  leftPercent.value = value
  clearResult()
}

const crop = async () => {
  if (!selectedFile.value) return

  isProcessing.value = true
  progress.value = 20
  status.value = copy.value.processing
  errorMessage.value = ''
  clearResult()

  try {
    progress.value = 65
    const blob = await cropPDF(selectedFile.value, {
      topPercent: topPercent.value,
      rightPercent: rightPercent.value,
      bottomPercent: bottomPercent.value,
      leftPercent: leftPercent.value,
    })
    progress.value = 100
    status.value = copy.value.done
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'crop',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })
  } catch {
    errorMessage.value = copy.value.errorFailed
  } finally {
    isProcessing.value = false
  }
}

const downloadResult = () => {
  if (!resultUrl.value || !selectedFile.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = selectedFile.value.name.replace(/\.pdf$/i, '') + '-cropped.pdf'
  link.click()
}

onUnmounted(clearResult)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-lime-50 via-white to-emerald-50 dark:from-slate-950 dark:via-slate-950 dark:to-lime-950/20">
    <ToolHeader
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="emerald"
    >
      <template #badgeIcon>
        <Crop class="h-4 w-4" />
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-6xl px-4 pb-16 pt-6">
      <ToolNoticeBar variant="amber">
        <template #icon>
          <ShieldAlert class="h-5 w-5" />
        </template>
        {{ copy.notice }}
      </ToolNoticeBar>

      <div
        v-if="errorMessage"
        class="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-700 shadow-sm dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-100"
      >
        {{ errorMessage }}
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div class="space-y-6">
          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-lime-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                  {{ copy.uploadLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ selectedFile ? copy.uploadTitleReady : copy.uploadTitleIdle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ selectedFile ? copy.uploadDescriptionReady : copy.uploadDescriptionIdle }}
                </p>
              </div>

              <DragDropZone
                v-if="!selectedFile"
                accept="pdf"
                :multiple="false"
                :max-files="1"
                @files-selected="handleFilesSelected"
                @error="handleError"
              >
                <template #icon>
                  <Crop class="h-12 w-12" />
                </template>
                <template #title>
                  {{ copy.dropTitle }}
                </template>
                <template #subtitle>
                  {{ copy.dropSubtitle }}
                </template>
              </DragDropZone>

              <FilePreview
                v-else
                :file="selectedFile"
                @remove="removeFile"
              />
            </div>
          </Card>

          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-lime-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                  {{ copy.settingsLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.settingsTitle }}
                </h2>
              </div>

              <div class="grid gap-3 sm:grid-cols-3">
                <button
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200"
                  type="button"
                  @click="setPreset(3)"
                >
                  {{ copy.small }}
                </button>
                <button
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200"
                  type="button"
                  @click="setPreset(8)"
                >
                  {{ copy.scan }}
                </button>
                <button
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200"
                  type="button"
                  @click="setPreset(0)"
                >
                  {{ copy.reset }}
                </button>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <label
                  v-for="item in [
                    { key: 'top', label: copy.top, model: topPercent },
                    { key: 'right', label: copy.right, model: rightPercent },
                    { key: 'bottom', label: copy.bottom, model: bottomPercent },
                    { key: 'left', label: copy.left, model: leftPercent },
                  ]"
                  :key="item.key"
                  class="block"
                >
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                    {{ item.label }}: {{ item.model }}%
                  </span>
                  <input
                    v-model.number="item.model"
                    type="range"
                    min="0"
                    max="35"
                    step="1"
                    class="w-full accent-emerald-500"
                    @input="clearResult"
                  >
                </label>
              </div>

              <ProgressBar
                v-if="isProcessing || resultUrl"
                :progress="progress"
                :label="status"
                variant="primary"
                size="md"
              />

              <div class="flex flex-col gap-3 sm:flex-row">
                <Button
                  variant="primary"
                  size="lg"
                  :loading="isProcessing"
                  :disabled="!canCrop"
                  full-width
                  @click="crop"
                >
                  <Crop class="mr-2 h-4 w-4" />
                  {{ isProcessing ? copy.processing : copy.action }}
                </Button>
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
              </div>
            </div>
          </Card>
        </div>

        <div class="space-y-6">
          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-lime-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                  {{ copy.previewLabel }}
                </p>
                <h3 class="mt-2 text-xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.previewTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.previewHint }}
                </p>
              </div>

              <div class="rounded-[28px] border border-emerald-100 bg-gradient-to-br from-lime-50 to-emerald-50 p-6 dark:border-emerald-500/20 dark:from-emerald-500/10 dark:to-lime-500/10">
                <div class="relative mx-auto aspect-[3/4] max-w-[360px] overflow-hidden rounded-[26px] border border-white/80 bg-white shadow-inner dark:border-white/10 dark:bg-slate-950/50">
                  <div class="absolute left-8 right-8 top-9 space-y-3">
                    <div class="h-4 rounded-full bg-slate-200 dark:bg-slate-700" />
                    <div class="h-3 w-5/6 rounded-full bg-slate-100 dark:bg-slate-800" />
                    <div class="h-3 w-2/3 rounded-full bg-slate-100 dark:bg-slate-800" />
                  </div>
                  <div class="absolute bottom-10 left-8 right-8 grid grid-cols-3 gap-3">
                    <div class="h-16 rounded-2xl bg-emerald-100 dark:bg-emerald-500/20" />
                    <div class="h-16 rounded-2xl bg-lime-100 dark:bg-lime-500/20" />
                    <div class="h-16 rounded-2xl bg-sky-100 dark:bg-sky-500/20" />
                  </div>
                  <div class="absolute inset-0 bg-slate-950/35" />
                  <div
                    class="absolute rounded-[20px] border-2 border-emerald-400 bg-white/82 shadow-2xl shadow-emerald-200/60 dark:bg-slate-900/70 dark:shadow-none"
                    :style="cropStyle"
                  />
                </div>
              </div>
            </div>
          </Card>

          <Card class="rounded-[28px] border border-amber-200 bg-amber-50/90 shadow-xl shadow-amber-100/70 dark:border-amber-900/40 dark:bg-amber-950/20 dark:shadow-none">
            <div class="flex items-start gap-4">
              <ShieldAlert class="mt-0.5 h-6 w-6 shrink-0 text-amber-600 dark:text-amber-300" />
              <div>
                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                  {{ copy.localTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.localDesc }}
                </p>
                <p
                  v-if="selectedFile"
                  class="mt-3 inline-flex items-center rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-slate-900/60 dark:text-emerald-200"
                >
                  <Eye class="mr-1.5 h-3.5 w-3.5" />
                  {{ copy.pages }}: {{ pageCount }}
                </p>
              </div>
            </div>
          </Card>

          <Card
            v-if="resultUrl"
            class="rounded-[28px] border border-emerald-200 bg-emerald-50/90 shadow-xl shadow-emerald-100/70 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
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
                <Button
                  class="mt-4"
                  variant="primary"
                  @click="downloadResult"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ copy.download }}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  </div>
</template>
