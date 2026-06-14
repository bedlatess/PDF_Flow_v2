<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { Download, FileText, Globe2, LogIn, Sparkles } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import { fileAPI, type HTMLToPDFRequest } from '@/services/api'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

type InputMode = 'url' | 'html'
type PageSize = 'A4' | 'Letter' | 'Legal'
type Orientation = 'portrait' | 'landscape'
type Margin = 'none' | 'narrow' | 'normal' | 'wide'
type ToolPageCopy = Record<string, any>

const { t, tm } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const inputMode = ref<InputMode>('url')
const url = ref('')
const html = ref('')
const pageSize = ref<PageSize>('A4')
const orientation = ref<Orientation>('portrait')
const margin = ref<Margin>('normal')
const converting = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const resultFileName = ref('html-to-pdf.pdf')
const errorState = ref<FormattedUserError | null>(null)

const copy = computed<ToolPageCopy>(() => tm('tools.htmlToPdf') as ToolPageCopy)
const htmlByteSize = computed(() => new Blob([html.value]).size)
const htmlSizeLimit = 512 * 1024
const canConvert = computed(() => {
  if (!userStore.isAuthenticated || converting.value) return false
  if (inputMode.value === 'url') return url.value.trim().length > 0
  return html.value.trim().length > 0 && htmlByteSize.value <= htmlSizeLimit
})

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

const resetResultState = () => {
  clearResult()
  progress.value = 0
  status.value = ''
}

const convert = async () => {
  if (!ensureLogin() || !canConvert.value) return

  converting.value = true
  errorState.value = null
  resetResultState()
  progress.value = 15
  status.value = copy.value.statusQueueing

  try {
    const payload: HTMLToPDFRequest = {
      mode: inputMode.value,
      page_size: pageSize.value,
      orientation: orientation.value,
      margin: margin.value,
    }
    if (inputMode.value === 'url') {
      payload.url = url.value.trim()
      resultFileName.value = 'webpage.pdf'
    } else {
      payload.html = html.value
      resultFileName.value = 'html-snippet.pdf'
    }

    const response = await fileAPI.htmlToPDF(payload)
    progress.value = 35
    status.value = copy.value.statusQueued

    const finalStatus = await fileAPI.pollJobUntilDone(response.job_id, (jobStatus) => {
      if (jobStatus.status === 'pending') status.value = copy.value.statusQueued
      if (jobStatus.status === 'processing') status.value = copy.value.statusRendering
      if (typeof jobStatus.progress === 'number') {
        progress.value = Math.max(35, Math.min(92, jobStatus.progress))
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
  if (!resultUrl.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = resultFileName.value
  link.click()
}

const modeButtonClass = (mode: InputMode) => [
  'inline-flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-semibold transition',
  inputMode.value === mode
    ? 'bg-sky-600 text-white shadow-sm'
    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
]

const formatBytes = (value: number) => {
  if (value < 1024) return `${value} B`
  return `${(value / 1024).toFixed(1)} KB`
}

onUnmounted(() => {
  clearResult()
})
</script>

<template>
  <ToolPageShell
    :title="t('tools.htmlToPdf.title')"
    :subtitle="t('tools.htmlToPdf.desc')"
    :badge="t('tools.htmlToPdf.badge')"
    accent="blue"
    width="lg"
  >
    <template #badgeIcon>
      <Sparkles class="h-4 w-4" />
    </template>

    <ToolNoticeBar variant="blue">
      <template #icon>
        <Globe2 class="h-5 w-5" />
      </template>
      {{ t('tools.htmlToPdf.notice') }}
    </ToolNoticeBar>

    <DiagnosticAlert
      v-if="errorState"
      :title="errorState.title"
      :message="errorState.message"
      :diagnostic-code="errorState.diagnosticCode"
      :support-hint="errorState.supportHint"
    />

    <ToolAccessPanel
      v-if="!userStore.isAuthenticated"
      accent="blue"
      :label="t('tools.htmlToPdf.accessLabel')"
      :title="t('tools.htmlToPdf.accessGuestTitle')"
      :description="t('tools.htmlToPdf.accessGuestDescription')"
      :action-label="t('tools.htmlToPdf.goToSignIn')"
      :steps="[
        t('tools.htmlToPdf.accessStep1'),
        t('tools.htmlToPdf.accessStep2'),
        t('tools.htmlToPdf.accessStep3'),
      ]"
      @action="ensureLogin()"
    >
      <template #actionIcon>
        <LogIn class="mr-2 h-4 w-4" />
      </template>
    </ToolAccessPanel>

    <ToolWorkspace
      v-else
      layout="wide-secondary"
    >
      <template #primary>
        <section class="pf-panel p-4 sm:p-5">
          <div class="space-y-5">
            <div>
              <p class="pf-eyebrow text-sky-600 dark:text-sky-300">{{ t('tools.htmlToPdf.inputLabel') }}</p>
              <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                {{ t('tools.htmlToPdf.inputTitle') }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t('tools.htmlToPdf.inputDescription') }}
              </p>
            </div>

            <div class="flex rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-950">
              <button :class="modeButtonClass('url')" type="button" @click="inputMode = 'url'; resetResultState()">
                <Globe2 class="h-4 w-4" />
                {{ t('tools.htmlToPdf.urlMode') }}
              </button>
              <button :class="modeButtonClass('html')" type="button" @click="inputMode = 'html'; resetResultState()">
                <FileText class="h-4 w-4" />
                {{ t('tools.htmlToPdf.htmlMode') }}
              </button>
            </div>

            <label v-if="inputMode === 'url'" class="block">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ t('tools.htmlToPdf.urlLabel') }}</span>
              <input
                v-model="url"
                type="url"
                class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
                placeholder="https://example.com/report"
                @input="resetResultState"
              >
              <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ t('tools.htmlToPdf.urlHint') }}</p>
            </label>

            <label v-else class="block">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ t('tools.htmlToPdf.htmlLabel') }}</span>
              <textarea
                v-model="html"
                rows="13"
                class="mt-2 w-full resize-y rounded-md border border-slate-200 bg-white px-3 py-3 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
                placeholder="<html><body><h1>Invoice</h1></body></html>"
                @input="resetResultState"
              />
              <div class="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span>{{ t('tools.htmlToPdf.htmlHint') }}</span>
                <span :class="{ 'text-rose-600 dark:text-rose-300': htmlByteSize > htmlSizeLimit }">
                  {{ formatBytes(htmlByteSize) }} / {{ formatBytes(htmlSizeLimit) }}
                </span>
              </div>
            </label>
          </div>
        </section>
      </template>

      <template #secondary>
        <ToolActionPanel
          :label="t('tools.htmlToPdf.optionsLabel')"
          :title="resultUrl ? t('tools.htmlToPdf.resultTitle') : t('tools.htmlToPdf.optionsTitle')"
          :description="resultUrl ? t('tools.htmlToPdf.resultDescription') : t('tools.htmlToPdf.optionsDescription')"
          accent="blue"
          :show-progress="converting || !!resultUrl"
          :progress="progress"
          :progress-label="status"
          :action-label="converting ? t('tools.htmlToPdf.converting') : t('tools.htmlToPdf.convert')"
          :loading="converting"
          :disabled="!canConvert"
          @action="convert"
        >
          <div class="grid gap-4">
            <label class="block">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ t('tools.htmlToPdf.pageSize') }}</span>
              <select v-model="pageSize" class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white">
                <option value="A4">A4</option>
                <option value="Letter">Letter</option>
                <option value="Legal">Legal</option>
              </select>
            </label>

            <label class="block">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ t('tools.htmlToPdf.orientation') }}</span>
              <select v-model="orientation" class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white">
                <option value="portrait">{{ t('tools.htmlToPdf.portrait') }}</option>
                <option value="landscape">{{ t('tools.htmlToPdf.landscape') }}</option>
              </select>
            </label>

            <label class="block">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ t('tools.htmlToPdf.margin') }}</span>
              <select v-model="margin" class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white">
                <option value="none">{{ t('tools.htmlToPdf.marginNone') }}</option>
                <option value="narrow">{{ t('tools.htmlToPdf.marginNarrow') }}</option>
                <option value="normal">{{ t('tools.htmlToPdf.marginNormal') }}</option>
                <option value="wide">{{ t('tools.htmlToPdf.marginWide') }}</option>
              </select>
            </label>
          </div>

          <template #details>
            <div class="rounded-md border border-sky-100 bg-sky-50/80 p-4 text-sm leading-6 text-sky-900 dark:border-sky-900/50 dark:bg-sky-950/20 dark:text-sky-200">
              <p>{{ t('tools.htmlToPdf.safety1') }}</p>
              <p>{{ t('tools.htmlToPdf.safety2') }}</p>
              <p>{{ t('tools.htmlToPdf.safety3') }}</p>
            </div>
            <Button
              v-if="resultUrl"
              variant="primary"
              size="lg"
              full-width
              @click="downloadResult"
            >
              <Download class="mr-2 h-4 w-4" />
              {{ t('common.download') }}
            </Button>
          </template>
        </ToolActionPanel>
      </template>
    </ToolWorkspace>
  </ToolPageShell>
</template>
