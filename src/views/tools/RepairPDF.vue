<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  CheckCircle2,
  Download,
  LogIn,
  RefreshCw,
  ShieldAlert,
  Wrench,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { advancedAPI } from '@/services/api'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'
import { historyManager } from '@/utils/history-manager'

const { tm } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

type ToolPageCopy = Record<string, any>

const selectedFile = ref<File | null>(null)
const isProcessing = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const resultSize = ref(0)
const errorState = ref<FormattedUserError | null>(null)

const copy = computed<ToolPageCopy>(() => tm('tools.repair.page') as ToolPageCopy)

const canSubmit = computed(() => !!selectedFile.value && !isProcessing.value)

const ensureLogin = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
})

const revokeResultUrl = () => {
  if (resultUrl.value) {
    URL.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const handleFilesSelected = (files: File[]) => {
  const file = files[0]
  if (!file) return
  selectedFile.value = file
  resultSize.value = 0
  errorState.value = null
  revokeResultUrl()
}

const removeFile = () => {
  selectedFile.value = null
  resultSize.value = 0
  progress.value = 0
  status.value = ''
  errorState.value = null
  revokeResultUrl()
}

const validate = () => {
  if (!selectedFile.value) {
    errorState.value = formatUserFacingError(new Error(copy.value.noFile), {
      area: 'REPAIR',
      fallbackMessage: copy.value.noFile,
    })
    return false
  }
  return true
}

const repairPDF = async () => {
  if (!ensureLogin() || !validate() || !selectedFile.value) {
    return
  }

  isProcessing.value = true
  progress.value = 15
  status.value = copy.value.uploading
  errorState.value = null
  revokeResultUrl()

  try {
    progress.value = 55
    status.value = copy.value.processing
    const blob = await advancedAPI.repairPDF(selectedFile.value)
    resultUrl.value = URL.createObjectURL(blob)
    resultSize.value = blob.size
    progress.value = 100
    status.value = copy.value.ready

    historyManager.addHistory({
      type: 'repair',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'REPAIR',
      fallbackMessage: copy.value.errorFailed,
    })
  } finally {
    isProcessing.value = false
  }
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`
}

const downloadResult = () => {
  if (!resultUrl.value || !selectedFile.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = selectedFile.value.name.replace(/\.pdf$/i, '') + '-repaired.pdf'
  link.click()
}

onUnmounted(revokeResultUrl)
</script>

<template>
  <ToolPageShell
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="blue"
    width="md"
  >

      <template #badgeIcon>
        <Wrench class="h-4 w-4" />
      </template>
      <ToolNoticeBar variant="blue">
        <template #icon>
          <ShieldAlert class="h-5 w-5" />
        </template>
        {{ copy.notice }}
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
        :label="copy.accessLabel"
        :title="copy.accessTitle"
        :description="copy.accessDescription"
        :action-label="copy.goToSignIn"
        :steps="copy.accessSteps"
        @action="ensureLogin"
      >
        <template #actionIcon>
          <LogIn class="mr-2 h-4 w-4" />
        </template>
      </ToolAccessPanel>

      <div
        v-else
        class="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]"
      >
        <div class="space-y-6">
          <Card class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700 dark:text-cyan-300">
                {{ copy.uploadLabel }}
              </p>
              <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                {{ selectedFile ? copy.uploadTitleSelected : copy.uploadTitleIdle }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ selectedFile ? copy.uploadDescriptionSelected : copy.uploadDescriptionIdle }}
              </p>
            </div>

            <div class="mt-6">
              <DragDropZone
                v-if="!selectedFile"
                accept="pdf"
                :multiple="false"
                :max-files="1"
                @files-selected="handleFilesSelected"
              >
                <template #icon>
                  <Wrench class="h-12 w-12" />
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

          <Card
            v-if="selectedFile || isProcessing || resultUrl"
            class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
          >
            <div class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ copy.workspaceTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.workspaceDescription }}
                </p>
              </div>
              <div class="grid gap-3">
                <div
                  v-for="(step, index) in [copy.step1, copy.step2, copy.step3]"
                  :key="step"
                  class="flex items-start gap-3 rounded-md border border-cyan-100 bg-cyan-50/70 p-4 dark:border-cyan-900/40 dark:bg-cyan-950/20"
                >
                  <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-600 text-sm font-bold text-white">
                    {{ index + 1 }}
                  </span>
                  <span class="text-sm leading-6 text-slate-700 dark:text-slate-200">
                    {{ step }}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div class="space-y-6">
          <Card class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-5">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                    {{ resultUrl ? copy.successTitle : copy.repair }}
                  </h2>
                  <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ resultUrl ? copy.successMessage : copy.uploadDescriptionSelected }}
                  </p>
                </div>
                <Button
                  v-if="resultUrl"
                  variant="primary"
                  size="sm"
                  @click="downloadResult"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ copy.download }}
                </Button>
              </div>

              <div class="rounded-md border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {{ copy.resultSize }}
                </p>
                <p class="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                  {{ formatFileSize(resultSize) }}
                </p>
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
                  :disabled="!canSubmit"
                  full-width
                  @click="repairPDF"
                >
                  <RefreshCw class="mr-2 h-4 w-4" />
                  {{ isProcessing ? copy.processing : copy.repair }}
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

          <Card
            v-if="resultUrl"
            class="rounded-lg border border-emerald-200 bg-emerald-50/90 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
          >
            <div class="flex items-start gap-4">
              <CheckCircle2 class="mt-0.5 h-6 w-6 shrink-0 text-emerald-500" />
              <div>
                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                  {{ copy.successTitle }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ copy.successMessage }}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
  </ToolPageShell>
</template>
