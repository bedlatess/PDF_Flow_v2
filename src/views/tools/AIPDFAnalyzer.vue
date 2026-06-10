<template>
  <div class="min-h-screen bg-gradient-to-br from-fuchsia-50 via-white to-indigo-50 dark:from-slate-950 dark:via-slate-950 dark:to-fuchsia-950/20">
    <ToolHeader
      :title="t('ai.title')"
      :subtitle="t('ai.subtitle')"
      :badge="t('ai.proBadge')"
      accent="pink"
    >
      <template #badgeIcon>
        <Sparkles class="h-4 w-4" />
      </template>

      <template #extra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          Sign in first, then use AI summary, Q&A, and structured extraction from one unified analysis surface.
        </p>
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
      <ToolNoticeBar variant="purple">
        <template #icon>
          <Sparkles class="h-5 w-5" />
        </template>
        AI PDF Analyzer follows the same rule as OCR: guests sign in first, then the app checks whether your account includes Pro AI access.
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
        v-if="!canUseAI"
        class="mt-6"
      >
        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-fuchsia-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div class="space-y-4">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-fuchsia-500">
                Access
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ userStore.isAuthenticated ? 'Upgrade required after login' : 'Sign in before AI analysis' }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ userStore.isAuthenticated
                  ? 'Your account is active, but AI analysis is a Pro capability. Upgrade only when you need AI-assisted document work.'
                  : 'Please sign in first so the app can verify your account and only show upgrade guidance if it is actually needed.' }}
              </p>

              <Button
                size="lg"
                @click="ensureAccess()"
              >
                <LockKeyhole class="mr-2 h-4 w-4" />
                {{ userStore.isAuthenticated ? 'Go to upgrade' : 'Go to sign in' }}
              </Button>
            </div>

            <div class="rounded-[24px] border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
              <div class="space-y-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  1. Sign in first
                </div>
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  2. Upload one PDF for AI analysis
                </div>
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  3. Summarize, ask, or extract using the same file
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-fuchsia-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-fuchsia-500">
                Upload
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ selectedFile ? 'Current analysis file' : 'Upload a PDF for AI analysis' }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ selectedFile ? 'The same file can be reused across summary, Q&A, and structured extraction.' : 'Use one PDF at a time to keep AI context and diagnostics easier to understand.' }}
              </p>
            </div>

            <DragDropZone
              v-if="!selectedFile"
              :accept="'.pdf'"
              @files-selected="handleFileSelected"
              @error="handleUploadError"
            >
              <template #icon>
                <FileText class="h-12 w-12" />
              </template>
              <template #title>
                Drop a PDF for AI analysis
              </template>
              <template #subtitle>
                Sign in first, then summarize, ask questions, or extract structured data.
              </template>
            </DragDropZone>

            <div
              v-else
              class="space-y-4"
            >
              <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <div class="flex items-center justify-between gap-4">
                  <div class="flex items-center gap-3">
                    <FileText class="h-8 w-8 text-fuchsia-500" />
                    <div>
                      <p class="font-semibold text-slate-900 dark:text-white">
                        {{ selectedFile.name }}
                      </p>
                      <p class="text-sm text-slate-500 dark:text-slate-400">
                        {{ formatFileSize(selectedFile.size) }}
                      </p>
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    @click="clearFile"
                  >
                    <X class="mr-2 h-4 w-4" />
                    Replace
                  </Button>
                </div>
              </div>

              <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 text-sm leading-6 text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300">
                <p class="font-semibold text-slate-900 dark:text-white">
                  Suggested flow
                </p>
                <p class="mt-2">
                  Start with summary for a quick overview, use Q&amp;A for targeted checks, then switch to structured extraction when you need machine-readable output.
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-fuchsia-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div class="flex flex-wrap gap-2">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                :class="[
                  'inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all',
                  activeTab === tab.id
                    ? 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-700 dark:border-fuchsia-700 dark:bg-fuchsia-950/30 dark:text-fuchsia-200'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-fuchsia-200 hover:text-fuchsia-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-fuchsia-700/50 dark:hover:text-fuchsia-200',
                ]"
                @click="activeTab = tab.id"
              >
                <component :is="tab.icon" class="h-4 w-4" />
                {{ tab.label }}
              </button>
            </div>

            <div v-if="activeTab === 'summarize'" class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.summarize.title') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('ai.summarize.description') }}
                </p>
              </div>

              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {{ t('ai.summarize.length') }}
                </label>
                <select
                  v-model="summaryLength"
                  class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-fuchsia-400 focus:ring-4 focus:ring-fuchsia-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-fuchsia-400 dark:focus:ring-fuchsia-500/20"
                >
                  <option value="short">
                    {{ t('ai.summarize.short') }}
                  </option>
                  <option value="medium">
                    {{ t('ai.summarize.medium') }}
                  </option>
                  <option value="long">
                    {{ t('ai.summarize.long') }}
                  </option>
                </select>
              </div>

              <Button
                :disabled="processing || !selectedFile"
                full-width
                @click="summarizePDF"
              >
                <Sparkles v-if="!processing" class="mr-2 h-4 w-4" />
                <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
                {{ processing ? t('common.processing') : t('ai.summarize.generate') }}
              </Button>

              <div
                v-if="summaryResult"
                class="space-y-4 rounded-[24px] border border-fuchsia-100 bg-fuchsia-50/70 p-5 dark:border-fuchsia-900/30 dark:bg-fuchsia-950/20"
              >
                <div>
                  <h4 class="font-semibold text-slate-900 dark:text-white">
                    {{ t('ai.summarize.summary') }}
                  </h4>
                  <p class="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                    {{ summaryResult.summary }}
                  </p>
                </div>

                <div v-if="summaryResult.key_points.length > 0">
                  <h4 class="font-semibold text-slate-900 dark:text-white">
                    {{ t('ai.summarize.keyPoints') }}
                  </h4>
                  <ul class="mt-2 space-y-2">
                    <li
                      v-for="(point, index) in summaryResult.key_points"
                      :key="index"
                      class="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300"
                    >
                      <span class="mt-1 text-fuchsia-500">•</span>
                      <span>{{ point }}</span>
                    </li>
                  </ul>
                </div>

                <div
                  v-if="summaryResult.topics.length > 0"
                  class="flex flex-wrap gap-2"
                >
                  <span
                    v-for="topic in summaryResult.topics"
                    :key="topic"
                    class="rounded-full bg-white px-3 py-1 text-sm text-fuchsia-700 dark:bg-slate-900 dark:text-fuchsia-200"
                  >
                    {{ topic }}
                  </span>
                </div>
              </div>
            </div>

            <div v-else-if="activeTab === 'ask'" class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.ask.title') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('ai.ask.description') }}
                </p>
              </div>

              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {{ t('ai.ask.question') }}
                </label>
                <textarea
                  v-model="question"
                  rows="4"
                  class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-fuchsia-400 focus:ring-4 focus:ring-fuchsia-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-fuchsia-400 dark:focus:ring-fuchsia-500/20"
                  :placeholder="t('ai.ask.placeholder')"
                />
              </div>

              <Button
                :disabled="processing || !selectedFile || !question"
                full-width
                @click="askQuestion"
              >
                <MessageCircle v-if="!processing" class="mr-2 h-4 w-4" />
                <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
                {{ processing ? t('common.processing') : t('ai.ask.submit') }}
              </Button>

              <div
                v-if="qaResult"
                class="space-y-4 rounded-[24px] border border-sky-100 bg-sky-50/70 p-5 dark:border-sky-900/30 dark:bg-sky-950/20"
              >
                <div class="flex items-center justify-between gap-3">
                  <h4 class="font-semibold text-slate-900 dark:text-white">
                    {{ t('ai.ask.answer') }}
                  </h4>
                  <span
                    :class="[
                      'rounded-full px-2.5 py-1 text-xs font-semibold',
                      qaResult.confidence === 'high'
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200'
                        : qaResult.confidence === 'medium'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/30 dark:text-amber-200'
                          : 'bg-rose-100 text-rose-700 dark:bg-rose-950/30 dark:text-rose-200',
                    ]"
                  >
                    {{ qaResult.confidence }} {{ t('ai.ask.confidence') }}
                  </span>
                </div>

                <p class="text-sm leading-7 text-slate-700 dark:text-slate-300">
                  {{ qaResult.answer }}
                </p>

                <div v-if="qaResult.relevant_excerpts.length > 0">
                  <h4 class="font-semibold text-slate-900 dark:text-white">
                    {{ t('ai.ask.excerpts') }}
                  </h4>
                  <div class="mt-2 space-y-2">
                    <div
                      v-for="(excerpt, index) in qaResult.relevant_excerpts"
                      :key="index"
                      class="rounded-2xl bg-white px-4 py-3 text-sm italic text-slate-600 dark:bg-slate-900 dark:text-slate-300"
                    >
                      "{{ excerpt }}"
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="activeTab === 'extract'" class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.extract.title') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('ai.extract.description') }}
                </p>
              </div>

              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {{ t('ai.extract.type') }}
                </label>
                <select
                  v-model="extractType"
                  class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-fuchsia-400 focus:ring-4 focus:ring-fuchsia-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-fuchsia-400 dark:focus:ring-fuchsia-500/20"
                >
                  <option value="general">
                    {{ t('ai.extract.general') }}
                  </option>
                  <option value="invoice">
                    {{ t('ai.extract.invoice') }}
                  </option>
                  <option value="resume">
                    {{ t('ai.extract.resume') }}
                  </option>
                  <option value="contract">
                    {{ t('ai.extract.contract') }}
                  </option>
                </select>
              </div>

              <Button
                :disabled="processing || !selectedFile"
                full-width
                @click="extractData"
              >
                <Database v-if="!processing" class="mr-2 h-4 w-4" />
                <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
                {{ processing ? t('common.processing') : t('ai.extract.extract') }}
              </Button>

              <div
                v-if="extractResult"
                class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
              >
                <h4 class="font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.extract.extractedData') }}
                </h4>
                <pre class="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-2xl bg-white p-4 text-sm text-slate-700 dark:bg-slate-900 dark:text-slate-300">{{ JSON.stringify(extractResult.extracted_data, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { aiAPI } from '@/services/api'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import ToolHeader from '@/components/tools/ToolHeader.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import {
  Sparkles,
  Loader2,
  MessageCircle,
  Database,
  BookOpen,
  HelpCircle,
  FileJson,
  FileText,
  X,
  LockKeyhole,
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const selectedFile = ref<File | null>(null)
const processing = ref(false)
const errorState = ref<FormattedUserError | null>(null)
const activeTab = ref('summarize')

const summaryLength = ref('medium')
const summaryResult = ref<any>(null)

const question = ref('')
const qaResult = ref<any>(null)

const extractType = ref('general')
const extractResult = ref<any>(null)

const tabs = computed(() => [
  { id: 'summarize', label: t('ai.tabs.summarize'), icon: BookOpen },
  { id: 'ask', label: t('ai.tabs.ask'), icon: HelpCircle },
  { id: 'extract', label: t('ai.tabs.extract'), icon: FileJson },
])

const canUseAI = computed(() => userStore.isAuthenticated && userStore.canUseCloudFeatures)

const ensureAccess = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
  canUseCloudFeatures: userStore.canUseCloudFeatures,
  requiresPro: true,
  pricingFeature: 'ai-analyzer',
})

const handleFileSelected = (files: File[]) => {
  if (files.length > 0) {
    selectedFile.value = files[0]
    errorState.value = null
    summaryResult.value = null
    qaResult.value = null
    extractResult.value = null
  }
}

const handleUploadError = (message: string) => {
  errorState.value = formatUserFacingError(new Error(message), {
    area: 'UPLOAD',
    fallbackMessage: message,
  })
}

const clearFile = () => {
  selectedFile.value = null
  summaryResult.value = null
  qaResult.value = null
  extractResult.value = null
  errorState.value = null
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const summarizePDF = async () => {
  if (!selectedFile.value) return
  if (!ensureAccess()) return

  try {
    processing.value = true
    errorState.value = null
    summaryResult.value = null

    const result = await aiAPI.summarize(selectedFile.value, summaryLength.value)
    summaryResult.value = result
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'AI',
      fallbackMessage: t('ai.errors.summarizeFailed'),
    })
  } finally {
    processing.value = false
  }
}

const askQuestion = async () => {
  if (!selectedFile.value || !question.value) return
  if (!ensureAccess()) return

  try {
    processing.value = true
    errorState.value = null
    qaResult.value = null

    const result = await aiAPI.ask(selectedFile.value, question.value)
    qaResult.value = result
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'AI',
      fallbackMessage: t('ai.errors.askFailed'),
    })
  } finally {
    processing.value = false
  }
}

const extractData = async () => {
  if (!selectedFile.value) return
  if (!ensureAccess()) return

  try {
    processing.value = true
    errorState.value = null
    extractResult.value = null

    const result = await aiAPI.extract(selectedFile.value, extractType.value)
    extractResult.value = result
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'AI',
      fallbackMessage: t('ai.errors.extractFailed'),
    })
  } finally {
    processing.value = false
  }
}
</script>
