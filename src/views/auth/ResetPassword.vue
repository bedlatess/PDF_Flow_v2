<template>
  <AuthWorkspaceShell :copy="marketingCopy" accent="teal">
    <div>
      <h2 class="text-3xl font-semibold text-slate-950 dark:text-white">
        {{ $t('auth.resetPasswordTitle') }}
      </h2>
      <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {{ $t('auth.resetPasswordSubtitle') }}
      </p>
    </div>

    <DiagnosticAlert
      v-if="notice"
      class="mt-6"
      :title="notice.title"
      :message="notice.message"
      :diagnostic-code="notice.status ? notice.diagnosticCode : ''"
      :support-hint="notice.supportHint"
      :tone="notice.tone"
    />

    <form class="mt-6 space-y-5" @submit.prevent="submit">
      <div>
        <label for="password" class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
          {{ $t('auth.newPassword') }}
        </label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          autocomplete="new-password"
          :disabled="loading || completed || !token"
          class="w-full rounded-md border border-slate-200 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 disabled:opacity-70 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-teal-400 dark:focus:ring-teal-500/20"
        >
        <p v-if="passwordError" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
          {{ passwordError }}
        </p>
      </div>

      <div>
        <label for="confirm-password" class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
          {{ $t('auth.confirmPassword') }}
        </label>
        <input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          required
          autocomplete="new-password"
          :disabled="loading || completed || !token"
          class="w-full rounded-md border border-slate-200 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 disabled:opacity-70 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-teal-400 dark:focus:ring-teal-500/20"
        >
        <p v-if="confirmError" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
          {{ confirmError }}
        </p>
      </div>

      <button
        type="submit"
        :disabled="loading || completed || !token"
        class="inline-flex w-full items-center justify-center rounded-md bg-slate-950 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-teal-600 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-teal-500 dark:hover:bg-teal-400"
      >
        <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
        {{ loading ? $t('auth.resetPasswordSaving') : $t('auth.resetPasswordSubmit') }}
      </button>
    </form>

    <div class="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
      <router-link to="/auth/login" class="font-semibold text-teal-600 transition hover:text-teal-500 dark:text-teal-300">
        {{ $t('auth.backToLogin') }}
      </router-link>
      <router-link to="/auth/forgot-password" class="text-slate-600 transition hover:text-slate-950 dark:text-slate-300 dark:hover:text-white">
        {{ $t('auth.requestNewResetLink') }}
      </router-link>
    </div>
  </AuthWorkspaceShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import AuthWorkspaceShell from '@/components/auth/AuthWorkspaceShell.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import { authAPI } from '@/services/api'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { getFirstQueryValue } from '@/utils/route-state'

type ResetNotice = FormattedUserError & { tone?: 'danger' | 'warning' | 'info' }

interface AuthMarketingHighlight {
  title: string
  description: string
}

interface AuthMarketingCopy {
  heroTitle: string
  heroDescription: string
  panelTitle: string
  panelDescription: string
  highlights: AuthMarketingHighlight[]
}

const route = useRoute()
const { t, tm } = useI18n()

const token = ref('')
const password = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const confirmError = ref('')
const loading = ref(false)
const completed = ref(false)
const notice = ref<ResetNotice | null>(null)

const marketingCopy = computed(() => tm('auth.recoveryMarketing') as AuthMarketingCopy)

onMounted(() => {
  token.value = getFirstQueryValue(route.query.token)
  if (!token.value) {
    notice.value = {
      title: t('auth.resetPasswordMissingTitle'),
      message: t('auth.resetPasswordMissingMessage'),
      diagnosticCode: '',
      supportHint: t('auth.requestNewResetLink'),
      tone: 'warning',
    }
  }
})

const validate = () => {
  passwordError.value = ''
  confirmError.value = ''

  if (password.value.length < 8) {
    passwordError.value = t('auth.passwordTooShort8')
    return false
  }

  if (password.value !== confirmPassword.value) {
    confirmError.value = t('auth.passwordsNotMatch')
    return false
  }

  return true
}

const submit = async () => {
  if (!token.value || !validate()) {
    return
  }

  loading.value = true
  notice.value = null

  try {
    await authAPI.resetPassword({
      token: token.value,
      new_password: password.value,
    })
    completed.value = true
    notice.value = {
      title: t('auth.resetPasswordSuccessTitle'),
      message: t('auth.resetPasswordSuccessMessage'),
      diagnosticCode: '',
      supportHint: t('auth.resetPasswordSuccessHint'),
      tone: 'info',
    }
  } catch (error) {
    notice.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackTitle: t('auth.resetPasswordFailedTitle'),
      fallbackMessage: t('auth.resetPasswordFailedMessage'),
    })
  } finally {
    loading.value = false
  }
}
</script>
