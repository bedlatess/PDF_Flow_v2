<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight,
  CheckCircle2,
  Download,
  FileText,
  LogIn,
  Sparkles,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import { fileAPI } from '@/services/api'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

const { t, tm } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const acceptedFileTypes = '.docx,.doc,.xlsx,.xls,.pptx,.ppt'
const uploadedFile = ref<File | null>(null)
const converting = ref(false)
const progress = ref(0)
const status = ref('')
const errorState = ref<FormattedUserError | null>(null)
const resultUrl = ref('')

type ToolPageCopy = Record<string, any>

const copy = computed<ToolPageCopy>(() => tm('tools.officeToPdf') as ToolPageCopy)

const supportedFormats = computed(() => [
  { label: copy.value.formats.word, ext: '.doc, .docx', tone: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-200' },
  { label: copy.value.formats.excel, ext: '.xls, .xlsx', tone: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200' },
  { label: copy.value.formats.powerpoint, ext: '.ppt, .pptx', tone: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-200' },
])

const isReadyToConvert = computed(() => !!uploadedFile.value && userStore.isAuthenticated)

const revokeResultUrl = () => {
  if (resultUrl.value) {
    URL.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const ensureLogin = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
})

const handleFilesSelected = (files: File[]) => {
  if (files.length === 0) {
    return
  }

  const [file] = files
  const extension = file.name.split('.').pop()?.toLowerCase()
  const allowedExtensions = ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt']

  if (!extension || !allowedExtensions.includes(extension)) {
    errorState.value = formatUserFacingError(new Error('unsupported file type'), {
      area: 'OFFICE',
      fallbackMessage: copy.value.unsupported,
    })
    return
  }

  uploadedFile.value = file
  errorState.value = null
  revokeResultUrl()
  progress.value = 0
  status.value = ''
}

const removeFile = () => {
  uploadedFile.value = null
  errorState.value = null
  progress.value = 0
  status.value = ''
  revokeResultUrl()
}

const convertFile = async () => {
  if (!uploadedFile.value) {
    return
  }

  if (!ensureLogin()) {
    return
  }

  converting.value = true
  errorState.value = null
  revokeResultUrl()
  progress.value = 15
  status.value = t('tools.officeToPdf.uploading')

  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)

    const response = await fileAPI.officeToPDF(formData)
    progress.value = 45
    status.value = t('tools.officeToPdf.queued')

    const finalStatus = await fileAPI.pollJobUntilDone(response.job_id, (jobStatus) => {
      if (jobStatus.status === 'processing') {
        status.value = t('tools.officeToPdf.serverProcessing')
      } else if (jobStatus.status === 'pending') {
        status.value = t('tools.officeToPdf.queued')
      }

      if (typeof jobStatus.progress === 'number') {
        progress.value = Math.max(45, Math.min(92, jobStatus.progress))
      }
    })

    if (finalStatus.status === 'failed') {
      throw new Error(finalStatus.error || copy.value.conversionFailedShort)
    }

    status.value = t('tools.officeToPdf.preparingDownload')
    progress.value = 96

    const blob = await fileAPI.downloadResult(response.job_id)
    resultUrl.value = URL.createObjectURL(blob)
    progress.value = 100
    status.value = t('tools.officeToPdf.resultReady')
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'OFFICE',
      fallbackMessage: copy.value.conversionFailed,
    })
  } finally {
    converting.value = false
  }
}

const downloadResult = () => {
  if (!resultUrl.value || !uploadedFile.value) {
    return
  }

  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = uploadedFile.value.name.replace(/\.(docx|doc|xlsx|xls|pptx|ppt)$/i, '.pdf')
  link.click()
}

onUnmounted(() => {
  revokeResultUrl()
})
</script>

<template>
  <ToolPageShell
      :title="t('tools.officeToPdf.title')"
      :subtitle="t('tools.officeToPdf.desc')"
      :badge="t('tools.officeToPdf.badge')"
      accent="blue"
    width="md"
  >

      <template #badgeIcon>
        <Sparkles class="h-4 w-4" />
      </template>

      <template #headerExtra>
        <div class="flex flex-wrap items-center justify-center gap-2">
          <span
            v-for="format in supportedFormats"
            :key="format.label"
            :class="['rounded-full px-3 py-1 text-xs font-semibold', format.tone]"
          >
            {{ format.label }} {{ format.ext }}
          </span>
        </div>
      </template>
      <ToolNoticeBar variant="blue">
        <template #icon>
          <FileText class="h-5 w-5" />
        </template>
        {{ t('tools.officeToPdf.pageNotice') }}
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
        v-if="!userStore.isAuthenticated"
        class="mt-6"
        accent="blue"
        :label="t('tools.officeToPdf.accessLabel')"
        :title="t('tools.officeToPdf.accessGuestTitle')"
        :description="t('tools.officeToPdf.accessGuestDescription')"
        :action-label="t('tools.officeToPdf.goToSignIn')"
        :steps="[
          t('tools.officeToPdf.accessStep1'),
          t('tools.officeToPdf.accessStep2'),
          t('tools.officeToPdf.accessStep3'),
        ]"
        @action="ensureLogin()"
      >
        <template #actionIcon>
          <LogIn class="mr-2 h-4 w-4" />
        </template>
      </ToolAccessPanel>

      <div v-if="userStore.isAuthenticated" class="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-blue-500">
                {{ t('tools.officeToPdf.uploadLabel') }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ uploadedFile ? t('tools.officeToPdf.uploadTitleSelected') : t('tools.officeToPdf.uploadTitleIdle') }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ uploadedFile ? t('tools.officeToPdf.uploadDescriptionSelected') : t('tools.officeToPdf.uploadDescriptionIdle') }}
              </p>
            </div>

            <DragDropZone
              v-if="!uploadedFile"
              :accept="acceptedFileTypes"
              :multiple="false"
              :max-files="1"
              @files-selected="handleFilesSelected"
            >
              <template #icon>
                <FileText class="h-12 w-12" />
              </template>
              <template #title>
                {{ t('tools.officeToPdf.dropFile') }}
              </template>
              <template #subtitle>
                {{ t('tools.officeToPdf.dropSubtitle') }}
              </template>
            </DragDropZone>

            <div v-else class="space-y-5">
              <FilePreview
                :file="uploadedFile"
                @remove="removeFile"
              />

              <ProgressBar
                v-if="converting || resultUrl"
                :progress="progress"
                :label="status"
                variant="primary"
                size="md"
              />

              <div class="flex flex-col gap-3 sm:flex-row">
                <Button
                  variant="primary"
                  size="lg"
                  :loading="converting"
                  :disabled="!isReadyToConvert"
                  full-width
                  @click="convertFile"
                >
                  <ArrowRight class="mr-2 h-4 w-4" />
                  {{ converting ? t('tools.officeToPdf.converting') : t('tools.officeToPdf.convert') }}
                </Button>

                <Button
                  v-if="resultUrl"
                  variant="outline"
                  size="lg"
                  full-width
                  @click="downloadResult"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ t('common.download') }}
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <div class="space-y-6">
          <Card
            v-if="uploadedFile"
            class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
          >
            <div class="space-y-6">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.officeToPdf.workspaceTitle') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('tools.officeToPdf.workspaceDescription') }}
                </p>
              </div>

              <div class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.officeToPdf.howItWorks') }}
                </p>
                <div class="mt-4 space-y-3">
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-sm font-semibold text-white">1</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.officeToPdf.step1') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500 text-sm font-semibold text-white">2</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.officeToPdf.step2') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-semibold text-white">3</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.officeToPdf.step3') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card
            v-if="resultUrl"
            class="rounded-lg border border-emerald-200 bg-emerald-50/90 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
          >
            <div class="flex items-start gap-4">
              <CheckCircle2 class="mt-0.5 h-6 w-6 flex-shrink-0 text-emerald-500" />
              <div class="space-y-3">
                <div>
                  <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                    {{ t('tools.officeToPdf.success') }}
                  </h3>
                  <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ t('tools.officeToPdf.downloadReady') }}
                  </p>
                </div>

                <Button
                  variant="primary"
                  @click="downloadResult"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ t('common.download') }}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
  </ToolPageShell>
</template>
