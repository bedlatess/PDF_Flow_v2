<template>
  <div class="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.16),transparent_32%),radial-gradient(circle_at_100%_0%,rgba(45,212,191,0.14),transparent_26%),linear-gradient(145deg,#f8fbff_0%,#eff6ff_48%,#f8fafc_100%)] px-4 py-8 dark:bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.14),transparent_26%),radial-gradient(circle_at_100%_0%,rgba(45,212,191,0.1),transparent_20%),linear-gradient(145deg,#020617_0%,#0f172a_52%,#111827_100%)]">
    <div class="absolute inset-0">
      <div class="absolute left-[-10rem] top-20 h-72 w-72 rounded-full bg-sky-200/55 blur-3xl dark:bg-sky-500/15" />
      <div class="absolute right-[-8rem] top-10 h-64 w-64 rounded-full bg-cyan-200/40 blur-3xl dark:bg-cyan-500/10" />
      <div class="absolute bottom-[-8rem] left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-white/70 blur-3xl dark:bg-white/5" />
    </div>

    <div class="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-5xl items-center gap-10 lg:grid-cols-[0.9fr_1.1fr]">
      <section class="px-2 py-8 lg:px-4">
        <div class="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/55 dark:text-sky-300">
          PDF-Flow
        </div>

        <div class="mt-8 max-w-xl">
          <h1 class="text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            Sign in and keep working.
          </h1>
          <p class="mt-5 text-base leading-8 text-slate-600 dark:text-slate-300 sm:text-lg">
            Access your document tools, recent activity, and account settings from one place without extra noise.
          </p>
        </div>

        <div class="mt-10 rounded-[32px] border border-white/80 bg-white/82 p-6 shadow-xl shadow-sky-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/58 dark:shadow-none">
          <div class="space-y-3">
            <p class="text-sm font-semibold uppercase tracking-[0.22em] text-sky-700 dark:text-sky-300">
              Secure account access
            </p>
            <p class="text-sm leading-7 text-slate-600 dark:text-slate-300">
              Use your account to continue across supported tools. If something fails, the page shows a short support-friendly message instead of internal system details.
            </p>
          </div>
        </div>
      </section>

      <section class="py-8">
        <div class="mx-auto w-full max-w-xl rounded-[36px] border border-white/80 bg-white/90 p-6 shadow-2xl shadow-sky-100/70 backdrop-blur dark:border-white/10 dark:bg-slate-900/82 dark:shadow-none sm:p-8">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">
                {{ $t('auth.welcomeBack') }}
              </h2>
              <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ $t('auth.loginSubtitle') }}
              </p>
            </div>

            <router-link
              to="/auth/register"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-sky-200 hover:text-sky-600 dark:border-slate-700 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
            >
              {{ $t('auth.signUp') }}
            </router-link>
          </div>

          <DiagnosticAlert
            v-if="errorState"
            class="mt-6"
            :title="errorState.title"
            :message="errorState.message"
            :diagnostic-code="errorState.diagnosticCode"
            :support-hint="errorState.supportHint"
          />

          <form @submit.prevent="handleLogin" class="mt-6 space-y-5">
            <div>
              <label for="email" class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                {{ $t('auth.email') }}
              </label>
              <input
                id="email"
                v-model="form.email"
                type="email"
                required
                autocomplete="email"
                :disabled="loading"
                class="w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-sky-400 dark:focus:ring-sky-500/20"
              />
              <p v-if="errors.email" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.email }}
              </p>
            </div>

            <div>
              <div class="mb-2 flex items-center justify-between gap-3">
                <label for="password" class="block text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {{ $t('auth.password') }}
                </label>
                <router-link
                  to="/auth/forgot-password"
                  class="text-sm font-medium text-sky-600 transition hover:text-sky-500 dark:text-sky-300"
                >
                  {{ $t('auth.forgotPassword') }}
                </router-link>
              </div>

              <div class="relative">
                <input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="current-password"
                  :disabled="loading"
                  class="w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 pr-12 text-slate-900 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-sky-400 dark:focus:ring-sky-500/20"
                />
                <button
                  type="button"
                  :disabled="loading"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-400 transition hover:text-slate-600 dark:hover:text-slate-200"
                  @click="showPassword = !showPassword"
                >
                  <component :is="showPassword ? EyeOff : Eye" class="h-5 w-5" />
                </button>
              </div>
              <p v-if="errors.password" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.password }}
              </p>
            </div>

            <div class="flex items-center justify-between gap-3 rounded-2xl bg-slate-50/90 px-4 py-3 dark:bg-slate-950/50">
              <label for="remember" class="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-300">
                <input
                  id="remember"
                  v-model="form.remember"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                  :disabled="loading"
                />
                <span>{{ $t('auth.rememberMe') }}</span>
              </label>
              <div class="h-2 w-2 rounded-full bg-emerald-400" />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="inline-flex w-full items-center justify-center rounded-2xl bg-slate-950 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-sky-500 dark:hover:bg-sky-400"
            >
              <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
              {{ loading ? $t('auth.loggingIn') : $t('auth.login') }}
            </button>
          </form>

          <div class="mt-6">
            <div class="relative">
              <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-slate-200 dark:border-slate-700" />
              </div>
              <div class="relative flex justify-center text-xs uppercase tracking-[0.22em] text-slate-400">
                <span class="bg-white px-3 dark:bg-slate-900">{{ $t('auth.orContinueWith') }}</span>
              </div>
            </div>

            <div class="mt-5 grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                :disabled="loading"
                class="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-sky-200 hover:text-sky-600 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
                @click="handleOAuthLogin('google')"
              >
                <svg class="mr-2 h-5 w-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
              </button>
              <button
                type="button"
                :disabled="loading"
                class="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:text-white"
                @click="handleOAuthLogin('github')"
              >
                <svg class="mr-2 h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                GitHub
              </button>
            </div>
          </div>

          <p class="mt-6 text-center text-sm text-slate-600 dark:text-slate-300">
            {{ $t('auth.noAccount') }}
            <router-link to="/auth/register" class="font-semibold text-sky-600 transition hover:text-sky-500 dark:text-sky-300">
              {{ $t('auth.signUp') }}
            </router-link>
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, EyeOff, Loader2 } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'

const router = useRouter()
const userStore = useUserStore()
const { t } = useI18n()

const form = reactive({
  email: '',
  password: '',
  remember: false,
})

const errors = reactive({
  email: '',
  password: '',
})

const showPassword = ref(false)
const loading = ref(false)
const errorState = ref<FormattedUserError | null>(null)

const validateForm = () => {
  errors.email = ''
  errors.password = ''
  errorState.value = null

  if (!form.email) {
    errors.email = t('auth.emailRequired')
    return false
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = t('auth.emailInvalid')
    return false
  }

  if (!form.password) {
    errors.password = t('auth.passwordRequired')
    return false
  }

  if (form.password.length < 6) {
    errors.password = t('auth.passwordTooShort')
    return false
  }

  return true
}

const handleLogin = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  errorState.value = null

  try {
    await userStore.login({
      email: form.email,
      password: form.password,
      remember: form.remember,
    })

    const redirect = router.currentRoute.value.query.redirect as string | undefined
    router.push(redirect || '/')
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackMessage: t('auth.loginFailed'),
    })
  } finally {
    loading.value = false
  }
}

const handleOAuthLogin = (provider: 'google' | 'github') => {
  const redirect = router.currentRoute.value.query.redirect as string | undefined
  if (redirect) {
    sessionStorage.setItem('oauth_redirect', redirect)
  }

  const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  window.location.href = `${backendUrl}/api/v1/auth/oauth/${provider}`
}
</script>
