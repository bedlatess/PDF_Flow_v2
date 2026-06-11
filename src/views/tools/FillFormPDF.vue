<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  CheckCircle2,
  Crown,
  Download,
  FileCheck,
  FileText,
  LockKeyhole,
  RotateCcw,
  Sparkles,
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
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'
import { memoryManager } from '@/utils/memory-manager'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const step = ref(1)
const uploadedFile = ref<File | null>(null)
const formFields = ref<any[]>([])
const loading = ref(false)
const progress = ref(0)
const errorState = ref<FormattedUserError | null>(null)
const resultUrl = ref('')
const isChinese = computed(() => locale.value.toLowerCase().startsWith('zh'))
const stepText = (value: number) => isChinese.value ? `\u6b65\u9aa4 ${value}` : `Step ${value}`

const canUseTool = computed(() => userStore.isAuthenticated && userStore.canUseCloudFeatures)

const primaryActionLabel = computed(() => {
  if (!userStore.isAuthenticated) {
    return t('tools.fillForm.useAfterLogin')
  }

  if (!userStore.canUseCloudFeatures) {
    return t('tools.fillForm.upgradeAfterLogin')
  }

  return t('tools.fillForm.fillForm')
})

const canSubmit = computed(() =>
  formFields.value.every((field) => {
    if (field.required) {
      return field.value !== '' && field.value !== null && field.value !== undefined
    }

    return true
  }),
)

const ensureAccess = () => redirectForFeatureAccess({
  router,
  route,
  isAuthenticated: userStore.isAuthenticated,
  canUseCloudFeatures: userStore.canUseCloudFeatures,
  requiresPro: true,
  pricingFeature: 'fill-form',
})

const handleFileUpload = async (files: File[]) => {
  if (files.length === 0) {
    return
  }

  uploadedFile.value = files[0]
  errorState.value = null
  step.value = 2

  if (!ensureAccess()) {
    return
  }

  await analyzeFormFields()
}

const handleRemoveFile = () => {
  uploadedFile.value = null
  formFields.value = []
  errorState.value = null
  step.value = 1
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
}

const analyzeFormFields = async () => {
  if (!uploadedFile.value) {
    return
  }

  if (!ensureAccess()) {
    return
  }

  loading.value = true
  errorState.value = null

  try {
    const result = await advancedAPI.getFormFields(uploadedFile.value)
    formFields.value = result.fields.map((field: any) => ({
      ...field,
      value: field.default_value || (field.type === 'checkbox' ? false : ''),
    }))
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'FORM',
      fallbackMessage: t('tools.fillForm.analyzeError'),
    })
    step.value = 1
  } finally {
    loading.value = false
  }
}

const handleFillForm = async () => {
  if (!uploadedFile.value || !canSubmit.value) {
    return
  }

  if (!ensureAccess()) {
    return
  }

  step.value = 3
  progress.value = 0
  errorState.value = null

  const payload = formFields.value.reduce((acc, field) => {
    acc[field.name] = field.value
    return acc
  }, {} as Record<string, any>)

  let progressInterval: ReturnType<typeof setInterval> | null = null

  try {
    progressInterval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += 10
      }
    }, 300)

    const blob = await advancedAPI.fillForm(uploadedFile.value, payload)
    progress.value = 100
    if (resultUrl.value) {
      memoryManager.revokeObjectURL(resultUrl.value)
    }
    resultUrl.value = memoryManager.createTemporaryURL(blob)
    step.value = 4
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'FORM',
      fallbackMessage: t('tools.fillForm.fillError'),
    })
    step.value = 2
  } finally {
    if (progressInterval) {
      clearInterval(progressInterval)
    }
  }
}

const handleDownload = async () => {
  if (!resultUrl.value) {
    return
  }

  try {
    const link = document.createElement('a')
    link.href = resultUrl.value
    link.download = 'filled-form.pdf'
    link.click()
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'FORM',
      fallbackMessage: t('common.downloadError'),
    })
  }
}

const handleReset = () => {
  uploadedFile.value = null
  formFields.value = []
  progress.value = 0
  errorState.value = null
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
  step.value = 1
}

onUnmounted(() => {
  if (resultUrl.value) {
    memoryManager.revokeObjectURL(resultUrl.value)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-amber-50 via-white to-orange-50 dark:from-slate-950 dark:via-slate-950 dark:to-amber-950/20">
    <ToolHeader
      :title="t('tools.fillForm.title')"
      :subtitle="t('tools.fillForm.description')"
      :badge="t('tools.fillForm.proOnly')"
      accent="amber"
    >
      <template #badgeIcon>
        <Crown class="h-4 w-4" />
      </template>

      <template #extra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          {{ t('tools.fillForm.pageExtra') }}
        </p>
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
      <ToolNoticeBar variant="amber">
        <template #icon>
          <Sparkles class="h-5 w-5" />
        </template>
        {{ t('tools.fillForm.notice') }}
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
        v-if="step === 1 && !canUseTool"
        class="mt-6"
        accent="amber"
        :label="t('tools.fillForm.accessLabel')"
        :title="userStore.isAuthenticated ? t('tools.fillForm.accessMemberTitle') : t('tools.fillForm.accessGuestTitle')"
        :description="userStore.isAuthenticated ? t('tools.fillForm.accessMemberDescription') : t('tools.fillForm.accessGuestDescription')"
        :action-label="userStore.isAuthenticated ? t('tools.fillForm.goToUpgrade') : t('tools.fillForm.goToSignIn')"
        :steps="[
          t('tools.fillForm.accessStep1'),
          t('tools.fillForm.accessStep2'),
          t('tools.fillForm.accessStep3'),
        ]"
        @action="ensureAccess()"
      >
        <template #actionIcon>
          <LockKeyhole class="mr-2 h-4 w-4" />
        </template>
      </ToolAccessPanel>

      <div class="mt-6 space-y-6">
        <div
          v-if="step === 1 && canUseTool"
          class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]"
        >
          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-amber-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-6">
              <div class="space-y-2">
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-500">
                  {{ t('tools.fillForm.uploadLabel') }}
                </p>
                <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.fillForm.uploadTitle') }}
                </h2>
                <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('tools.fillForm.uploadDescription') }}
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
                  {{ t('tools.fillForm.dropTitle') }}
                </template>
                <template #subtitle>
                  {{ t('tools.fillForm.dropSubtitle') }}
                </template>
              </DragDropZone>
            </div>
          </Card>

          <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-amber-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="space-y-6">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.fillForm.workspaceTitle') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('tools.fillForm.workspaceDescription') }}
                </p>
              </div>

              <div class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.fillForm.flowTitle') }}
                </p>
                <div class="mt-4 space-y-3">
                  <div class="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-sm font-semibold text-white">1</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.fillForm.flowStep1') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-orange-500 text-sm font-semibold text-white">2</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.fillForm.flowStep2') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-2xl bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-yellow-500 text-sm font-semibold text-white">3</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.fillForm.flowStep3') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <Card
          v-if="step === 2"
          class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-amber-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
        >
          <div
            v-if="loading"
            class="space-y-6 py-6 text-center"
          >
            <div class="mx-auto h-14 w-14 animate-spin rounded-full border-4 border-amber-100 border-t-amber-500 dark:border-amber-950 dark:border-t-amber-400" />
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-500">
                {{ stepText(2) }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.fillForm.stepDetecting') }}
              </h2>
              <p class="text-sm text-slate-600 dark:text-slate-300">
                {{ t('tools.fillForm.analyzing') }}
              </p>
            </div>
          </div>

          <div
            v-else-if="formFields.length > 0"
            class="space-y-6"
          >
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-500">
                {{ stepText(2) }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.fillForm.stepReview') }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t('tools.fillForm.foundFields', { count: formFields.length }) }}
              </p>
            </div>

            <FilePreview
              v-if="uploadedFile"
              :file="uploadedFile"
              @remove="handleRemoveFile"
            />

            <div class="space-y-4">
              <div
                v-for="(field, index) in formFields"
                :key="`${field.name}-${index}`"
                class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
              >
                <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <label class="block text-sm font-semibold text-slate-900 dark:text-white">
                      {{ field.name }}
                      <span
                        v-if="field.required"
                        class="ml-1 text-red-500"
                      >*</span>
                    </label>
                    <p class="mt-1 text-xs uppercase tracking-[0.14em] text-slate-400">
                      {{ t(`tools.fillForm.fieldTypes.${field.type}`) }}
                    </p>
                  </div>

                  <span
                    :class="[
                      'rounded-full px-3 py-1 text-xs font-semibold',
                      field.required
                        ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-200'
                        : 'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
                    ]"
                  >
                    {{ field.required ? t('common.required') : t('common.optional') }}
                  </span>
                </div>

                <input
                  v-if="field.type === 'text'"
                  v-model="field.value"
                  type="text"
                  :placeholder="field.default_value || t('tools.fillForm.enterValue')"
                  class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                >

                <label
                  v-else-if="field.type === 'checkbox'"
                  class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                >
                  <input
                    v-model="field.value"
                    type="checkbox"
                    class="h-4 w-4 rounded border-slate-300 text-amber-500 focus:ring-amber-500"
                  >
                  <span>{{ field.default_value || t('tools.fillForm.checkThis') }}</span>
                </label>

                <div
                  v-else-if="field.type === 'radio'"
                  class="grid gap-3 sm:grid-cols-2"
                >
                  <label
                    v-for="(option, optionIndex) in field.options || []"
                    :key="optionIndex"
                    class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                  >
                    <input
                      v-model="field.value"
                      type="radio"
                      :value="option"
                      class="h-4 w-4 border-slate-300 text-amber-500 focus:ring-amber-500"
                    >
                    <span>{{ option }}</span>
                  </label>
                </div>

                <select
                  v-else-if="field.type === 'dropdown'"
                  v-model="field.value"
                  class="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                >
                  <option value="">
                    {{ t('tools.fillForm.selectOption') }}
                  </option>
                  <option
                    v-for="(option, optionIndex) in field.options || []"
                    :key="optionIndex"
                    :value="option"
                  >
                    {{ option }}
                  </option>
                </select>
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
                :disabled="!canSubmit"
                full-width
                @click="handleFillForm"
              >
                <FileCheck class="mr-2 h-4 w-4" />
                {{ primaryActionLabel }}
              </Button>
            </div>
          </div>

          <div
            v-else
            class="space-y-6 py-6 text-center"
          >
            <div class="space-y-2">
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.fillForm.noFields') }}
              </h2>
              <p class="text-sm text-slate-600 dark:text-slate-300">
                {{ t('tools.fillForm.noFieldsHelp') }}
              </p>
            </div>
            <Button
              variant="outline"
              size="lg"
              @click="step = 1"
            >
              {{ t('common.back') }}
            </Button>
          </div>
        </Card>

        <Card
          v-if="step === 3"
          class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-amber-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
        >
          <div class="space-y-6 py-6 text-center">
            <div class="mx-auto h-14 w-14 animate-spin rounded-full border-4 border-amber-100 border-t-amber-500 dark:border-amber-950 dark:border-t-amber-400" />
            <div class="space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-amber-500">
                {{ stepText(3) }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.fillForm.stepGenerating') }}
              </h2>
              <p class="text-sm text-slate-600 dark:text-slate-300">
                {{ t('tools.fillForm.filling') }}
              </p>
            </div>

            <ProgressBar
              :progress="progress"
              :label="t('tools.fillForm.preparingResult')"
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
                {{ t('tools.fillForm.ready') }}
              </p>
              <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                {{ t('tools.fillForm.success') }}
              </h2>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ t('tools.fillForm.successMessage') }}
              </p>
              <p class="text-sm font-medium text-emerald-700 dark:text-emerald-200">
                {{ t('tools.fillForm.filledFields', { count: formFields.length }) }}
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
                {{ t('common.fillAnother') }}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </section>
  </div>
</template>
