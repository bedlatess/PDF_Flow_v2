<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  Crown,
  FileText,
  LockKeyhole,
  RotateCcw,
  Sparkles,
} from 'lucide-vue-next'
import { advancedAPI } from '@/services/api'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import DragDropZone from '@/components/pdf/DragDropZone.vue'
import FilePreview from '@/components/pdf/FilePreview.vue'
import ToolPageShell from '@/components/tools/ToolPageShell.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import ToolAccessPanel from '@/components/tools/ToolAccessPanel.vue'
import ToolWorkspace from '@/components/tools/ToolWorkspace.vue'
import ToolActionPanel from '@/components/tools/ToolActionPanel.vue'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'
import { memoryManager } from '@/utils/memory-manager'

const { t } = useI18n()
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
const stepText = (value: number) => t('tools.fillForm.stepLabel', { step: value })
const fieldInputId = (field: any, index: number) => `fill-form-field-${index}-${String(field.name || 'field').replace(/[^a-zA-Z0-9_-]/g, '-')}`
const fillText = (key: string, fallback: string, params?: Record<string, unknown>) => {
  const value = t(key, params || {})
  return value === key ? fallback : value
}

const canUseTool = computed(() => userStore.isAuthenticated && userStore.canUseCloudFeatures)

const primaryActionLabel = computed(() => {
  if (!userStore.isAuthenticated) {
    return t('tools.fillForm.useAfterLogin')
  }

  if (!userStore.canUseCloudFeatures) {
    return t('tools.fillForm.upgradeAfterLogin')
  }

  return fillText('tools.fillForm.fillForm', 'Fill Form')
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
  <ToolPageShell
      :title="t('tools.fillForm.title')"
      :subtitle="t('tools.fillForm.desc')"
      :badge="t('tools.fillForm.proOnly')"
      pro
      accent="amber"
    width="md"
  >

      <template #badgeIcon>
        <Crown class="h-4 w-4" />
      </template>

      <template #headerExtra>
        <p class="mx-auto max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          {{ t('tools.fillForm.pageExtra') }}
        </p>
      </template>
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

      <ToolWorkspace
        v-if="step === 1 && canUseTool"
        class="mt-6"
        layout="wide-secondary"
      >
        <template #upload>
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
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
          </section>
        </template>

        <template #secondary>
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <div class="space-y-6">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.fillForm.workspaceTitle') }}
                </h3>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ t('tools.fillForm.workspaceDescription') }}
                </p>
              </div>

              <div class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">
                  {{ t('tools.fillForm.flowTitle') }}
                </p>
                <div class="mt-4 space-y-3">
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-sm font-semibold text-white">1</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.fillForm.flowStep1') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-orange-500 text-sm font-semibold text-white">2</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.fillForm.flowStep2') }}
                    </p>
                  </div>
                  <div class="flex items-start gap-3 rounded-md bg-white px-4 py-4 dark:bg-slate-900">
                    <span class="flex h-8 w-8 items-center justify-center rounded-full bg-yellow-500 text-sm font-semibold text-white">3</span>
                    <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ t('tools.fillForm.flowStep3') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </template>
      </ToolWorkspace>

      <ToolWorkspace
        v-if="step === 2"
        class="mt-6"
        layout="wide-primary"
      >
        <template #primary>
          <section class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-5">
            <FilePreview
              v-if="uploadedFile"
              :file="uploadedFile"
              class="mb-5"
              @remove="handleRemoveFile"
            />

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
                  {{ fillText('tools.fillForm.foundFields', `${formFields.length} fields found`, { count: formFields.length }) }}
                </p>
              </div>

              <div class="space-y-4">
                <div
                  v-for="(field, index) in formFields"
                  :key="`${field.name}-${index}`"
                  class="rounded-md border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
                >
                  <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <label
                        :for="field.type === 'radio' ? undefined : fieldInputId(field, index)"
                        class="block text-sm font-semibold text-slate-900 dark:text-white"
                      >
                        {{ field.name }}
                        <span
                          v-if="field.required"
                          class="ml-1 text-red-500"
                        >*</span>
                      </label>
                      <p class="mt-1 text-xs uppercase tracking-[0.14em] text-slate-400">
                        {{ fillText(`tools.fillForm.fieldTypes.${field.type}`, field.type) }}
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
                    :id="fieldInputId(field, index)"
                    v-model="field.value"
                    type="text"
                    :placeholder="field.default_value || fillText('tools.fillForm.enterValue', 'Enter value')"
                    class="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                  >

                  <label
                    v-else-if="field.type === 'checkbox'"
                    :for="fieldInputId(field, index)"
                    class="flex items-center gap-3 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                  >
                    <input
                      :id="fieldInputId(field, index)"
                      v-model="field.value"
                      type="checkbox"
                      class="h-4 w-4 rounded border-slate-300 text-amber-500 focus:ring-amber-500"
                    >
                    <span>{{ field.default_value || fillText('tools.fillForm.checkThis', 'Check this') }}</span>
                  </label>

                  <div
                    v-else-if="field.type === 'radio'"
                    class="grid gap-3 sm:grid-cols-2"
                  >
                    <label
                      v-for="(option, optionIndex) in field.options || []"
                      :key="optionIndex"
                      class="flex items-center gap-3 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
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
                    :id="fieldInputId(field, index)"
                    v-model="field.value"
                    class="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-amber-400 dark:focus:ring-amber-500/20"
                  >
                    <option value="">
                      {{ fillText('tools.fillForm.selectOption', 'Select an option') }}
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
            </div>
          </section>
        </template>

        <template #secondary>
          <ToolActionPanel
            :label="stepText(2)"
            :title="loading ? t('tools.fillForm.stepDetecting') : t('tools.fillForm.workspaceTitle')"
            :description="formFields.length > 0 ? fillText('tools.fillForm.foundFields', `${formFields.length} fields found`, { count: formFields.length }) : t('tools.fillForm.workspaceDescription')"
            accent="amber"
            :action-label="primaryActionLabel"
            :loading="loading"
            :disabled="loading || formFields.length === 0 || !canSubmit"
            @action="handleFillForm"
          >
            <template #details>
              <Button
                variant="outline"
                size="lg"
                full-width
                @click="step = 1"
              >
                <ArrowLeft class="mr-2 h-4 w-4" />
                {{ t('common.back') }}
              </Button>
            </template>
          </ToolActionPanel>
        </template>
      </ToolWorkspace>

      <ToolWorkspace
        v-if="step === 3"
        class="mt-6"
      >
        <template #primary>
          <ToolActionPanel
            :label="stepText(3)"
            :title="t('tools.fillForm.stepGenerating')"
            :description="fillText('tools.fillForm.filling', 'Filling form fields')"
            accent="amber"
            :show-progress="true"
            :progress="progress"
            :progress-label="t('tools.fillForm.preparingResult')"
            :action-label="t('common.processing')"
            :loading="true"
            disabled
            @action="() => {}"
          />
        </template>
      </ToolWorkspace>

      <ToolWorkspace
        v-if="step === 4"
        class="mt-6"
      >
        <template #primary>
          <ToolActionPanel
            :label="t('tools.fillForm.ready')"
            :title="fillText('tools.fillForm.success', 'Form filled')"
            :description="t('tools.fillForm.successMessage')"
            accent="emerald"
            :action-label="t('common.download')"
            @action="handleDownload"
          >
            <template #details>
              <p class="text-center text-sm font-medium text-emerald-700 dark:text-emerald-200">
                {{ fillText('tools.fillForm.filledFields', `${formFields.length} fields filled`, { count: formFields.length }) }}
              </p>
              <Button
                variant="outline"
                size="lg"
                full-width
                @click="handleReset"
              >
                <RotateCcw class="mr-2 h-4 w-4" />
                {{ t('common.fillAnother') }}
              </Button>
            </template>
          </ToolActionPanel>
        </template>
      </ToolWorkspace>

  </ToolPageShell>
</template>
