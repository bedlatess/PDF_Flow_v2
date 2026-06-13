<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  CheckCircle2,
  Download,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
  LogIn,
  ShieldCheck,
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
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const isProcessing = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const errorState = ref<FormattedUserError | null>(null)

const copy = computed<ToolPageCopy>(() => tm('tools.protect.page') as ToolPageCopy)

const passwordScore = computed(() => {
  let score = 0
  if (password.value.length >= 6) score += 1
  if (password.value.length >= 10) score += 1
  if (/[a-zA-Z]/.test(password.value) && /\d/.test(password.value)) score += 1
  if (/[^a-zA-Z0-9]/.test(password.value)) score += 1
  return Math.min(score, 3)
})

const strengthText = computed(() => {
  if (passwordScore.value >= 3) return copy.value.strong
  if (passwordScore.value >= 2) return copy.value.fair
  return copy.value.weak
})

const strengthClass = computed(() => {
  if (passwordScore.value >= 3) return 'bg-emerald-500'
  if (passwordScore.value >= 2) return 'bg-blue-500'
  return 'bg-amber-500'
})

const canSubmit = computed(() =>
  !!selectedFile.value
  && password.value.length >= 6
  && password.value === confirmPassword.value
  && !isProcessing.value
)

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
  errorState.value = null
  revokeResultUrl()
}

const removeFile = () => {
  selectedFile.value = null
  errorState.value = null
  progress.value = 0
  status.value = ''
  revokeResultUrl()
}

const validate = () => {
  if (!selectedFile.value) {
    errorState.value = formatUserFacingError(new Error(copy.value.noFile), {
      area: 'PROTECT',
      fallbackMessage: copy.value.noFile,
    })
    return false
  }
  if (password.value.length < 6) {
    errorState.value = formatUserFacingError(new Error(copy.value.tooShort), {
      area: 'PROTECT',
      fallbackMessage: copy.value.tooShort,
    })
    return false
  }
  if (password.value !== confirmPassword.value) {
    errorState.value = formatUserFacingError(new Error(copy.value.mismatch), {
      area: 'PROTECT',
      fallbackMessage: copy.value.mismatch,
    })
    return false
  }
  return true
}

const protectPDF = async () => {
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
    const blob = await advancedAPI.protectPDF(selectedFile.value, password.value)
    resultUrl.value = URL.createObjectURL(blob)
    progress.value = 100
    status.value = copy.value.ready

    historyManager.addHistory({
      type: 'protect',
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      resultSize: blob.size,
    })
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'PROTECT',
      fallbackMessage: copy.value.errorFailed,
    })
  } finally {
    isProcessing.value = false
  }
}

const downloadResult = () => {
  if (!resultUrl.value || !selectedFile.value) return
  const link = document.createElement('a')
  link.href = resultUrl.value
  link.download = selectedFile.value.name.replace(/\.pdf$/i, '') + '-protected.pdf'
  link.click()
}

onUnmounted(() => {
  revokeResultUrl()
})
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
        <ShieldCheck class="h-4 w-4" />
      </template>
      <ToolNoticeBar variant="blue">
        <template #icon>
          <LockKeyhole class="h-5 w-5" />
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
        @action="ensureLogin()"
      >
        <template #actionIcon>
          <LogIn class="mr-2 h-4 w-4" />
        </template>
      </ToolAccessPanel>

      <div
        v-if="userStore.isAuthenticated"
        class="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]"
      >
        <Card class="rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
          <div class="space-y-6">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-blue-500">
                {{ copy.uploadLabel }}
              </p>
              <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                {{ selectedFile ? copy.uploadTitleSelected : copy.uploadTitleIdle }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ selectedFile ? copy.uploadDescriptionSelected : copy.uploadDescriptionIdle }}
              </p>
            </div>

            <DragDropZone
              v-if="!selectedFile"
              accept="pdf"
              :multiple="false"
              :max-files="1"
              @files-selected="handleFilesSelected"
            >
              <template #icon>
                <LockKeyhole class="h-12 w-12" />
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

            <div
              v-if="selectedFile"
              class="grid gap-4 sm:grid-cols-2"
            >
              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.passwordLabel }}
                </span>
                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    :placeholder="copy.passwordPlaceholder"
                    class="w-full rounded-md border border-slate-300 px-4 py-3 pr-12 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                  >
                  <button
                    type="button"
                    class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                    @click="showPassword = !showPassword"
                  >
                    <EyeOff v-if="showPassword" class="h-5 w-5" />
                    <Eye v-else class="h-5 w-5" />
                  </button>
                </div>
              </label>

              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.confirmLabel }}
                </span>
                <input
                  v-model="confirmPassword"
                  :type="showPassword ? 'text' : 'password'"
                  :placeholder="copy.confirmPlaceholder"
                  class="w-full rounded-md border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                >
              </label>
            </div>

            <div
              v-if="selectedFile"
              class="rounded-md border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40"
            >
              <div class="flex items-center justify-between gap-3 text-sm">
                <span class="font-semibold text-slate-700 dark:text-slate-200">
                  {{ copy.strengthLabel }}
                </span>
                <span class="font-semibold text-slate-500 dark:text-slate-300">
                  {{ strengthText }}
                </span>
              </div>
              <div class="mt-3 grid grid-cols-3 gap-2">
                <span
                  v-for="index in 3"
                  :key="index"
                  :class="[
                    'h-2 rounded-full transition',
                    index <= passwordScore ? strengthClass : 'bg-slate-200 dark:bg-slate-800',
                  ]"
                />
              </div>
            </div>

            <ProgressBar
              v-if="isProcessing || resultUrl"
              :progress="progress"
              :label="status"
              variant="primary"
              size="md"
            />

            <div
              v-if="selectedFile"
              class="flex flex-col gap-3 sm:flex-row"
            >
              <Button
                variant="primary"
                size="lg"
                :loading="isProcessing"
                :disabled="!canSubmit"
                full-width
                @click="protectPDF"
              >
                <KeyRound class="mr-2 h-4 w-4" />
                {{ isProcessing ? copy.processing : copy.protect }}
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

        <div class="space-y-6">
          <Card
            v-if="selectedFile"
            class="overflow-hidden rounded-lg border border-white/70 bg-white/90 shadow-sm dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none"
          >
            <div class="space-y-6">
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
                    class="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                  >
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white dark:bg-blue-500">
                      {{ index + 1 }}
                    </span>
                    <p class="pt-0.5 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {{ step }}
                    </p>
                  </div>
                </div>
            </div>
          </Card>

          <Card
            v-if="resultUrl"
            class="rounded-lg border border-emerald-200 bg-emerald-50/90 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
          >
            <div class="flex items-start gap-4">
              <CheckCircle2 class="mt-0.5 h-6 w-6 shrink-0 text-emerald-500" />
              <div class="space-y-3">
                <div>
                  <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                    {{ copy.successTitle }}
                  </h3>
                  <p class="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {{ copy.successMessage }}
                  </p>
                </div>

                <Button
                  variant="primary"
                  @click="downloadResult"
                >
                  <Download class="mr-2 h-4 w-4" />
                  {{ copy.download }}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
  </ToolPageShell>
</template>
