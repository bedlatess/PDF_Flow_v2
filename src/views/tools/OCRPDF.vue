<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Copy,
  Crown,
  Download,
  FileSearch,
  Languages,
  Sparkles,
} from 'lucide-vue-next'
import { fileAPI } from '@/services/api'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolHeader from '@/components/tools/ToolHeader.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const selectedFile = ref<File | null>(null)
const selectedLanguage = ref('eng')
const isProcessing = ref(false)
const processingProgress = ref(0)
const processingStatus = ref('')
const showResultModal = ref(false)
const extractedText = ref('')
const ocrResult = ref<any>(null)
const errorState = ref<FormattedUserError | null>(null)
const copyMessage = ref('')

const canUseOCR = computed(() => userStore.isAuthenticated && userStore.canUseCloudFeatures)

const languageOptions = [
  { value: 'eng', label: 'English', code: 'EN' },
  { value: 'chi_sim', label: 'Simplified Chinese', code: 'ZH-CN' },
  { value: 'chi_tra', label: 'Traditional Chinese', code: 'ZH-TW' },
  { value: 'jpn', label: 'Japanese', code: 'JP' },
  { value: 'kor', label: 'Korean', code: 'KR' },
  { value: 'fra', label: 'French', code: 'FR' },
  { value: 'deu', label: 'German', code: 'DE' },
  { value: 'spa', label: 'Spanish', code: 'ES' },
]

const primaryActionLabel = computed(() => {
  if (!userStore.isAuthenticated) {
    return 'Sign in to use OCR'
  }

  if (!userStore.canUseCloudFeatures) {
    return 'Upgrade to Pro for OCR'
  }

  return isProcessing.value ? 'Running OCR...' : 'Start OCR'
})

const ensureAccess = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
  canUseCloudFeatures: userStore.canUseCloudFeatures,
  requiresPro: true,
  pricingFeature: 'ocr',
})

const handleFilesSelected = (files: File[]) => {
  if (files.length === 0) {
    return
  }

  selectedFile.value = files[0]
  errorState.value = null
  copyMessage.value = ''
  extractedText.value = ''
  ocrResult.value = null
}

const handleError = (message: string) => {
  errorState.value = formatUserFacingError(new Error(message), {
    area: 'UPLOAD',
    fallbackMessage: message,
  })
}

const clearAll = () => {
  selectedFile.value = null
  extractedText.value = ''
  ocrResult.value = null
  errorState.value = null
  copyMessage.value = ''
}

const performOCR = async () => {
  if (!selectedFile.value) {
    return
  }

  if (!ensureAccess()) {
    return
  }

  isProcessing.value = true
  processingProgress.value = 0
  processingStatus.value = 'Uploading file...'
  errorState.value = null
  copyMessage.value = ''

  try {
    const uploaded = await fileAPI.uploadFile(selectedFile.value)
    processingProgress.value = 25
    processingStatus.value = 'Submitting OCR job...'

    const job = await fileAPI.extractTextOCR(uploaded.file_id, selectedLanguage.value)
    processingProgress.value = 38
    processingStatus.value = 'Recognizing text...'

    const finalStatus = await fileAPI.pollJobUntilDone(job.job_id, (status) => {
      if (typeof status.progress === 'number') {
        processingProgress.value = Math.max(38, Math.min(92, status.progress))
      }

      processingStatus.value = status.status === 'pending'
        ? 'Waiting in queue...'
        : 'Recognizing text...'
    })

    if (finalStatus.status === 'failed') {
      throw new Error(finalStatus.error || 'OCR failed')
    }

    processingProgress.value = 96
    processingStatus.value = 'Preparing results...'

    const blob = await fileAPI.downloadResult(job.job_id)
    const text = await blob.text()

    extractedText.value = text

    try {
      ocrResult.value = JSON.parse(text)
      if (ocrResult.value.text) {
        extractedText.value = ocrResult.value.text
      }
    } catch {
      ocrResult.value = {
        text,
        page_count: 1,
        language: selectedLanguage.value,
      }
    }

    processingProgress.value = 100
    processingStatus.value = 'OCR complete'
    showResultModal.value = true
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'OCR',
      fallbackMessage: 'OCR could not finish successfully. Please try again.',
    })
  } finally {
    isProcessing.value = false
  }
}

const downloadText = () => {
  if (!extractedText.value) {
    return
  }

  const blob = new Blob([extractedText.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `ocr-${new Date().toISOString().slice(0, 10)}.txt`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(extractedText.value)
    copyMessage.value = 'Copied to clipboard.'
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'OCR',
      fallbackMessage: 'Copy failed. Please select the text manually and copy it.',
    })
  }
}

const closeResultModal = () => {
  showResultModal.value = false
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 dark:from-slate-950 dark:via-slate-950 dark:to-purple-950/20">
    <ToolHeader
      title="OCR Text Recognition"
      subtitle="Extract text from PDFs and images with a login-first cloud workflow and clearer diagnostic feedback."
      badge="Pro cloud feature"
      accent="purple"
    >
      <template #badgeIcon>
        <Sparkles class="h-4 w-4" />
      </template>

      <template #extra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          One upload area, one language selector, and one result view so users can finish OCR without bouncing between duplicate panels.
        </p>
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
      <ToolNoticeBar variant="amber">
        <template #icon>
          <Crown class="h-5 w-5" />
        </template>
        OCR follows the same access pattern as the rest of the premium tools: sign in first, then check whether your account includes Pro cloud access.
      </ToolNoticeBar>

      <DiagnosticAlert
        v-if="errorState"
        class="mt-6"
        :title="errorState.title"
        :message="errorState.message"
        :diagnostic-code="errorState.diagnosticCode"
        :support-hint="errorState.supportHint"
      />

      <div
        v-if="!canUseOCR"
        class="mt-6"
      >
        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div class="space-y-4">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                Access
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ userStore.isAuthenticated ? 'Upgrade required after login' : 'Sign in before text recognition' }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ userStore.isAuthenticated
                  ? 'Your account is active, but OCR runs as a Pro cloud workflow. Upgrade only when you need cloud text extraction.'
                  : 'Please sign in first so the app can verify your account before deciding whether an upgrade is actually required.' }}
              </p>

              <Button
                size="lg"
                @click="ensureAccess()"
              >
                <Crown class="mr-2 h-4 w-4" />
                {{ userStore.isAuthenticated ? 'Go to upgrade' : 'Go to sign in' }}
              </Button>
            </div>

            <div class="rounded-[24px] border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
              <div class="space-y-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  1. Sign in first
                </div>
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  2. Upload one PDF or image source
                </div>
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  3. Run OCR and export plain text
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                Upload
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ selectedFile ? 'Current OCR source file' : 'Upload a PDF or image' }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ selectedFile ? 'Switch language after upload, then run one OCR task from the same workspace.' : 'Supports PDF, PNG, JPG, JPEG, and WEBP. Single-file OCR keeps the result easier to validate.' }}
              </p>
            </div>

            <DragDropZone
              v-if="!selectedFile"
              accept="application/pdf,.pdf,image/*,.png,.jpg,.jpeg,.webp"
              :multiple="false"
              :max-files="1"
              @files-selected="handleFilesSelected"
              @error="handleError"
            >
              <template #icon>
                <FileSearch class="h-12 w-12" />
              </template>
              <template #title>
                Drop a file to start OCR
              </template>
              <template #subtitle>
                PDFs and common image formats are supported in the same flow.
              </template>
            </DragDropZone>

            <div v-else class="space-y-5">
              <FilePreview
                :file="selectedFile"
                @remove="clearAll"
              />

              <ProgressBar
                v-if="isProcessing"
                :progress="processingProgress"
                :label="processingStatus"
                variant="primary"
                size="md"
              />

              <Button
                size="lg"
                full-width
                :loading="isProcessing"
                @click="performOCR"
              >
                {{ primaryActionLabel }}
              </Button>
            </div>
          </div>
        </Card>

        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div class="flex flex-wrap gap-2">
              <span class="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 dark:border-purple-800 dark:bg-purple-950/30 dark:text-purple-200">
                <Languages class="h-4 w-4" />
                Language
              </span>
              <span class="inline-flex items-center gap-2 rounded-full border border-fuchsia-200 bg-fuchsia-50 px-4 py-2 text-sm font-medium text-fuchsia-700 dark:border-fuchsia-800 dark:bg-fuchsia-950/30 dark:text-fuchsia-200">
                <Sparkles class="h-4 w-4" />
                Cloud OCR
              </span>
              <span class="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-200">
                <Download class="h-4 w-4" />
                TXT export
              </span>
            </div>

            <div class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  OCR workspace
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  Keep recognition language, account state, and export actions in one aligned workspace instead of splitting them into unrelated cards.
                </p>
              </div>

              <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <div class="flex items-center gap-2">
                  <Languages class="h-5 w-5 text-purple-500" />
                  <label class="text-sm font-semibold text-slate-900 dark:text-white">
                    Recognition language
                  </label>
                </div>

                <div class="mt-4 grid gap-3 sm:grid-cols-2">
                  <button
                    v-for="lang in languageOptions"
                    :key="lang.value"
                    :class="[
                      'rounded-2xl border px-4 py-4 text-left transition-all',
                      selectedLanguage === lang.value
                        ? 'border-purple-300 bg-purple-50 shadow-sm dark:border-purple-700 dark:bg-purple-950/30'
                        : 'border-slate-200 bg-white hover:border-purple-200 dark:border-slate-700 dark:bg-slate-900',
                    ]"
                    @click="selectedLanguage = lang.value"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="font-semibold text-slate-900 dark:text-white">
                          {{ lang.label }}
                        </p>
                        <p class="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                          {{ lang.code }}
                        </p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 px-4 py-4 dark:border-slate-800 dark:bg-slate-950/50">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">
                  {{ userStore.isAuthenticated ? 'Signed-in account detected' : 'Not signed in yet' }}
                </p>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ canUseOCR ? 'This account can start OCR jobs right away.' : 'Please sign in first, then upgrade to Pro if you want to unlock OCR cloud processing.' }}
                </p>
              </div>

              <Button
                v-if="!canUseOCR"
                variant="outline"
                size="lg"
                full-width
                @click="ensureAccess()"
              >
                {{ userStore.isAuthenticated ? 'Go to upgrade' : 'Go to sign in' }}
              </Button>

              <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">
                  Recognition flow
                </p>
                <div class="mt-4 space-y-3">
                  <div class="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-purple-500 text-sm font-semibold text-white">1</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      Upload a PDF or image and confirm the source file looks correct.
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-fuchsia-500 text-sm font-semibold text-white">2</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      Choose the nearest language to improve recognition quality.
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-semibold text-white">3</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      Copy the extracted text or download it as a plain text file.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Modal
        v-model="showResultModal"
        title="OCR result"
        size="lg"
      >
        <div class="space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-4 dark:bg-slate-800">
            <div class="text-sm text-slate-600 dark:text-slate-300">
              <span v-if="ocrResult?.page_count">Pages: {{ ocrResult.page_count }}</span>
              <span
                v-if="ocrResult?.average_confidence"
                class="ml-4"
              >
                Confidence: {{ ocrResult.average_confidence }}%
              </span>
            </div>

            <div class="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                @click="copyToClipboard"
              >
                <Copy class="mr-2 h-4 w-4" />
                Copy
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="downloadText"
              >
                <Download class="mr-2 h-4 w-4" />
                Download
              </Button>
            </div>
          </div>

          <div
            v-if="copyMessage"
            class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-200"
          >
            {{ copyMessage }}
          </div>

          <div class="max-h-96 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <pre class="whitespace-pre-wrap text-sm leading-6 text-slate-800 dark:text-slate-200">{{ extractedText }}</pre>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Button
              variant="outline"
              size="md"
              @click="closeResultModal"
            >
              Close
            </Button>
            <Button
              size="md"
              @click="clearAll(); closeResultModal()"
            >
              Recognize another file
            </Button>
          </div>
        </div>
      </Modal>
    </section>
  </div>
</template>
