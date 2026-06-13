<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  BadgeCheck,
  Download,
  FileSignature,
  ImagePlus,
  PenLine,
  ShieldCheck,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { addVisualSignature } from '@/utils/pdf/signature'
import { getPDFPageCount } from '@/utils/pdf/merge'
import { historyManager } from '@/utils/history-manager'
import { memoryManager } from '@/utils/memory-manager'

const { tm } = useI18n()

const pdfFile = ref<File | null>(null)
const signatureFile = ref<File | null>(null)
const signaturePreviewUrl = ref('')
const pageCount = ref(0)
const pageNumber = ref(1)
const xPercent = ref(68)
const yPercent = ref(72)
const widthPercent = ref(22)
const opacity = ref(1)
const isProcessing = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const errorMessage = ref('')

type ToolPageCopy = Record<string, any>

const copy = computed<ToolPageCopy>(() => tm('tools.sign.page') as ToolPageCopy)
const canSign = computed(() => !!pdfFile.value && !!signatureFile.value && !isProcessing.value)

const handlePDFSelected = async (files: File[]) => {
  try {
    clearResult()
    pdfFile.value = files[0]
    pageCount.value = await getPDFPageCount(files[0])
    pageNumber.value = Math.min(pageNumber.value, pageCount.value || 1)
    errorMessage.value = ''
  } catch {
    pdfFile.value = null
    pageCount.value = 0
    errorMessage.value = copy.value.errorPdf
  }
}

const handleSignatureSelected = (files: File[]) => {
  const file = files[0]
  if (!file) return
  clearSignaturePreview()
  clearResult()
  signatureFile.value = file
  signaturePreviewUrl.value = URL.createObjectURL(file)
  errorMessage.value = ''
}

const clearSignaturePreview = () => {
  if (signaturePreviewUrl.value) {
    URL.revokeObjectURL(signaturePreviewUrl.value)
    signaturePreviewUrl.value = ''
  }
}

const clearResult = () => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const removePDF = () => {
  pdfFile.value = null
  pageCount.value = 0
  clearResult()
}

const removeSignature = () => {
  signatureFile.value = null
  clearSignaturePreview()
  clearResult()
}

const handleError = (message: string) => {
  errorMessage.value = message
}

const signPDF = async () => {
  if (!pdfFile.value) return
  if (!signatureFile.value) {
    errorMessage.value = copy.value.errorSignature
    return
  }

  isProcessing.value = true
  progress.value = 18
  status.value = copy.value.processing
  errorMessage.value = ''
  clearResult()

  try {
    progress.value = 56
    const blob = await addVisualSignature(pdfFile.value, signatureFile.value, {
      pageNumber: pageNumber.value,
      xPercent: xPercent.value,
      yPercent: yPercent.value,
      widthPercent: widthPercent.value,
      opacity: opacity.value,
    })

    progress.value = 100
    status.value = copy.value.done
    resultUrl.value = memoryManager.createTemporaryURL(blob)

    historyManager.addHistory({
      type: 'sign',
      fileName: pdfFile.value.name,
      fileSize: pdfFile.value.size,
      resultSize: blob.size,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : copy.value.errorFailed
  } finally {
    isProcessing.value = false
  }
}

const downloadResult = () => {
  if (!resultUrl.value || !pdfFile.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = pdfFile.value.name.replace(/\.pdf$/i, '') + '-signed.pdf'
  link.click()
}

onUnmounted(() => {
  clearSignaturePreview()
  clearResult()
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
        <PenLine class="h-4 w-4" />
      </template>
      <ToolNoticeBar variant="amber">
        <template #icon>
          <ShieldCheck class="h-5 w-5" />
        </template>
        {{ copy.notice }}
      </ToolNoticeBar>

      <div
        v-if="errorMessage"
        class="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-700 shadow-sm dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-100"
      >
        {{ errorMessage }}
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[1fr_0.95fr]">
        <div class="space-y-6">
          <Card class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-600">
                  {{ copy.pdfLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ pdfFile ? copy.pdfTitleReady : copy.pdfTitleIdle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ pdfFile ? copy.pdfDescReady : copy.pdfDescIdle }}
                </p>
              </div>

              <DragDropZone
                v-if="!pdfFile"
                accept="pdf"
                :multiple="false"
                :max-files="1"
                @files-selected="handlePDFSelected"
                @error="handleError"
              >
                <template #icon>
                  <FileSignature class="h-12 w-12" />
                </template>
                <template #title>
                  {{ copy.pdfDropTitle }}
                </template>
                <template #subtitle>
                  {{ copy.dropSubtitle }}
                </template>
              </DragDropZone>

              <FilePreview
                v-else
                :file="pdfFile"
                @remove="removePDF"
              />
            </div>
          </Card>

          <Card
            v-if="pdfFile"
            class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
          >
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-orange-600">
                  {{ copy.signLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ signatureFile ? copy.signTitleReady : copy.signTitleIdle }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ signatureFile ? copy.signDescReady : copy.signDescIdle }}
                </p>
              </div>

              <DragDropZone
                v-if="!signatureFile"
                accept="image"
                :multiple="false"
                :max-files="1"
                :max-size="20"
                @files-selected="handleSignatureSelected"
                @error="handleError"
              >
                <template #icon>
                  <ImagePlus class="h-12 w-12" />
                </template>
                <template #title>
                  {{ copy.imageDropTitle }}
                </template>
                <template #subtitle>
                  {{ copy.dropSubtitle }}
                </template>
              </DragDropZone>

              <div
                v-else
                class="flex items-center gap-4 rounded-[22px] border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40"
              >
                <div class="flex h-20 w-32 items-center justify-center rounded-md bg-white p-3 dark:bg-slate-900">
                  <img
                    :src="signaturePreviewUrl"
                    alt=""
                    class="max-h-full max-w-full object-contain"
                  >
                </div>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                    {{ signatureFile.name }}
                  </p>
                  <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {{ Math.round(signatureFile.size / 1024) }} KB
                  </p>
                </div>
                <button
                  class="rounded-full px-3 py-2 text-sm font-semibold text-rose-600 hover:bg-rose-50 dark:text-rose-300 dark:hover:bg-rose-500/10"
                  type="button"
                  @click="removeSignature"
                >
                  {{ copy.remove }}
                </button>
              </div>
            </div>
          </Card>

          <Card
            v-if="pdfFile && signatureFile"
            class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
          >
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-600">
                  {{ copy.settingsLabel }}
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.settingsTitle }}
                </h2>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.page }}</span>
                  <input
                    v-model.number="pageNumber"
                    type="number"
                    min="1"
                    :max="pageCount || 1"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-amber-500 focus:outline-none focus:ring-4 focus:ring-amber-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.width }}: {{ widthPercent }}%</span>
                  <input
                    v-model.number="widthPercent"
                    type="range"
                    min="8"
                    max="50"
                    step="1"
                    class="w-full accent-amber-500"
                  >
                </label>
              </div>

              <div class="grid gap-4 sm:grid-cols-3">
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.x }}: {{ xPercent }}%</span>
                  <input
                    v-model.number="xPercent"
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    class="w-full accent-amber-500"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.y }}: {{ yPercent }}%</span>
                  <input
                    v-model.number="yPercent"
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    class="w-full accent-amber-500"
                  >
                </label>
                <label class="block">
                  <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">{{ copy.opacity }}: {{ Math.round(opacity * 100) }}%</span>
                  <input
                    v-model.number="opacity"
                    type="range"
                    min="0.2"
                    max="1"
                    step="0.05"
                    class="w-full accent-amber-500"
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
                  :disabled="!canSign"
                  full-width
                  @click="signPDF"
                >
                  <PenLine class="mr-2 h-4 w-4" />
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
          <Card
            v-if="pdfFile"
            class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
          >
            <div class="space-y-5">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-600">
                  {{ copy.previewLabel }}
                </p>
                <h3 class="mt-2 text-xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.previewTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.previewHint }}
                </p>
              </div>

              <div class="rounded-lg border border-amber-100 bg-gradient-to-br from-amber-50 to-orange-50 p-5 dark:border-amber-500/20 dark:from-amber-500/10 dark:to-orange-500/10">
                <div class="relative mx-auto aspect-[3/4] max-w-[340px] overflow-hidden rounded-md border border-white/80 bg-white shadow-inner dark:border-white/10 dark:bg-slate-950/50">
                  <div class="absolute left-7 right-7 top-8 space-y-3">
                    <div class="h-4 rounded-full bg-slate-200 dark:bg-slate-700" />
                    <div class="h-3 w-4/5 rounded-full bg-slate-100 dark:bg-slate-800" />
                    <div class="h-3 w-3/5 rounded-full bg-slate-100 dark:bg-slate-800" />
                  </div>
                  <div class="absolute bottom-8 left-7 right-7 h-px bg-slate-200 dark:bg-slate-700" />
                  <div
                    class="absolute rounded-xl border border-amber-300/70 bg-white/70 p-1 shadow-sm dark:border-amber-300/30 dark:bg-slate-900/70 dark:shadow-none"
                    :style="{
                      left: `${Math.min(xPercent, 82)}%`,
                      top: `${Math.min(yPercent, 88)}%`,
                      width: `${widthPercent}%`,
                      opacity,
                    }"
                  >
                    <img
                      v-if="signaturePreviewUrl"
                      :src="signaturePreviewUrl"
                      alt=""
                      class="w-full object-contain"
                    >
                    <div
                      v-else
                      class="flex h-10 items-center justify-center rounded-lg border border-dashed border-amber-300 text-xs font-semibold text-amber-700 dark:text-amber-200"
                    >
                      Signature
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card
            v-if="pdfFile"
            class="rounded-lg border border-emerald-200 bg-emerald-50/90 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
          >
            <div class="flex items-start gap-4">
              <BadgeCheck class="mt-0.5 h-6 w-6 shrink-0 text-emerald-500" />
              <div>
                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                  {{ resultUrl ? copy.successTitle : copy.localTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ resultUrl ? copy.successMessage : copy.localDesc }}
                </p>
                <Button
                  v-if="resultUrl"
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
  </ToolPageShell>
</template>
