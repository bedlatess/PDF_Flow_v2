<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDownToLine, Boxes, FileText, LogIn, RefreshCw } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import { fileAPI, type JobStatusResponse } from '@/services/api'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

type BatchMode = 'pdf_to_word' | 'pdf_to_excel'
type BatchState = 'queued' | 'uploading' | 'processing' | 'completed' | 'failed'
type ToolPageCopy = Record<string, any>

interface BatchItem {
  id: string
  file: File
  state: BatchState
  progress: number
  jobId?: string
  resultUrl?: string
  error?: string
}

const { t, tm } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const mode = ref<BatchMode>('pdf_to_word')
const items = ref<BatchItem[]>([])
const running = ref(false)
const activeMessage = ref('')
const errorState = ref<FormattedUserError | null>(null)

const copy = computed<ToolPageCopy>(() => tm('tools.batchConvert') as ToolPageCopy)
const canStart = computed(() => userStore.isAuthenticated && items.value.length > 0 && !running.value)
const completedCount = computed(() => items.value.filter((item) => item.state === 'completed').length)
const failedCount = computed(() => items.value.filter((item) => item.state === 'failed').length)
const overallProgress = computed(() => {
  if (items.value.length === 0) return 0
  const total = items.value.reduce((sum, item) => sum + item.progress, 0)
  return Math.round(total / items.value.length)
})

const ensureLogin = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
})

const handleFilesSelected = (files: File[]) => {
  const pdfFiles = files.filter((file) => file.name.toLowerCase().endsWith('.pdf'))
  if (pdfFiles.length !== files.length) {
    errorState.value = formatUserFacingError(new Error('PDF required'), {
      area: 'GENERAL',
      fallbackTitle: copy.value.errorTitle,
      fallbackMessage: copy.value.errorPdfOnly,
    })
  } else {
    errorState.value = null
  }

  const existingKeys = new Set(items.value.map((item) => `${item.file.name}:${item.file.size}`))
  for (const file of pdfFiles) {
    const key = `${file.name}:${file.size}`
    if (existingKeys.has(key)) continue
    items.value.push({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      file,
      state: 'queued',
      progress: 0,
    })
    existingKeys.add(key)
  }
}

const removeItem = (id: string) => {
  const item = items.value.find((entry) => entry.id === id)
  if (item?.resultUrl) URL.revokeObjectURL(item.resultUrl)
  items.value = items.value.filter((entry) => entry.id !== id)
}

const clearAll = () => {
  for (const item of items.value) {
    if (item.resultUrl) URL.revokeObjectURL(item.resultUrl)
  }
  items.value = []
  errorState.value = null
  activeMessage.value = ''
}

onUnmounted(clearAll)

const resetItemForRun = (item: BatchItem) => {
  if (item.resultUrl) URL.revokeObjectURL(item.resultUrl)
  item.resultUrl = undefined
  item.error = undefined
  item.jobId = undefined
  item.state = 'queued'
  item.progress = 0
}

const startBatch = async () => {
  if (!ensureLogin() || !canStart.value) return
  running.value = true
  errorState.value = null
  activeMessage.value = copy.value.statusStarting

  try {
    for (const item of items.value) {
      resetItemForRun(item)
      item.state = 'uploading'
      item.progress = 12
      activeMessage.value = t('tools.batchConvert.statusUploadingFile', { file: item.file.name })

      try {
        const upload = await fileAPI.uploadFile(item.file)
        item.progress = 28
        item.state = 'processing'
        const response = mode.value === 'pdf_to_word'
          ? await fileAPI.pdfToWord(upload.file_id)
          : await fileAPI.pdfToExcel(upload.file_id)
        item.jobId = response.job_id
        item.progress = 42

        const finalStatus = await fileAPI.pollJobUntilDone(response.job_id, (jobStatus: JobStatusResponse) => {
          if (typeof jobStatus.progress === 'number') {
            item.progress = Math.max(42, Math.min(92, jobStatus.progress))
          }
        })

        if (finalStatus.status === 'failed') {
          throw new Error(finalStatus.error || copy.value.errorItemFailed)
        }

        const blob = await fileAPI.downloadResult(response.job_id)
        item.resultUrl = URL.createObjectURL(blob)
        item.state = 'completed'
        item.progress = 100
      } catch (error) {
        const formatted = formatUserFacingError(error, {
          area: 'GENERAL',
          fallbackTitle: copy.value.errorTitle,
          fallbackMessage: copy.value.errorItemFailed,
        })
        item.state = 'failed'
        item.progress = 100
        item.error = formatted.message
      }
    }
    activeMessage.value = copy.value.statusDone
  } finally {
    running.value = false
  }
}

const downloadItem = (item: BatchItem) => {
  if (!item.resultUrl) return
  const extension = mode.value === 'pdf_to_word' ? '.docx' : '.xlsx'
  const link = document.createElement('a')
  link.href = item.resultUrl
  link.download = item.file.name.replace(/\.pdf$/i, extension)
  link.click()
}

const modeOptions = computed(() => [
  {
    value: 'pdf_to_word',
    label: copy.value.modeWord,
    description: copy.value.modeWordDescription,
  },
  {
    value: 'pdf_to_excel',
    label: copy.value.modeExcel,
    description: copy.value.modeExcelDescription,
  },
])
</script>

<template>
  <ToolPageShell
    :title="t('tools.batchConvert.title')"
    :subtitle="t('tools.batchConvert.desc')"
    :badge="t('tools.batchConvert.badge')"
    accent="slate"
    width="lg"
  >
    <template #badgeIcon>
      <Boxes class="h-4 w-4" />
    </template>

    <ToolNoticeBar variant="blue">
      <template #icon>
        <Boxes class="h-5 w-5" />
      </template>
      {{ t('tools.batchConvert.notice') }}
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
      :label="t('tools.batchConvert.accessLabel')"
      :title="t('tools.batchConvert.accessGuestTitle')"
      :description="t('tools.batchConvert.accessGuestDescription')"
      :action-label="t('tools.batchConvert.goToSignIn')"
      :steps="[
        t('tools.batchConvert.accessStep1'),
        t('tools.batchConvert.accessStep2'),
        t('tools.batchConvert.accessStep3'),
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
      layout="wide-primary"
    >
      <template #primary>
        <section class="pf-panel p-4 sm:p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="pf-eyebrow text-slate-500 dark:text-slate-400">{{ t('tools.batchConvert.uploadLabel') }}</p>
              <h2 class="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                {{ t('tools.batchConvert.uploadTitle') }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t('tools.batchConvert.uploadDescription') }}
              </p>
            </div>
            <Button
              v-if="items.length"
              variant="outline"
              size="sm"
              :disabled="running"
              @click="clearAll"
            >
              {{ t('tools.batchConvert.clearAll') }}
            </Button>
          </div>

          <DragDropZone
            class="mt-6"
            accept="pdf"
            :multiple="true"
            :max-files="10"
            @files-selected="handleFilesSelected"
          >
            <template #icon>
              <FileText class="h-12 w-12" />
            </template>
            <template #title>
              {{ t('tools.batchConvert.dropTitle') }}
            </template>
            <template #subtitle>
              {{ t('tools.batchConvert.dropSubtitle') }}
            </template>
          </DragDropZone>
        </section>

        <section
          v-if="items.length"
          class="pf-panel overflow-hidden"
        >
          <div class="border-b border-slate-200 px-4 py-3 dark:border-slate-800 sm:px-5">
            <p class="text-sm font-semibold text-slate-950 dark:text-white">
              {{ t('tools.batchConvert.queueTitle', { count: items.length }) }}
            </p>
          </div>
          <div class="divide-y divide-slate-100 dark:divide-slate-800">
            <div
              v-for="item in items"
              :key="item.id"
              class="grid gap-3 px-4 py-4 sm:grid-cols-[1fr_auto] sm:items-center sm:px-5"
            >
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold text-slate-950 dark:text-white">{{ item.file.name }}</p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {{ t(`tools.batchConvert.states.${item.state}`) }}
                  <span v-if="item.jobId"> · {{ item.jobId }}</span>
                </p>
                <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <div class="h-full rounded-full bg-sky-500" :style="{ width: `${item.progress}%` }" />
                </div>
                <p v-if="item.error" class="mt-2 text-xs leading-5 text-rose-600 dark:text-rose-300">{{ item.error }}</p>
              </div>
              <div class="flex flex-wrap gap-2 sm:justify-end">
                <Button
                  v-if="item.resultUrl"
                  size="sm"
                  @click="downloadItem(item)"
                >
                  <ArrowDownToLine class="mr-2 h-4 w-4" />
                  {{ t('common.download') }}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  :disabled="running"
                  @click="removeItem(item.id)"
                >
                  {{ t('common.remove', 'Remove') }}
                </Button>
              </div>
            </div>
          </div>
        </section>
      </template>

      <template #secondary>
        <ToolActionPanel
          :label="t('tools.batchConvert.actionLabel')"
          :title="t('tools.batchConvert.actionTitle')"
          :description="t('tools.batchConvert.actionDescription')"
          accent="slate"
          :show-progress="running || completedCount > 0 || failedCount > 0"
          :progress="overallProgress"
          :progress-label="activeMessage"
          :action-label="running ? t('tools.batchConvert.running') : t('tools.batchConvert.start')"
          :loading="running"
          :disabled="!canStart"
          @action="startBatch"
        >
          <div class="space-y-3">
            <label
              v-for="option in modeOptions"
              :key="option.value"
              :class="[
                'block cursor-pointer rounded-md border p-4 transition',
                mode === option.value
                  ? 'border-sky-300 bg-sky-50 dark:border-sky-500/40 dark:bg-sky-500/10'
                  : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950',
              ]"
            >
              <input
                v-model="mode"
                class="sr-only"
                type="radio"
                :value="option.value"
                :disabled="running"
              >
              <span class="text-sm font-semibold text-slate-950 dark:text-white">{{ option.label }}</span>
              <span class="mt-1 block text-xs leading-5 text-slate-600 dark:text-slate-300">{{ option.description }}</span>
            </label>
          </div>

          <template #details>
            <div class="grid grid-cols-3 gap-2 text-center text-xs">
              <div class="rounded-md bg-slate-100 p-3 dark:bg-slate-800">
                <p class="font-semibold text-slate-950 dark:text-white">{{ items.length }}</p>
                <p class="mt-1 text-slate-500 dark:text-slate-400">{{ t('tools.batchConvert.stats.total') }}</p>
              </div>
              <div class="rounded-md bg-emerald-50 p-3 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
                <p class="font-semibold">{{ completedCount }}</p>
                <p class="mt-1">{{ t('tools.batchConvert.stats.completed') }}</p>
              </div>
              <div class="rounded-md bg-rose-50 p-3 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">
                <p class="font-semibold">{{ failedCount }}</p>
                <p class="mt-1">{{ t('tools.batchConvert.stats.failed') }}</p>
              </div>
            </div>

            <Button
              v-if="completedCount || failedCount"
              variant="outline"
              size="lg"
              full-width
              :disabled="running"
              @click="startBatch"
            >
              <RefreshCw class="mr-2 h-4 w-4" />
              {{ t('tools.batchConvert.retry') }}
            </Button>
          </template>
        </ToolActionPanel>
      </template>
    </ToolWorkspace>
  </ToolPageShell>
</template>
