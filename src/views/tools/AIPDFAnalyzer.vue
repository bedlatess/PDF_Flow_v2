<template>
  <ToolPageShell
      :title="t('ai.title')"
      :subtitle="t('ai.subtitle')"
      :badge="t('ai.proBadge')"
      pro
      accent="pink"
    width="md"
  >

      <template #badgeIcon>
        <Sparkles class="h-4 w-4" />
      </template>

      <template #headerExtra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          {{ t('ai.pageExtra') }}
        </p>
      </template>
      <ToolNoticeBar variant="purple">
        <template #icon>
          <Sparkles class="h-5 w-5" />
        </template>
        {{ t('ai.notice') }}
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
        v-if="!canUseAI"
        class="mt-6"
        accent="pink"
        :label="t('ai.accessLabel')"
        :title="userStore.isAuthenticated ? t('ai.accessMemberTitle') : t('ai.accessGuestTitle')"
        :description="userStore.isAuthenticated ? t('ai.accessMemberDescription') : t('ai.accessGuestDescription')"
        :action-label="userStore.isAuthenticated ? t('ai.goToUpgrade') : t('ai.goToSignIn')"
        :steps="[
          t('ai.accessStep1'),
          t('ai.accessStep2'),
          t('ai.accessStep3'),
        ]"
        @action="ensureAccess()"
      >
        <template #actionIcon>
          <LockKeyhole class="mr-2 h-4 w-4" />
        </template>
      </ToolAccessPanel>

      <div v-if="canUseAI" class="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-fuchsia-500">
                {{ t('ai.uploadLabel') }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ selectedFile ? t('ai.uploadTitleSelected') : t('ai.uploadTitleIdle') }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ selectedFile ? t('ai.uploadDescriptionSelected') : t('ai.uploadDescriptionIdle') }}
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
                {{ t('ai.dropPDF') }}
              </template>
              <template #subtitle>
                {{ t('ai.dropSubtitle') }}
              </template>
            </DragDropZone>

            <div
              v-else
              class="space-y-4"
            >
              <div class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
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
                    {{ t('common.replace') }}
                  </Button>
                </div>
              </div>

              <div class="rounded-md border border-slate-200 bg-slate-50/70 p-5 text-sm leading-6 text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300">
                <p class="font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.suggestedFlowTitle') }}
                </p>
                <p class="mt-2">
                  {{ t('ai.suggestedFlowDescription') }}
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card
          v-if="selectedFile"
          class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
        >
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
                <label
                  for="ai-summary-length"
                  class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200"
                >
                  {{ t('ai.summarize.length') }}
                </label>
                <select
                  id="ai-summary-length"
                  v-model="summaryLength"
                  class="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-fuchsia-400 focus:ring-4 focus:ring-fuchsia-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-fuchsia-400 dark:focus:ring-fuchsia-500/20"
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
                class="space-y-4 rounded-md border border-fuchsia-100 bg-fuchsia-50/70 p-5 dark:border-fuchsia-900/30 dark:bg-fuchsia-950/20"
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
                      <span class="mt-1 text-fuchsia-500">&bull;</span>
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
                <label
                  for="ai-question"
                  class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200"
                >
                  {{ t('ai.ask.question') }}
                </label>
                <textarea
                  id="ai-question"
                  v-model="question"
                  rows="4"
                  class="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-fuchsia-400 focus:ring-4 focus:ring-fuchsia-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-fuchsia-400 dark:focus:ring-fuchsia-500/20"
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
                class="space-y-4 rounded-md border border-sky-100 bg-sky-50/70 p-5 dark:border-sky-900/30 dark:bg-sky-950/20"
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
                      class="rounded-md bg-white px-4 py-3 text-sm italic text-slate-600 dark:bg-slate-900 dark:text-slate-300"
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
                <label
                  for="ai-extract-type"
                  class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200"
                >
                  {{ t('ai.extract.type') }}
                </label>
                <select
                  id="ai-extract-type"
                  v-model="extractType"
                  class="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-fuchsia-400 focus:ring-4 focus:ring-fuchsia-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-fuchsia-400 dark:focus:ring-fuchsia-500/20"
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
                class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
              >
                <h4 class="font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.extract.extractedData') }}
                </h4>
                <pre class="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-white p-4 text-sm text-slate-700 dark:bg-slate-900 dark:text-slate-300">{{ JSON.stringify(extractResult.extracted_data, null, 2) }}</pre>
              </div>
            </div>

            <div v-else-if="activeTab === 'batch'" class="space-y-5">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('ai.batch.title') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('ai.batch.description') }}
                </p>
              </div>

              <div class="grid gap-3 sm:grid-cols-3">
                <label
                  v-for="operation in batchOperationOptions"
                  :key="operation.value"
                  :class="[
                    'cursor-pointer rounded-[22px] border p-4 transition-all',
                    batchOperations.includes(operation.value)
                      ? 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-800 shadow-sm dark:border-fuchsia-700 dark:bg-fuchsia-950/30 dark:text-fuchsia-100'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-fuchsia-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-fuchsia-700/60',
                  ]"
                >
                  <input
                    v-model="batchOperations"
                    class="sr-only"
                    type="checkbox"
                    :value="operation.value"
                  >
                  <component
                    :is="operation.icon"
                    class="h-5 w-5"
                  />
                  <span class="mt-3 block text-sm font-semibold">
                    {{ operation.label }}
                  </span>
                  <span class="mt-1 block text-xs leading-5 opacity-75">
                    {{ operation.description }}
                  </span>
                </label>
              </div>

              <Button
                :disabled="processing || !selectedFile || batchOperations.length === 0"
                full-width
                @click="batchAnalyzePDF"
              >
                <Layers3 v-if="!processing" class="mr-2 h-4 w-4" />
                <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
                {{ processing ? t('common.processing') : t('ai.batch.start') }}
              </Button>

              <div
                v-if="batchResult"
                class="space-y-4 rounded-md border border-fuchsia-100 bg-fuchsia-50/70 p-5 dark:border-fuchsia-900/30 dark:bg-fuchsia-950/20"
              >
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h4 class="font-semibold text-slate-900 dark:text-white">
                      {{ t('ai.batch.complete') }}
                    </h4>
                    <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
                      {{ t('ai.batch.completedCount', { count: batchResult.operations_completed?.length || batchOperations.length }) }}
                    </p>
                  </div>
                  <span
                    v-if="batchClassificationLabel"
                    class="rounded-full bg-white px-3 py-1 text-sm font-semibold text-fuchsia-700 dark:bg-slate-900 dark:text-fuchsia-200"
                  >
                    {{ batchClassificationLabel }}
                  </span>
                </div>

                <pre class="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-white p-4 text-sm leading-6 text-slate-700 dark:bg-slate-900 dark:text-slate-300">{{ JSON.stringify(batchResult.results || batchResult, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </Card>
      </div>
  </ToolPageShell>
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
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import {
  Sparkles,
  Loader2,
  MessageCircle,
  Database,
  BookOpen,
  HelpCircle,
  FileJson,
  Layers3,
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

const batchOperations = ref(['summarize', 'extract'])
const batchResult = ref<any>(null)

const batchClassificationLabel = computed(() => {
  const classification = batchResult.value?.results?.classification
  if (!classification?.category) return ''

  const confidence = classification.confidence ? ` · ${classification.confidence}` : ''
  return `${classification.category}${confidence}`
})

const tabs = computed(() => [
  { id: 'summarize', label: t('ai.tabs.summarize'), icon: BookOpen },
  { id: 'ask', label: t('ai.tabs.ask'), icon: HelpCircle },
  { id: 'extract', label: t('ai.tabs.extract'), icon: FileJson },
  { id: 'batch', label: t('ai.tabs.batch'), icon: Layers3 },
])

const batchOperationOptions = computed(() => [
  {
    value: 'summarize',
    label: t('ai.batch.operations.summarize.label'),
    description: t('ai.batch.operations.summarize.description'),
    icon: BookOpen,
  },
  {
    value: 'extract',
    label: t('ai.batch.operations.extract.label'),
    description: t('ai.batch.operations.extract.description'),
    icon: FileJson,
  },
  {
    value: 'classify',
    label: t('ai.batch.operations.classify.label'),
    description: t('ai.batch.operations.classify.description'),
    icon: Layers3,
  },
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
    batchResult.value = null
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
  batchResult.value = null
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

const batchAnalyzePDF = async () => {
  if (!selectedFile.value || batchOperations.value.length === 0) return
  if (!ensureAccess()) return

  try {
    processing.value = true
    errorState.value = null
    batchResult.value = null

    const result = await aiAPI.batchAnalyze(selectedFile.value, batchOperations.value)
    batchResult.value = result
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'AI',
      fallbackMessage: t('ai.errors.batchFailed'),
    })
  } finally {
    processing.value = false
  }
}
</script>
