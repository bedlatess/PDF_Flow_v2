<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  CheckCircle2,
  Crown,
  Download,
  FileText,
  FileType,
  Highlighter,
  LockKeyhole,
  MessageSquare,
  RotateCcw,
} from 'lucide-vue-next'
import { advancedAPI } from '@/services/api'
import Button from '@/components/common/Button.vue'
import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolHeader from '@/components/tools/ToolHeader.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const step = ref(1)
const uploadedFile = ref<File | null>(null)
const annotationType = ref<'text' | 'highlight'>('text')
const progress = ref(0)
const errorState = ref<FormattedUserError | null>(null)
const resultJobId = ref('')

const textAnnotation = ref({
  text: '',
  page: 1,
  x: 100,
  y: 100,
  color: '#FF0000',
})

const highlightAnnotation = ref({
  page: 1,
  x1: 100,
  y1: 100,
  x2: 300,
  y2: 120,
  color: '#FFFF00',
})

const textColors = [
  { name: 'Red', value: '#FF0000' },
  { name: 'Blue', value: '#2563EB' },
  { name: 'Green', value: '#059669' },
  { name: 'Black', value: '#111827' },
]

const highlightColors = [
  { name: 'Yellow', value: '#FACC15' },
  { name: 'Mint', value: '#34D399' },
  { name: 'Sky', value: '#38BDF8' },
  { name: 'Pink', value: '#F472B6' },
]

const canUseTool = computed(() => userStore.isAuthenticated && userStore.canUseCloudFeatures)

const primaryActionLabel = computed(() => {
  if (!userStore.isAuthenticated) {
    return 'Sign in to annotate'
  }

  if (!userStore.canUseCloudFeatures) {
    return 'Upgrade to Pro to annotate'
  }

  return t('tools.annotate.addAnnotation')
})

const canAnnotate = computed(() => {
  if (annotationType.value === 'text') {
    return textAnnotation.value.text.trim() !== '' && textAnnotation.value.page >= 1
  }

  return highlightAnnotation.value.page >= 1
})

const ensureAccess = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
  canUseCloudFeatures: userStore.canUseCloudFeatures,
  requiresPro: true,
  pricingFeature: 'annotate',
})

const handleFileUpload = (files: File[]) => {
  if (files.length === 0) {
    return
  }

  uploadedFile.value = files[0]
  errorState.value = null
  step.value = 2
}

const handleRemoveFile = () => {
  uploadedFile.value = null
  errorState.value = null
  step.value = 1
}

const handleAnnotate = async () => {
  if (!uploadedFile.value || !canAnnotate.value) {
    return
  }

  if (!ensureAccess()) {
    return
  }

  step.value = 3
  progress.value = 0
  errorState.value = null

  let progressInterval: ReturnType<typeof setInterval> | null = null

  try {
    progressInterval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += 10
      }
    }, 300)

    const result = annotationType.value === 'text'
      ? await advancedAPI.annotateText(
        uploadedFile.value,
        textAnnotation.value.text,
        textAnnotation.value.page,
        textAnnotation.value.x,
        textAnnotation.value.y,
        textAnnotation.value.color,
      )
      : await advancedAPI.annotateHighlight(
        uploadedFile.value,
        highlightAnnotation.value.page,
        highlightAnnotation.value.x1,
        highlightAnnotation.value.y1,
        highlightAnnotation.value.x2,
        highlightAnnotation.value.y2,
        highlightAnnotation.value.color,
      )

    progress.value = 100
    resultJobId.value = result.job_id
    step.value = 4
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'ANNOTATE',
      fallbackMessage: t('tools.annotate.annotateError'),
    })
    step.value = 2
  } finally {
    if (progressInterval) {
      clearInterval(progressInterval)
    }
  }
}

const handleDownload = async () => {
  if (!resultJobId.value) {
    return
  }

  try {
    await advancedAPI.downloadResult(resultJobId.value, 'annotated.pdf')
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'ANNOTATE',
      fallbackMessage: t('common.downloadError'),
    })
  }
}

const handleReset = () => {
  uploadedFile.value = null
  resultJobId.value = ''
  progress.value = 0
  errorState.value = null
  annotationType.value = 'text'
  textAnnotation.value = {
    text: '',
    page: 1,
    x: 100,
    y: 100,
    color: '#FF0000',
  }
  highlightAnnotation.value = {
    page: 1,
    x1: 100,
    y1: 100,
    x2: 300,
    y2: 120,
    color: '#FFFF00',
  }
  step.value = 1
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 dark:from-slate-950 dark:via-slate-950 dark:to-purple-950/20">
    <ToolHeader
      :title="t('tools.annotate.title')"
      :subtitle="t('tools.annotate.description')"
      :badge="t('tools.annotate.proOnly')"
      accent="purple"
    >
      <template #badgeIcon>
        <Crown class="h-4 w-4" />
      </template>

      <template #extra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          Upload once, configure either text notes or highlight regions, then export a clean annotated PDF from a single focused layout.
        </p>
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
      <ToolNoticeBar variant="purple">
        <template #icon>
          <Crown class="h-5 w-5" />
        </template>
        This annotation flow uses cloud processing. Guests are sent to sign in first, and only signed-in users see the Pro upgrade path.
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
        v-if="step === 1 && !canUseTool"
        class="mt-6"
      >
        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div class="space-y-4">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                Access
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ userStore.isAuthenticated ? 'Upgrade required after login' : 'Sign in before annotating PDFs' }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ userStore.isAuthenticated
                  ? 'Your account is active, but annotation is a Pro cloud feature. Upgrade only when you actually need this workflow.'
                  : 'Please sign in first so the system can check your account and route you to the right access step.' }}
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
                  2. Choose text note or highlight mode
                </div>
                <div class="rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                  3. Export the annotated PDF
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div class="mt-6 space-y-6">
        <Card
          v-if="step === 1"
          class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
        >
          <div class="space-y-6">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                Step 1
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                Upload a PDF to annotate
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                Start with one PDF, then configure text notes or highlight regions inside the same workspace.
              </p>
            </div>

            <DragDropZone
              accept="application/pdf,.pdf"
              :multiple="false"
              :max-files="1"
              @files-selected="handleFileUpload"
            >
              <template #icon>
                <FileText class="h-12 w-12" />
              </template>
              <template #title>
                Upload the PDF you want to annotate
              </template>
              <template #subtitle>
                Sign in first, then continue with text notes or highlight regions.
              </template>
            </DragDropZone>
          </div>
        </Card>

        <Card
          v-if="step === 2"
          class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
        >
          <div class="space-y-6">
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                Step 2
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                Configure annotation
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                Choose the annotation mode first, then define page, coordinates, and color before exporting.
              </p>
            </div>

            <FilePreview
              v-if="uploadedFile"
              :file="uploadedFile"
              @remove="handleRemoveFile"
            />

            <div class="grid gap-6 lg:grid-cols-[0.86fr_1.14fr]">
              <div class="space-y-6">
                <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                  <label class="block text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                    Annotation mode
                  </label>

                  <div class="mt-4 space-y-3">
                    <button
                      :class="[
                        'w-full rounded-2xl border px-4 py-4 text-left transition-all',
                        annotationType === 'text'
                          ? 'border-purple-300 bg-purple-50 shadow-sm dark:border-purple-700 dark:bg-purple-950/30'
                          : 'border-slate-200 bg-white hover:border-purple-200 dark:border-slate-700 dark:bg-slate-900',
                      ]"
                      @click="annotationType = 'text'"
                    >
                      <div class="flex items-start gap-3">
                        <MessageSquare :class="['mt-0.5 h-5 w-5', annotationType === 'text' ? 'text-purple-500' : 'text-slate-400']" />
                        <div>
                          <p class="font-semibold text-slate-900 dark:text-white">
                            {{ t('tools.annotate.types.text') }}
                          </p>
                          <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                            {{ t('tools.annotate.types.textDesc') }}
                          </p>
                        </div>
                      </div>
                    </button>

                    <button
                      :class="[
                        'w-full rounded-2xl border px-4 py-4 text-left transition-all',
                        annotationType === 'highlight'
                          ? 'border-amber-300 bg-amber-50 shadow-sm dark:border-amber-700 dark:bg-amber-950/20'
                          : 'border-slate-200 bg-white hover:border-amber-200 dark:border-slate-700 dark:bg-slate-900',
                      ]"
                      @click="annotationType = 'highlight'"
                    >
                      <div class="flex items-start gap-3">
                        <Highlighter :class="['mt-0.5 h-5 w-5', annotationType === 'highlight' ? 'text-amber-500' : 'text-slate-400']" />
                        <div>
                          <p class="font-semibold text-slate-900 dark:text-white">
                            {{ t('tools.annotate.types.highlight') }}
                          </p>
                          <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                            {{ t('tools.annotate.types.highlightDesc') }}
                          </p>
                        </div>
                      </div>
                    </button>
                  </div>
                </div>

                <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 text-sm leading-6 text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300">
                  <p class="font-semibold text-slate-900 dark:text-white">
                    Coordinate hint
                  </p>
                  <p class="mt-2">
                    Use page coordinates from the original PDF space. Start with the page number, then adjust X and Y values gradually for a faster setup loop.
                  </p>
                </div>
              </div>

              <div class="space-y-6">
                <div
                  v-if="annotationType === 'text'"
                  class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
                >
                  <div class="space-y-4">
                    <div>
                      <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                        {{ t('tools.annotate.text.content') }}
                      </label>
                      <textarea
                        v-model="textAnnotation.text"
                        rows="4"
                        :placeholder="t('tools.annotate.text.placeholder')"
                        class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-400 focus:ring-4 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-purple-400 dark:focus:ring-purple-500/20"
                      />
                    </div>

                    <div class="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                          {{ t('tools.annotate.text.page') }}
                        </label>
                        <input
                          v-model.number="textAnnotation.page"
                          type="number"
                          min="1"
                          :placeholder="t('tools.annotate.text.pagePlaceholder')"
                          class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-400 focus:ring-4 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-purple-400 dark:focus:ring-purple-500/20"
                        >
                      </div>

                      <div>
                        <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                          {{ t('tools.annotate.text.color') }}
                        </label>
                        <div class="flex flex-wrap gap-2">
                          <button
                            v-for="color in textColors"
                            :key="color.value"
                            :class="[
                              'h-10 w-10 rounded-xl border-2 transition',
                              textAnnotation.color === color.value
                                ? 'scale-105 border-slate-900 dark:border-white'
                                : 'border-slate-200 dark:border-slate-700',
                            ]"
                            :style="{ backgroundColor: color.value }"
                            :title="color.name"
                            @click="textAnnotation.color = color.value"
                          />
                        </div>
                      </div>
                    </div>

                    <div class="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                          {{ t('tools.annotate.text.x') }}
                        </label>
                        <input
                          v-model.number="textAnnotation.x"
                          type="number"
                          min="0"
                          class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-400 focus:ring-4 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-purple-400 dark:focus:ring-purple-500/20"
                        >
                      </div>

                      <div>
                        <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                          {{ t('tools.annotate.text.y') }}
                        </label>
                        <input
                          v-model.number="textAnnotation.y"
                          type="number"
                          min="0"
                          class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-400 focus:ring-4 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-purple-400 dark:focus:ring-purple-500/20"
                        >
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  v-else
                  class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
                >
                  <div class="space-y-4">
                    <div class="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                          {{ t('tools.annotate.highlight.page') }}
                        </label>
                        <input
                          v-model.number="highlightAnnotation.page"
                          type="number"
                          min="1"
                          :placeholder="t('tools.annotate.highlight.pagePlaceholder')"
                          class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                        >
                      </div>

                      <div>
                        <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                          {{ t('tools.annotate.highlight.color') }}
                        </label>
                        <div class="flex flex-wrap gap-2">
                          <button
                            v-for="color in highlightColors"
                            :key="color.value"
                            :class="[
                              'h-10 w-10 rounded-xl border-2 transition',
                              highlightAnnotation.color === color.value
                                ? 'scale-105 border-slate-900 dark:border-white'
                                : 'border-slate-200 dark:border-slate-700',
                            ]"
                            :style="{ backgroundColor: color.value }"
                            :title="color.name"
                            @click="highlightAnnotation.color = color.value"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
                        {{ t('tools.annotate.highlight.coordinates') }}
                      </label>
                      <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                        <input
                          v-model.number="highlightAnnotation.x1"
                          type="number"
                          placeholder="x1"
                          class="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                        >
                        <input
                          v-model.number="highlightAnnotation.y1"
                          type="number"
                          placeholder="y1"
                          class="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                        >
                        <input
                          v-model.number="highlightAnnotation.x2"
                          type="number"
                          placeholder="x2"
                          class="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                        >
                        <input
                          v-model.number="highlightAnnotation.y2"
                          type="number"
                          placeholder="y2"
                          class="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                        >
                      </div>
                      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
                        {{ t('tools.annotate.highlight.coordsHelp') }}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="flex flex-col gap-3 sm:flex-row">
                  <Button
                    variant="outline"
                    size="lg"
                    @click="step = 1"
                  >
                    <ArrowLeft class="mr-2 h-4 w-4" />
                    {{ t('common.back') }}
                  </Button>
                  <Button
                    size="lg"
                    :disabled="!canAnnotate"
                    full-width
                    @click="handleAnnotate"
                  >
                    <FileType class="mr-2 h-4 w-4" />
                    {{ primaryActionLabel }}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card
          v-if="step === 3"
          class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-purple-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
        >
          <div class="space-y-6 py-6 text-center">
            <div class="mx-auto h-14 w-14 animate-spin rounded-full border-4 border-purple-100 border-t-purple-500 dark:border-purple-950 dark:border-t-purple-400" />
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-purple-500">
                Step 3
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                Generating the annotated PDF
              </h2>
              <p class="text-sm text-slate-600 dark:text-slate-300">
                {{ t('tools.annotate.processing') }}
              </p>
            </div>

            <ProgressBar
              :progress="progress"
              label="Preparing the annotated PDF..."
              variant="primary"
              size="md"
            />
          </div>
        </Card>

        <Card
          v-if="step === 4"
          class="rounded-[28px] border border-emerald-200 bg-emerald-50/90 shadow-xl shadow-emerald-100/70 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
        >
          <div class="space-y-6 py-4 text-center">
            <CheckCircle2 class="mx-auto h-16 w-16 text-emerald-500" />
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-500">
                Ready
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.annotate.success') }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t('tools.annotate.successMessage') }}
              </p>
              <p class="text-sm font-medium text-emerald-700 dark:text-emerald-200">
                {{ annotationType === 'text' ? t('tools.annotate.textAdded') : t('tools.annotate.highlightAdded') }}
              </p>
            </div>

            <div class="flex flex-col gap-3 sm:flex-row sm:justify-center">
              <Button
                size="lg"
                @click="handleDownload"
              >
                <Download class="mr-2 h-4 w-4" />
                {{ t('common.download') }}
              </Button>
              <Button
                variant="outline"
                size="lg"
                @click="handleReset"
              >
                <RotateCcw class="mr-2 h-4 w-4" />
                {{ t('common.annotateAnother') }}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </section>
  </div>
</template>
