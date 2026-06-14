<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
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
import Modal from '@/components/common/Modal.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

const { t, tm } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const selectedFile = ref<File | null>(null)
type ToolPageCopy = Record<string, any>

const copy = computed<ToolPageCopy>(() => tm('tools.ocr') as ToolPageCopy)

const selectedLanguage = ref(String(copy.value.defaultLanguage || 'eng'))
const isProcessing = ref(false)
const processingProgress = ref(0)
const processingStatus = ref('')
const showResultModal = ref(false)
const extractedText = ref('')
const ocrResult = ref<any>(null)
const errorState = ref<FormattedUserError | null>(null)
const copyMessage = ref('')

const canUseOCR = computed(() => userStore.isAuthenticated && userStore.canUseCloudFeatures)

const selectedLanguageLabel = computed(() =>
  languageOptions.value.find((item) => item.value === selectedLanguage.value)?.label || selectedLanguage.value
)

const resultPreview = computed(() => {
  const text = extractedText.value.trim()
  if (!text) return ''
  return text.length > 900 ? `${text.slice(0, 900)}...` : text
})

const viewResultLabel = computed(() => t('tools.ocr.viewFullResult'))

const languageOptions = computed(() => [
  { value: 'eng', label: t('tools.ocr.languageOptions.eng'), code: 'EN' },
  { value: 'chi_sim', label: t('tools.ocr.languageOptions.chi_sim'), code: 'ZH-CN' },
  { value: 'chi_tra', label: t('tools.ocr.languageOptions.chi_tra'), code: 'ZH-TW' },
  { value: 'jpn', label: t('tools.ocr.languageOptions.jpn'), code: 'JP' },
  { value: 'kor', label: t('tools.ocr.languageOptions.kor'), code: 'KR' },
  { value: 'fra', label: t('tools.ocr.languageOptions.fra'), code: 'FR' },
  { value: 'deu', label: t('tools.ocr.languageOptions.deu'), code: 'DE' },
  { value: 'spa', label: t('tools.ocr.languageOptions.spa'), code: 'ES' },
])

const primaryActionLabel = computed(() => {
  if (!userStore.isAuthenticated) {
    return t('tools.ocr.signInToUse')
  }

  if (!userStore.canUseCloudFeatures) {
    return t('tools.ocr.upgradeToUse')
  }

  return isProcessing.value ? t('tools.ocr.running') : t('tools.ocr.start')
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

watch(copy, (value) => {
  if (!selectedFile.value && !extractedText.value) {
    selectedLanguage.value = String(value.defaultLanguage || 'eng')
  }
})

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
  processingStatus.value = t('tools.ocr.uploading')
  errorState.value = null
  copyMessage.value = ''

  try {
    const uploaded = await fileAPI.uploadFile(selectedFile.value)
    processingProgress.value = 25
    processingStatus.value = t('tools.ocr.submitting')

    const job = await fileAPI.extractTextOCR(uploaded.file_id, selectedLanguage.value)
    processingProgress.value = 38
    processingStatus.value = t('tools.ocr.recognizing')

    const finalStatus = await fileAPI.pollJobUntilDone(job.job_id, (status) => {
      if (typeof status.progress === 'number') {
        processingProgress.value = Math.max(38, Math.min(92, status.progress))
      }

      processingStatus.value = status.status === 'pending'
        ? t('tools.ocr.waiting')
        : t('tools.ocr.recognizing')
    })

    if (finalStatus.status === 'failed') {
      throw new Error(finalStatus.error || 'OCR failed')
    }

    processingProgress.value = 96
    processingStatus.value = t('tools.ocr.preparingResults')

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
    processingStatus.value = t('tools.ocr.completed')
    showResultModal.value = true
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'OCR',
      fallbackMessage: t('tools.ocr.failed'),
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
    copyMessage.value = t('tools.ocr.copied')
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'OCR',
      fallbackMessage: t('tools.ocr.copyFailed'),
    })
  }
}

const closeResultModal = () => {
  showResultModal.value = false
}
</script>

<template>
  <ToolPageShell
      :title="t('tools.ocr.title')"
      :subtitle="t('tools.ocr.subtitle')"
      :badge="t('tools.ocr.badge')"
      pro
      accent="purple"
    width="md"
  >

      <template #badgeIcon>
        <Sparkles class="h-4 w-4" />
      </template>

      <template #headerExtra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          {{ t('tools.ocr.pageExtra') }}
        </p>
      </template>
      <ToolNoticeBar variant="amber">
        <template #icon>
          <Crown class="h-5 w-5" />
        </template>
        {{ t('tools.ocr.notice') }}
      </ToolNoticeBar>

      <DiagnosticAlert
        v-if="errorState"
        class="mt-6"
        :title="errorState.title"
        :message="errorState.message"
        :diagnostic-code="errorState.diagnosticCode"
        :support-hint="errorState.supportHint"
      />

      <ToolAccessPanel
        v-if="!canUseOCR"
        class="mt-6"
        accent="purple"
        :label="t('tools.ocr.accessLabel')"
        :title="userStore.isAuthenticated ? t('tools.ocr.accessMemberTitle') : t('tools.ocr.accessGuestTitle')"
        :description="userStore.isAuthenticated ? t('tools.ocr.accessMemberDescription') : t('tools.ocr.accessGuestDescription')"
        :action-label="userStore.isAuthenticated ? t('tools.ocr.goToUpgrade') : t('tools.ocr.goToSignIn')"
        :steps="[
          t('tools.ocr.accessStep1'),
          t('tools.ocr.accessStep2'),
          t('tools.ocr.accessStep3'),
        ]"
        @action="ensureAccess()"
      >
        <template #actionIcon>
          <Crown class="mr-2 h-4 w-4" />
        </template>
      </ToolAccessPanel>

      <ToolWorkspace
        v-if="canUseOCR"
        class="mt-6"
        layout="wide-secondary"
      >
        <template
          v-if="!selectedFile"
          #upload
        >
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                {{ t('tools.ocr.uploadLabel') }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.ocr.uploadTitleIdle') }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t('tools.ocr.uploadDescriptionIdle') }}
              </p>
            </div>

            <DragDropZone
              class="mt-6"
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
                {{ t('tools.ocr.dropTitle') }}
              </template>
              <template #subtitle>
                {{ t('tools.ocr.dropSubtitle') }}
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
                @remove="clearAll"
              />

              <div
                v-if="extractedText"
                class="rounded-md border border-emerald-200 bg-emerald-50/80 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20"
              >
                <p class="text-sm font-semibold text-emerald-800 dark:text-emerald-100">
                  {{ t('tools.ocr.resultTitle') }}
                </p>
                <p class="mt-2 max-h-20 overflow-hidden text-sm leading-6 text-emerald-700 dark:text-emerald-200">
                  {{ resultPreview }}
                </p>
                <div class="mt-4 flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" @click="showResultModal = true">
                    {{ viewResultLabel }}
                  </Button>
                  <Button variant="outline" size="sm" @click="copyToClipboard">
                    <Copy class="mr-2 h-4 w-4" />
                    {{ t('tools.ocr.copy') }}
                  </Button>
                  <Button variant="outline" size="sm" @click="downloadText">
                    <Download class="mr-2 h-4 w-4" />
                    {{ t('tools.ocr.download') }}
                  </Button>
                </div>
              </div>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <ToolActionPanel
            :label="t('tools.ocr.flowStep2')"
            :title="extractedText ? t('tools.ocr.resultTitle') : t('tools.ocr.start')"
            :description="extractedText ? resultPreview : t('tools.ocr.workspaceDescription')"
            accent="purple"
            :show-progress="isProcessing"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="primaryActionLabel"
            :loading="isProcessing"
            @action="performOCR"
          >
            <template #details>
              <div class="rounded-md border border-purple-100 bg-purple-50/70 p-4 text-sm leading-6 text-purple-900 dark:border-purple-900/40 dark:bg-purple-950/20 dark:text-purple-100">
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <span class="font-semibold">{{ t('tools.ocr.workspaceLanguage') }}</span>
                  <span class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-purple-700 shadow-sm dark:bg-slate-900 dark:text-purple-200">
                    {{ selectedLanguageLabel }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-purple-700/80 dark:text-purple-200/80">
                  {{ t('tools.ocr.flowStep2') }}
                </p>
              </div>
            </template>
          </ToolActionPanel>

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
          <div class="space-y-6">
            <div class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.ocr.workspaceTitle') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('tools.ocr.workspaceDescription') }}
                </p>
              </div>

              <div class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <div class="flex items-center gap-2">
                  <Languages class="h-5 w-5 text-purple-500" />
                  <label class="text-sm font-semibold text-slate-900 dark:text-white">
                    {{ t('tools.ocr.workspaceLanguage') }}
                  </label>
                </div>

                <div class="mt-4 grid gap-3 sm:grid-cols-2">
                  <button
                    v-for="lang in languageOptions"
                    :key="lang.value"
                    :class="[
                      'rounded-md border px-4 py-4 text-left transition-all',
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

              <div class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.ocr.flowTitle') }}
                </p>
                <div class="mt-4 space-y-3">
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-purple-500 text-sm font-semibold text-white">1</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.ocr.flowStep1') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-fuchsia-500 text-sm font-semibold text-white">2</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.ocr.flowStep2') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-semibold text-white">3</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.ocr.flowStep3') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </section>
        </template>
      </ToolWorkspace>

      <Modal
        v-model="showResultModal"
        :title="t('tools.ocr.resultTitle')"
        size="lg"
      >
        <div class="space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3 rounded-md bg-slate-50 px-4 py-4 dark:bg-slate-800">
            <div class="text-sm text-slate-600 dark:text-slate-300">
              <span v-if="ocrResult?.page_count">{{ t('tools.ocr.pages') }}: {{ ocrResult.page_count }}</span>
              <span
                v-if="ocrResult?.average_confidence"
                class="ml-4"
              >
                {{ t('tools.ocr.confidence') }}: {{ ocrResult.average_confidence }}%
              </span>
            </div>

            <div class="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                @click="copyToClipboard"
              >
                <Copy class="mr-2 h-4 w-4" />
                {{ t('tools.ocr.copy') }}
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="downloadText"
              >
                <Download class="mr-2 h-4 w-4" />
                {{ t('tools.ocr.download') }}
              </Button>
            </div>
          </div>

          <div
            v-if="copyMessage"
            class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-200"
          >
            {{ copyMessage }}
          </div>

          <div class="max-h-96 overflow-y-auto rounded-md border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <pre class="whitespace-pre-wrap text-sm leading-6 text-slate-800 dark:text-slate-200">{{ extractedText }}</pre>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Button
              variant="outline"
              size="md"
              @click="closeResultModal"
            >
              {{ t('common.close') }}
            </Button>
            <Button
              size="md"
              @click="clearAll(); closeResultModal()"
            >
              {{ t('tools.ocr.recognizeAnother') }}
            </Button>
          </div>
        </div>
      </Modal>
  </ToolPageShell>
</template>
