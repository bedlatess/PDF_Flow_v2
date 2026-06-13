<template>
  <AuthWorkspaceShell :copy="marketingCopy" accent="teal">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">
                {{ $t('auth.createAccount') }}
              </h2>
              <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ $t('auth.registerSubtitle') }}
              </p>
            </div>

            <router-link
              to="/auth/login"
              class="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-teal-200 hover:text-teal-600 dark:border-slate-700 dark:text-slate-200 dark:hover:border-teal-500/40 dark:hover:text-teal-300"
            >
              {{ $t('auth.login') }}
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

          <form @submit.prevent="handleRegister" class="mt-6 space-y-5">
            <div>
              <label for="fullName" class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                {{ $t('auth.fullName') }}
              </label>
              <input
                id="fullName"
                v-model="form.fullName"
                type="text"
                required
                autocomplete="name"
                :disabled="loading"
                class="w-full rounded-md border border-slate-200 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-teal-400 dark:focus:ring-teal-500/20"
              />
              <p v-if="errors.fullName" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.fullName }}
              </p>
            </div>

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
                class="w-full rounded-md border border-slate-200 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-teal-400 dark:focus:ring-teal-500/20"
              />
              <p v-if="errors.email" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.email }}
              </p>
            </div>

            <div>
              <label for="password" class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                {{ $t('auth.password') }}
              </label>
              <div class="relative">
                <input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="new-password"
                  :disabled="loading"
                  class="w-full rounded-md border border-slate-200 bg-white/80 px-4 py-3 pr-12 text-slate-900 outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-teal-400 dark:focus:ring-teal-500/20"
                />
                <button
                  type="button"
                  :disabled="loading"
                  :aria-label="showPassword ? $t('auth.hidePassword') : $t('auth.showPassword')"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-400 transition hover:text-slate-600 dark:hover:text-slate-200"
                  @click="showPassword = !showPassword"
                >
                  <component :is="showPassword ? EyeOff : Eye" class="h-5 w-5" />
                </button>
              </div>

              <div class="mt-3">
                <div class="flex gap-2">
                  <div
                    v-for="i in 4"
                    :key="i"
                    class="h-1.5 flex-1 rounded-full transition-all"
                    :class="i <= passwordStrength ? strengthColors[passwordStrength] : 'bg-slate-200 dark:bg-slate-700'"
                  />
                </div>
                <p class="mt-2 text-xs font-medium" :class="strengthTextColors[passwordStrength]">
                  {{ strengthLabels[passwordStrength] }}
                </p>
              </div>

              <p v-if="errors.password" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.password }}
              </p>
            </div>

            <div>
              <label for="confirmPassword" class="mb-2 block text-sm font-semibold text-slate-800 dark:text-slate-200">
                {{ $t('auth.confirmPassword') }}
              </label>
              <div class="relative">
                <input
                  id="confirmPassword"
                  v-model="form.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  required
                  autocomplete="new-password"
                  :disabled="loading"
                  class="w-full rounded-md border border-slate-200 bg-white/80 px-4 py-3 pr-12 text-slate-900 outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white dark:focus:border-teal-400 dark:focus:ring-teal-500/20"
                />
                <button
                  type="button"
                  :disabled="loading"
                  :aria-label="showConfirmPassword ? $t('auth.hidePassword') : $t('auth.showPassword')"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-400 transition hover:text-slate-600 dark:hover:text-slate-200"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <component :is="showConfirmPassword ? EyeOff : Eye" class="h-5 w-5" />
                </button>
              </div>
              <p v-if="errors.confirmPassword" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.confirmPassword }}
              </p>
            </div>

            <div class="rounded-md bg-slate-50/90 px-4 py-4 dark:bg-slate-950/50">
              <label for="terms" class="flex min-h-8 items-start gap-3 text-sm leading-6 text-slate-700 dark:text-slate-300">
                <input
                  id="terms"
                  v-model="form.acceptTerms"
                  type="checkbox"
                  class="mt-1 h-5 w-5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  :disabled="loading"
                />
                <span>
                  {{ $t('auth.iAgree') }}
                  <a href="/terms" target="_blank" class="inline-flex min-h-8 items-center px-1 font-semibold text-teal-600 transition hover:text-teal-500 dark:text-teal-300">
                    {{ $t('auth.terms') }}
                  </a>
                  {{ $t('auth.and') }}
                  <a href="/privacy" target="_blank" class="inline-flex min-h-8 items-center px-1 font-semibold text-teal-600 transition hover:text-teal-500 dark:text-teal-300">
                    {{ $t('auth.privacy') }}
                  </a>
                </span>
              </label>
              <p v-if="errors.acceptTerms" class="mt-2 text-sm text-rose-600 dark:text-rose-300">
                {{ errors.acceptTerms }}
              </p>
            </div>

            <button
              type="submit"
              :disabled="loading || !form.acceptTerms"
              class="inline-flex w-full items-center justify-center rounded-md bg-slate-950 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-teal-600 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-teal-500 dark:hover:bg-teal-400"
            >
              <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
              {{ loading ? $t('auth.creatingAccount') : $t('auth.signUp') }}
            </button>
          </form>

          <p class="mt-6 text-center text-sm text-slate-600 dark:text-slate-300">
            {{ $t('auth.alreadyHaveAccount') }}
            <router-link to="/auth/login" class="inline-flex min-h-8 items-center px-1 font-semibold text-teal-600 transition hover:text-teal-500 dark:text-teal-300">
              {{ $t('auth.login') }}
            </router-link>
          </p>
  </AuthWorkspaceShell>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, EyeOff, Loader2 } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import AuthWorkspaceShell from '@/components/auth/AuthWorkspaceShell.vue'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { useLocalePath } from '@/composables/useLocalePath'

const router = useRouter()
const userStore = useUserStore()
const { t, tm } = useI18n()
const { localePath } = useLocalePath()

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

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
})

const errors = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: '',
})

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const errorState = ref<FormattedUserError | null>(null)

const marketingCopy = computed(() => tm('auth.registerMarketing') as AuthMarketingCopy)

const passwordStrength = computed(() => {
  const password = form.password
  if (!password) {
    return 0
  }

  let strength = 0
  if (password.length >= 8) strength += 1
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 1
  if (/\d/.test(password)) strength += 1
  if (/[^a-zA-Z\d]/.test(password)) strength += 1

  return strength
})

const strengthColors = ['bg-slate-200', 'bg-rose-500', 'bg-amber-500', 'bg-sky-500', 'bg-emerald-500']
const strengthTextColors = ['text-slate-500', 'text-rose-600', 'text-amber-600', 'text-sky-600', 'text-emerald-600']
const strengthLabels = computed(() => [
  '',
  t('auth.passwordWeak'),
  t('auth.passwordFair'),
  t('auth.passwordGood'),
  t('auth.passwordStrong'),
])

const validateForm = () => {
  errors.fullName = ''
  errors.email = ''
  errors.password = ''
  errors.confirmPassword = ''
  errors.acceptTerms = ''
  errorState.value = null

  if (!form.fullName.trim()) {
    errors.fullName = t('auth.fullNameRequired')
    return false
  }

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

  if (form.password.length < 8) {
    errors.password = t('auth.passwordTooShort8')
    return false
  }

  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = t('auth.passwordsNotMatch')
    return false
  }

  if (!form.acceptTerms) {
    errors.acceptTerms = t('auth.mustAcceptTerms')
    return false
  }

  return true
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  errorState.value = null

  try {
    await userStore.register({
      email: form.email,
      password: form.password,
      full_name: form.fullName,
    })

    router.push({
      path: localePath('/auth/login'),
      query: { registered: 'true' },
    })
  } catch (error) {
    errorState.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackTitle: t('auth.registerFailedTitle'),
      fallbackMessage: t('auth.registerFailed'),
    })
  } finally {
    loading.value = false
  }
}
</script>
