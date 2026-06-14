<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loader2, ShieldAlert } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { formatUserFacingError } from '@/utils/error-messages'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  email: '',
  password: '',
})

const loading = ref(false)
const errorMessage = ref('')

const reason = computed(() => String(route.query.reason || 'auth'))
const isForbidden = computed(() => reason.value === 'forbidden')
const isPasswordChanged = computed(() => reason.value === 'password_changed')

const publicHomeUrl = computed(() => {
  if (window.location.hostname === 'admin.pawn.eu.org') {
    return 'https://pdf.pawn.eu.org/zh-cn/'
  }
  return '/zh-cn/'
})

const title = computed(() =>
  isForbidden.value ? '没有后台权限' : '管理员登录'
)

const description = computed(() =>
  isForbidden.value
    ? '当前账号不是管理员。请使用拥有 admin 角色的账号重新登录后台。'
    : '后台和主站是独立域名，请在这里使用管理员账号登录。'
)

const handleLogin = async () => {
  errorMessage.value = ''
  loading.value = true

  try {
    const user = await userStore.login({
      email: form.email,
      password: form.password,
      remember: true,
    })

    if (user.role !== 'admin') {
      await userStore.logout()
      errorMessage.value = '该账号不是管理员，不能进入后台。'
      return
    }

    router.push(String(route.query.redirect || '/'))
  } catch (error) {
    errorMessage.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackMessage: '登录失败，请检查邮箱和密码。',
    }).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10 text-white">
    <section class="w-full max-w-xl rounded-lg border border-white/10 bg-white p-6 text-slate-950 shadow-2xl sm:p-8">
      <div class="flex h-12 w-12 items-center justify-center rounded-md bg-slate-950 text-white">
        <ShieldAlert class="h-6 w-6" />
      </div>
      <h1 class="mt-5 text-3xl font-semibold">{{ title }}</h1>
      <p class="mt-3 text-sm leading-7 text-slate-600">{{ description }}</p>
      <p
        v-if="isPasswordChanged"
        class="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700"
      >
        Password changed. Sign in again with the new administrator password.
      </p>

      <form class="mt-6 space-y-4" @submit.prevent="handleLogin">
        <div>
          <label for="admin-email" class="mb-2 block text-sm font-semibold text-slate-800">
            管理员邮箱
          </label>
          <input
            id="admin-email"
            v-model="form.email"
            type="email"
            required
            autocomplete="email"
            :disabled="loading"
            class="w-full rounded-md border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-4 focus:ring-slate-100 disabled:opacity-60"
          />
        </div>

        <div>
          <label for="admin-password" class="mb-2 block text-sm font-semibold text-slate-800">
            密码
          </label>
          <input
            id="admin-password"
            v-model="form.password"
            type="password"
            required
            autocomplete="current-password"
            :disabled="loading"
            class="w-full rounded-md border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-4 focus:ring-slate-100 disabled:opacity-60"
          />
        </div>

        <p
          v-if="errorMessage"
          class="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
        >
          {{ errorMessage }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="inline-flex min-h-11 w-full items-center justify-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
          {{ loading ? '正在登录' : '进入后台' }}
        </button>
      </form>

      <a
        class="mt-4 inline-flex min-h-10 items-center text-sm font-semibold text-slate-600 transition hover:text-slate-950"
        :href="publicHomeUrl"
      >
        返回主站首页
      </a>
    </section>
  </main>
</template>
