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
import ToolHeader from '@/components/tools/ToolHeader.vue'
import ToolNoticeBar from '@/components/tools/ToolNoticeBar.vue'
import { advancedAPI } from '@/services/api'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { redirectForFeatureAccess } from '@/utils/feature-access'
import { historyManager } from '@/utils/history-manager'

const { locale } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const selectedFile = ref<File | null>(null)
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const isProcessing = ref(false)
const progress = ref(0)
const status = ref('')
const resultUrl = ref('')
const errorState = ref<FormattedUserError | null>(null)

const isZh = computed(() => locale.value.toLowerCase().startsWith('zh'))
const isEs = computed(() => locale.value.toLowerCase().startsWith('es'))

const copy = computed(() => {
  if (isZh.value) {
    return {
      title: '保护 PDF',
      subtitle: '为合同、资料和交付文件添加打开密码，分享前多一层保护。',
      badge: '登录可用',
      notice: '此功能会把 PDF 上传到服务器生成真正带打开密码的文件。处理完成后请及时下载，临时文件会按云端文件生命周期策略自动清理。',
      accessLabel: '需要登录',
      accessTitle: '登录后即可生成受密码保护的 PDF',
      accessDescription: '密码保护需要云端重新写入 PDF 安全信息。登录后可继续上传文件并下载加密结果。',
      goToSignIn: '登录后使用',
      accessSteps: ['登录账号', '上传 PDF 并设置密码', '下载受保护的新文件'],
      uploadLabel: '文件',
      uploadTitleIdle: '选择要保护的 PDF',
      uploadTitleSelected: '文件已准备好',
      uploadDescriptionIdle: '支持标准 PDF 文件。原文件不会被覆盖。',
      uploadDescriptionSelected: '确认密码后会生成一个新的加密 PDF。',
      dropTitle: '拖放 PDF 到这里',
      dropSubtitle: '或点击选择文件',
      passwordLabel: '打开密码',
      confirmLabel: '确认密码',
      passwordPlaceholder: '至少 6 位，建议使用字母和数字',
      confirmPlaceholder: '再次输入同一个密码',
      strengthLabel: '密码强度',
      weak: '较弱',
      fair: '可用',
      strong: '较强',
      mismatch: '两次输入的密码不一致。',
      tooShort: '密码至少需要 6 个字符。',
      noFile: '请先上传一份 PDF 文件。',
      protect: '生成受保护 PDF',
      processing: '正在写入密码保护...',
      uploading: '正在上传文件...',
      ready: '加密文件已生成',
      successTitle: 'PDF 已受保护',
      successMessage: '新的 PDF 已添加打开密码。请用刚才设置的密码打开验证。',
      download: '下载加密 PDF',
      workspaceTitle: '适合分享前最后一步',
      workspaceDescription: '给对外资料、合同草稿、内部文档增加基础访问门槛，减少误发后的直接打开风险。',
      step1: '上传 PDF 后，系统会生成独立副本，不会覆盖原文件。',
      step2: '密码只用于本次加密请求，请自行保存；平台不会在页面展示明文密码。',
      step3: '下载后建议用 PDF 阅读器打开一次，确认密码生效。',
    }
  }

  if (isEs.value) {
    return {
      title: 'Proteger PDF',
      subtitle: 'Añade una contraseña de apertura antes de compartir contratos o documentos importantes.',
      badge: 'Requiere inicio de sesión',
      notice: 'Este proceso sube el PDF al servidor para crear un archivo realmente protegido por contraseña. Descarga el resultado pronto; los archivos temporales se limpian segun la politica de ciclo de vida en la nube.',
      accessLabel: 'Inicio de sesión requerido',
      accessTitle: 'Inicia sesión para crear un PDF protegido',
      accessDescription: 'La protección con contraseña necesita reescribir el PDF en la nube. Después de iniciar sesión podrás subir el archivo y descargar el resultado.',
      goToSignIn: 'Iniciar sesión',
      accessSteps: ['Inicia sesión', 'Sube el PDF y define la contraseña', 'Descarga el archivo protegido'],
      uploadLabel: 'Archivo',
      uploadTitleIdle: 'Elige el PDF que quieres proteger',
      uploadTitleSelected: 'Archivo listo',
      uploadDescriptionIdle: 'Compatible con archivos PDF estándar. El archivo original no se sobrescribe.',
      uploadDescriptionSelected: 'Confirma la contraseña para crear un nuevo PDF protegido.',
      dropTitle: 'Arrastra tu PDF aqui',
      dropSubtitle: 'o haz clic para elegir un archivo',
      passwordLabel: 'Contraseña de apertura',
      confirmLabel: 'Confirmar contraseña',
      passwordPlaceholder: 'Minimo 6 caracteres; letras y numeros recomendado',
      confirmPlaceholder: 'Vuelve a escribir la misma contraseña',
      strengthLabel: 'Fortaleza',
      weak: 'Baja',
      fair: 'Aceptable',
      strong: 'Fuerte',
      mismatch: 'Las contraseñas no coinciden.',
      tooShort: 'La contraseña debe tener al menos 6 caracteres.',
      noFile: 'Sube primero un archivo PDF.',
      protect: 'Crear PDF protegido',
      processing: 'Aplicando protección...',
      uploading: 'Subiendo archivo...',
      ready: 'Archivo protegido listo',
      successTitle: 'PDF protegido',
      successMessage: 'El nuevo PDF ahora requiere contraseña para abrirse.',
      download: 'Descargar PDF protegido',
      workspaceTitle: 'Una capa extra antes de compartir',
      workspaceDescription: 'Ideal para documentos externos, borradores de contrato y archivos que no quieres dejar abiertos accidentalmente.',
      step1: 'Se crea una copia independiente; el archivo original no se modifica.',
      step2: 'La contraseña solo se usa para este proceso. Guardala en un lugar seguro.',
      step3: 'Abre el archivo descargado una vez para confirmar que la contraseña funciona.',
    }
  }

  return {
    title: 'Protect PDF',
    subtitle: 'Add an opening password before sharing contracts, drafts, and sensitive documents.',
    badge: 'Sign-in required',
    notice: 'This tool uploads the PDF to the server to create a truly password-protected file. Download the result promptly; temporary files are cleaned by the cloud file lifecycle policy.',
    accessLabel: 'Sign-in required',
    accessTitle: 'Sign in to create a protected PDF',
    accessDescription: 'Password protection needs cloud processing to rewrite the PDF security layer. After signing in, you can upload the file and download the protected result.',
    goToSignIn: 'Sign in to use',
    accessSteps: ['Sign in', 'Upload the PDF and set a password', 'Download the protected copy'],
    uploadLabel: 'File',
    uploadTitleIdle: 'Choose the PDF to protect',
    uploadTitleSelected: 'File is ready',
    uploadDescriptionIdle: 'Standard PDF files are supported. Your original file will not be overwritten.',
    uploadDescriptionSelected: 'Confirm the password to create a new protected PDF.',
    dropTitle: 'Drop your PDF here',
    dropSubtitle: 'or click to choose a file',
    passwordLabel: 'Open password',
    confirmLabel: 'Confirm password',
    passwordPlaceholder: 'At least 6 characters; letters and numbers recommended',
    confirmPlaceholder: 'Enter the same password again',
    strengthLabel: 'Password strength',
    weak: 'Weak',
    fair: 'Usable',
    strong: 'Strong',
    mismatch: 'The two passwords do not match.',
    tooShort: 'Password must be at least 6 characters.',
    noFile: 'Please upload a PDF file first.',
    protect: 'Create protected PDF',
    processing: 'Applying password protection...',
    uploading: 'Uploading file...',
    ready: 'Protected file is ready',
    successTitle: 'PDF protected',
    successMessage: 'The new PDF now requires the password to open.',
    download: 'Download protected PDF',
    workspaceTitle: 'One extra layer before sharing',
    workspaceDescription: 'Useful for external materials, contract drafts, and files you do not want opened accidentally.',
    step1: 'A separate copy is created; the original file is not modified.',
    step2: 'The password is only used for this processing request. Store it safely.',
    step3: 'Open the downloaded file once to confirm the password works.',
  }
})

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
      fallbackMessage: 'The PDF could not be protected. Please retry with a standard PDF file.',
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
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-950 dark:to-blue-950/30">
    <ToolHeader
      :title="copy.title"
      :subtitle="copy.subtitle"
      :badge="copy.badge"
      accent="blue"
    >
      <template #badgeIcon>
        <ShieldCheck class="h-4 w-4" />
      </template>
    </ToolHeader>

    <section class="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-6">
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
        <Card class="rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-blue-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
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

            <div class="grid gap-4 sm:grid-cols-2">
              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-900 dark:text-white">
                  {{ copy.passwordLabel }}
                </span>
                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    :placeholder="copy.passwordPlaceholder"
                    class="w-full rounded-2xl border border-slate-300 px-4 py-3 pr-12 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
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
                  class="w-full rounded-2xl border border-slate-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                >
              </label>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40">
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

            <div class="flex flex-col gap-3 sm:flex-row">
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
          <Card class="overflow-hidden rounded-[28px] border border-white/70 bg-white/90 shadow-xl shadow-blue-100/60 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-none">
            <div class="relative">
              <div class="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-blue-300/30 blur-3xl dark:bg-blue-500/20" />
              <div class="relative space-y-6">
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
                    class="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40"
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
            </div>
          </Card>

          <Card
            v-if="resultUrl"
            class="rounded-[28px] border border-emerald-200 bg-emerald-50/90 shadow-xl shadow-emerald-100/70 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:shadow-none"
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
    </section>
  </div>
</template>
