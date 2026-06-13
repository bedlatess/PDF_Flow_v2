<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-950">
    <div class="w-full max-w-lg rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-md bg-sky-50 text-sky-600 dark:bg-sky-500/10 dark:text-sky-300">
        <AlertCircle v-if="status === 'error'" class="h-7 w-7" />
        <CheckCircle2 v-else-if="status === 'complete'" class="h-7 w-7" />
        <Loader2 v-else class="h-7 w-7 animate-spin" />
      </div>

      <p class="mt-5 text-xs font-semibold uppercase tracking-[0.14em] text-sky-700 dark:text-sky-300">
        {{ t('auth.oauthCallback.badge') }}
      </p>
      <h1 class="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
        {{ statusTitle }}
      </h1>
      <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {{ statusMessage }}
      </p>

      <div v-if="status === 'error'" class="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
        <Button variant="primary" @click="goToLogin">
          {{ t('auth.oauthCallback.backToLogin') }}
        </Button>
        <Button variant="outline" @click="goHome">
          {{ t('auth.oauthCallback.goHome') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-vue-next'
import Button from '@/components/common/Button.vue'
import { useUserStore } from '@/stores/user'
import { getFirstQueryValue, resolveInternalRedirect } from '@/utils/route-state'
import { useLocalePath } from '@/composables/useLocalePath'

type CallbackStatus = 'checking' | 'saving' | 'complete' | 'error'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const userStore = useUserStore()
const { localePath } = useLocalePath()
const status = ref<CallbackStatus>('checking')

const clearCallbackUrl = () => {
  if (typeof window === 'undefined') return
  window.history.replaceState({}, document.title, route.path)
}

const statusTitle = computed(() => {
  if (status.value === 'error') return t('auth.oauthCallback.errorTitle')
  if (status.value === 'complete') return t('auth.oauthCallback.completeTitle')
  return t('auth.processingLogin')
})

const statusMessage = computed(() => {
  if (status.value === 'saving') return t('auth.oauthCallback.saving')
  if (status.value === 'complete') return t('auth.oauthCallback.redirecting')
  if (status.value === 'error') return t('auth.oauthCallback.errorMessage')
  return t('auth.pleaseWait')
})

onMounted(async () => {
  try {
    const accessToken = getFirstQueryValue(route.query.access_token)
    const refreshToken = getFirstQueryValue(route.query.refresh_token)

    clearCallbackUrl()

    if (!accessToken || !refreshToken) {
      throw new Error('Missing tokens in callback')
    }

    status.value = 'saving'
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)

    await userStore.checkAuth()

    status.value = 'complete'
    const redirect = resolveInternalRedirect(sessionStorage.getItem('oauth_redirect'))
    sessionStorage.removeItem('oauth_redirect')

    await router.replace(redirect)
  } catch (error) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    sessionStorage.removeItem('oauth_redirect')
    status.value = 'error'
  }
})

const goToLogin = () => {
  router.replace({
    path: localePath('/auth/login'),
    query: { error: 'oauth_callback_failed' },
  })
}

const goHome = () => {
  router.replace(localePath('/'))
}
</script>
