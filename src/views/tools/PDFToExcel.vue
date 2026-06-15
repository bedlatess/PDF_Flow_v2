<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDownToLine, FileText, LogIn, Sheet, Sparkles } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import { fileAPI } from '@/services/api'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

type ToolPageCopy = Record<string, any>

const { t, tm } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const uploadedFile = ref<File | null>(null)
const converting = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const errorState = ref<FormattedUserError | null>(null)

const copy = computed<ToolPageCopy>(() => tm('tools.pdfToExcel') as ToolPageCopy)
const canConvert = computed(() => !!uploadedFile.value && userStore.isAuthenticated && !converting.value)

const ensureLogin = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
})

const clearResult = () => {
  if (resultUrl.value) {
    URL.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const resetState = () => {
  clearResult()
  progress.value = 0
  status.value = ''
}

const handleFilesSelected = (files: File[]) => {
  const [file] = files
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    errorState.value = formatUserFacingError(new Error('PDF required'), {
      area: 'GENERAL',
      fallbackTitle: copy.value.errorTitle,
      fallbackMessage: copy.value.errorPdfOnly,
    })
    return
  }
  uploadedFile.value = file
  errorState.value = null
  resetState()
}

const removeFile = () => {
  uploadedFile.value = null
  errorState.value = null
  resetState()
}

const convert = async () => {
  if (!uploadedFile.value || !ensureLogin()) return

  converting.value = true
  errorState.value = null
  resetState()
  progress.value = 12
  status.value = copy.value.statusUploading

  try {
    const upload = await fileAPI.uploadFile(uploadedFile.value)
    progress.value = 28
    status.value = copy.value.statusQueueing

    const response = await fileAPI.pdfToExcel(upload.file_id)
    progress.value = 42
    status.value = copy.value.statusQueued

    const finalStatus = await fileAPI.pollJobUntilDone(response.job_id, (jobStatus) => {
      if (jobStatus.status === 'pending') status.value = copy.value.statusQueued
      if (jobStatus.status === 'processing') status.value = copy.value.statusConverting
      if (typeof jobStatus.progress === 'number') {
        progress.value = Math.max(42, Math.min(92, jobStatus.progress))
      }
    })

    if (finalStatus.status === 'failed') {
      throw new Error(finalStatus.error || copy.value.errorFailed)
    }

    progress.value = 96
    status.value = copy.value.statusPreparing
    const blob = await fileAPI.downloadResult(response.job_id)
    resultUrl.value = URL.createObjectURL(blob)
    progress.value = 100
    status.value = copy.value.statusReady
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'GENERAL',
      fallbackTitle: copy.value.errorTitle,
      fallbackMessage: copy.value.errorFailed,
    })
  } finally {
    converting.value = false
  }
}

const downloadResult = () => {
  if (!resultUrl.value || !uploadedFile.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = uploadedFile.value.name.replace(/\.pdf$/i, '.xlsx')
  link.click()
}

onUnmounted(() => {
  clearResult()
})
</script>

<template>
  <ToolPageShell
    :title="t('tools.pdfToExcel.title')"
    :subtitle="t('tools.pdfToExcel.desc')"
    :badge="t('tools.pdfToExcel.badge')"
    accent="emerald"
    width="md"
  >
    <template #badgeIcon>
      <Sparkles class="h-4 w-4" />
    </template>

    <ToolNoticeBar variant="emerald">
      <template #icon>
        <Sheet class="h-5 w-5" />
      </template>
      {{ t('tools.pdfToExcel.notice') }}
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
      :label="t('tools.pdfToExcel.accessLabel')"
      :title="t('tools.pdfToExcel.accessGuestTitle')"
      :description="t('tools.pdfToExcel.accessGuestDescription')"
      :action-label="t('tools.pdfToExcel.goToSignIn')"
      :steps="[
        t('tools.pdfToExcel.accessStep1'),
        t('tools.pdfToExcel.accessStep2'),
        t('tools.pdfToExcel.accessStep3'),
      ]"
      @action="ensureLogin()"
    >
      <template #actionIcon>
        <LogIn class="mr-2 h-4 w-4" />
      </template>
    </ToolAccessPanel>

    <ToolWorkspace
      v-else
      class="mt-6"
      layout="wide-secondary"
    >
      <template #upload>
        <section
          v-if="!uploadedFile"
          class="pf-panel p-4 sm:p-5"
        >
          <div>
            <p class="pf-eyebrow text-emerald-600 dark:text-emerald-300">{{ t('tools.pdfToExcel.uploadLabel') }}</p>
            <h2 class="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
              {{ t('tools.pdfToExcel.uploadTitle') }}
            </h2>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {{ t('tools.pdfToExcel.uploadDescription') }}
            </p>
          </div>

          <DragDropZone
            class="mt-6"
            accept="pdf"
            :multiple="false"
            :max-files="1"
            @files-selected="handleFilesSelected"
          >
            <template #icon>
              <FileText class="h-12 w-12" />
            </template>
            <template #title>
              {{ t('tools.pdfToExcel.dropTitle') }}
            </template>
            <template #subtitle>
              {{ t('tools.pdfToExcel.dropSubtitle') }}
            </template>
          </DragDropZone>
        </section>
      </template>

      <template
        v-if="uploadedFile"
        #primary
      >
        <FilePreview
          :file="uploadedFile"
          @remove="removeFile"
        />

        <section class="pf-panel p-4 sm:p-5">
          <p class="pf-eyebrow text-emerald-600 dark:text-emerald-300">{{ t('tools.pdfToExcel.betaLabel') }}</p>
          <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
            {{ t('tools.pdfToExcel.betaTitle') }}
          </h2>
          <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ t('tools.pdfToExcel.betaDescription') }}
          </p>

          <div class="mt-5 grid gap-3 sm:grid-cols-3">
            <div
              v-for="item in copy.expectations"
              :key="item.title"
              class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50"
            >
              <p class="text-sm font-semibold text-slate-950 dark:text-white">{{ item.title }}</p>
              <p class="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-300">{{ item.body }}</p>
            </div>
          </div>
        </section>
      </template>

      <template
        v-if="uploadedFile"
        #secondary
      >
        <ToolActionPanel
          :label="t('tools.pdfToExcel.actionLabel')"
          :title="resultUrl ? t('tools.pdfToExcel.resultTitle') : t('tools.pdfToExcel.actionTitle')"
          :description="resultUrl ? t('tools.pdfToExcel.resultDescription') : t('tools.pdfToExcel.actionDescription')"
          accent="emerald"
          :show-progress="converting || !!resultUrl"
          :progress="progress"
          :progress-label="status"
          :action-label="converting ? t('tools.pdfToExcel.converting') : t('tools.pdfToExcel.convert')"
          :loading="converting"
          :disabled="!canConvert"
          @action="convert"
        >
          <template #details>
            <div class="rounded-md border border-emerald-100 bg-emerald-50/80 p-4 text-sm leading-6 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-200">
              <p>{{ t('tools.pdfToExcel.limit1') }}</p>
              <p>{{ t('tools.pdfToExcel.limit2') }}</p>
              <p>{{ t('tools.pdfToExcel.limit3') }}</p>
            </div>

            <Button
              v-if="resultUrl"
              variant="primary"
              size="lg"
              full-width
              @click="downloadResult"
            >
              <ArrowDownToLine class="mr-2 h-4 w-4" />
              {{ t('common.download') }}
            </Button>
          </template>
        </ToolActionPanel>
      </template>
    </ToolWorkspace>
  </ToolPageShell>
</template>
