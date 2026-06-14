<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  Download,
  LogIn,
  RefreshCw,
  ShieldAlert,
  Wrench,
} from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import { useToolFileSelection } from '@/composables/useToolFileSelection'
import { useToolProcessingState } from '@/composables/useToolProcessingState'
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

const {
  selectedItems: selectedFiles,
  fileError,
  setItems: setSelectedFiles,
  clearSelection,
  setFileError,
  clearFileError,
} = useToolFileSelection<File>()
const resultUrl = ref('')
const resultSize = ref(0)
const errorState = ref<FormattedUserError | null>(null)

const {
  isProcessing,
  processingProgress,
  processingStatus,
  processingError,
  startProcessing,
  updateProcessing,
  resetProcessing,
  failProcessing,
} = useToolProcessingState()

const copy = computed<ToolPageCopy>(() => tm('tools.repair.page') as ToolPageCopy)
const selectedFile = computed(() => selectedFiles.value[0] || null)
const workspaceError = computed(() => fileError.value || processingError.value)
const resultStats = computed(() => [
  { label: copy.value.resultSize, value: formatFileSize(resultSize.value) },
])

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
  setSelectedFiles([file])
  resultSize.value = 0
  errorState.value = null
  clearFileError()
  resetProcessing()
  revokeResultUrl()
}

const handleError = (message: string) => {
  setFileError(message)
}

const removeFile = () => {
  clearSelection()
  resultSize.value = 0
  resetProcessing()
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

  startProcessing(copy.value.uploading)
  updateProcessing(15, copy.value.uploading)
  errorState.value = null
  revokeResultUrl()

  try {
    updateProcessing(55, copy.value.processing)
    const blob = await advancedAPI.repairPDF(selectedFile.value)
    resultUrl.value = URL.createObjectURL(blob)
    resultSize.value = blob.size
    updateProcessing(100, copy.value.ready)

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
    failProcessing('')
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

      <ToolWorkspace
        v-else
        class="mt-6"
        :error-message="workspaceError"
        layout="wide-secondary"
      >
        <template
          v-if="!selectedFile"
          #upload
        >
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
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
                accept="pdf"
                :multiple="false"
                :max-files="1"
                @files-selected="handleFilesSelected"
                @error="handleError"
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
            </div>
          </section>
        </template>

        <template
          v-if="selectedFile"
          #primary
        >
          <FilePreview
            :file="selectedFile"
            @remove="removeFile"
          />

          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
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
          </section>
        </template>

        <template
          v-if="selectedFile"
          #secondary
        >
          <ToolActionPanel
            :label="copy.workspaceTitle"
            :title="resultUrl ? copy.successTitle : copy.repair"
            :description="resultUrl ? copy.successMessage : copy.uploadDescriptionSelected"
            accent="blue"
            :stats="resultStats"
            :show-progress="isProcessing || !!resultUrl"
            :progress="processingProgress"
            :progress-label="processingStatus"
            :action-label="isProcessing ? copy.processing : copy.repair"
            :loading="isProcessing"
            :disabled="!canSubmit"
            @action="repairPDF"
          >
            <template #details>
              <div class="rounded-md border border-cyan-100 bg-cyan-50/80 p-4 text-sm leading-6 text-cyan-900 dark:border-cyan-900/50 dark:bg-cyan-950/20 dark:text-cyan-200">
                <RefreshCw class="mb-3 h-5 w-5" />
                <p>{{ copy.step1 }}</p>
                <p>{{ copy.step2 }}</p>
                <p>{{ copy.step3 }}</p>
              </div>
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
            </template>
          </ToolActionPanel>
        </template>
      </ToolWorkspace>
  </ToolPageShell>
</template>
