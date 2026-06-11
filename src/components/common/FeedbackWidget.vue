<script setup lang="ts">
import { computed, ref } from 'vue'
import { Bug, CheckCircle2, ClipboardCopy, Loader2, MessageSquare, X } from 'lucide-vue-next'
import { feedbackAPI } from '@/services/api'
import { useSettingsStore } from '@/stores/settings'
import { useUserStore } from '@/stores/user'

const settingsStore = useSettingsStore()
const userStore = useUserStore()

const open = ref(false)
const submitting = ref(false)
const copied = ref(false)
const error = ref('')
const resultId = ref<number | null>(null)
const MAX_MESSAGE_LENGTH = 4000

const form = ref({
  title: '',
  message: '',
  email: '',
  category: 'bug',
  severity: 'normal',
})

const diagnosticCode = computed(() => {
  const now = new Date()
  const date = now.toISOString().slice(0, 10).replace(/-/g, '')
  return `PDF-${date}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`
})

const currentDiagnostics = () => ({
  path: window.location.pathname,
  url: window.location.href,
  locale: settingsStore.locale,
  theme: settingsStore.theme,
  viewport: `${window.innerWidth}x${window.innerHeight}`,
  userAgent: navigator.userAgent,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  timestamp: new Date().toISOString(),
  authState: userStore.isAuthenticated ? `signed-in:${userStore.user?.role || 'unknown'}` : 'guest',
})

const feedbackSummary = computed(() => {
  if (!resultId.value) return ''
  return `反馈编号 #${resultId.value}\n诊断码 ${diagnosticCode.value}\n页面 ${window.location.href}`
})
const messageLength = computed(() => form.value.message.length)
const messageRemaining = computed(() => MAX_MESSAGE_LENGTH - messageLength.value)

const resetForm = () => {
  form.value = {
    title: '',
    message: '',
    email: userStore.user?.email || '',
    category: 'bug',
    severity: 'normal',
  }
  error.value = ''
  copied.value = false
  resultId.value = null
}

const show = () => {
  resetForm()
  open.value = true
}

const close = () => {
  open.value = false
}

const submitFeedback = async () => {
  const title = form.value.title.trim()
  const message = form.value.message.trim()

  if (!title || !message) {
    error.value = '请填写问题标题和具体描述，方便我们更快定位。'
    return
  }

  if (message.length > MAX_MESSAGE_LENGTH) {
    error.value = `描述内容过长，请压缩到 ${MAX_MESSAGE_LENGTH} 字以内，优先保留复现步骤和错误提示。`
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const response = await feedbackAPI.create({
      title,
      message,
      email: form.value.email.trim() || undefined,
      category: form.value.category,
      severity: form.value.severity,
      page_url: window.location.href,
      diagnostic_code: diagnosticCode.value,
      diagnostics: currentDiagnostics(),
    })
    resultId.value = response.id
  } catch {
    error.value = '反馈暂时提交失败，请稍后重试。你也可以保留截图、页面地址和诊断码，稍后再提交。'
  } finally {
    submitting.value = false
  }
}

const copySummary = async () => {
  if (!feedbackSummary.value) return
  await navigator.clipboard?.writeText(feedbackSummary.value)
  copied.value = true
}
</script>

<template>
  <button
    v-if="!open"
    type="button"
    class="fixed bottom-5 right-5 z-[70] inline-flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/92 px-4 py-3 text-sm font-semibold text-slate-800 shadow-2xl shadow-violet-200/70 backdrop-blur transition hover:-translate-y-0.5 hover:border-violet-300 hover:text-violet-700 dark:border-violet-500/20 dark:bg-slate-900/92 dark:text-slate-100 dark:shadow-black/30 dark:hover:border-violet-400/40"
    @click="show"
  >
    <MessageSquare class="h-4 w-4 text-violet-500" />
    反馈问题
  </button>

  <div
    v-if="open"
    class="fixed inset-0 z-[80] flex items-end justify-center bg-slate-950/35 px-4 py-5 backdrop-blur-sm sm:items-center"
    @click.self="close"
  >
    <section class="w-full max-w-xl overflow-hidden rounded-[30px] border border-white/80 bg-white shadow-2xl shadow-slate-950/20 dark:border-slate-800 dark:bg-slate-950">
      <div class="flex items-start justify-between gap-4 border-b border-slate-200/80 bg-[linear-gradient(135deg,#faf5ff_0%,#eef2ff_100%)] p-5 dark:border-slate-800 dark:bg-[linear-gradient(135deg,rgba(76,29,149,0.28),rgba(15,23,42,0.96))]">
        <div>
          <div class="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-violet-700 dark:bg-violet-500/10 dark:text-violet-200">
            <Bug class="h-3.5 w-3.5" />
            使用反馈
          </div>
          <h2 class="mt-3 text-2xl font-bold text-slate-950 dark:text-white">
            遇到问题？告诉我们
          </h2>
          <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            系统会附带页面地址、浏览器信息和诊断码，帮助我们定位问题；不会收集你的文件内容。
          </p>
        </div>
        <button
          type="button"
          class="rounded-full p-2 text-slate-500 transition hover:bg-white/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
          aria-label="关闭反馈窗口"
          @click="close"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <div class="p-5">
        <div
          v-if="resultId"
          class="rounded-[24px] border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-100"
        >
          <CheckCircle2 class="h-8 w-8" />
          <h3 class="mt-3 text-lg font-semibold">反馈已提交</h3>
          <p class="mt-2 text-sm leading-6">
            我们已收到你的反馈。编号 <strong>#{{ resultId }}</strong>，诊断码 <strong>{{ diagnosticCode }}</strong>。如果后续需要补充信息，可以保留或复制这段编号。
          </p>
          <button
            type="button"
            class="mt-4 inline-flex items-center gap-2 rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500"
            @click="copySummary"
          >
            <ClipboardCopy class="h-4 w-4" />
            {{ copied ? '已复制' : '复制反馈编号' }}
          </button>
        </div>

        <form
          v-else
          class="space-y-4"
          @submit.prevent="submitFeedback"
        >
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="block">
              <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">类型</span>
              <select
                v-model="form.category"
                class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:focus:ring-violet-500/20"
              >
                <option value="bug">功能异常</option>
                <option value="ui">显示或排版问题</option>
                <option value="account">账号或登录问题</option>
                <option value="suggestion">使用建议</option>
              </select>
            </label>
            <label class="block">
              <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">影响程度</span>
              <select
                v-model="form.severity"
                class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:focus:ring-violet-500/20"
              >
                <option value="normal">一般问题</option>
                <option value="high">影响使用</option>
                <option value="critical">无法继续使用</option>
              </select>
            </label>
          </div>

          <label class="block">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">问题标题</span>
            <input
              v-model="form.title"
              type="text"
              maxlength="160"
              placeholder="例如：PDF 转图片本地处理失败"
              class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:focus:ring-violet-500/20"
            >
          </label>

          <label class="block">
            <span class="flex items-center justify-between gap-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
              <span>具体描述</span>
              <span
                class="text-xs font-medium"
                :class="messageRemaining < 0 ? 'text-rose-500' : messageRemaining < 300 ? 'text-amber-500' : 'text-slate-400'"
              >
                {{ messageLength }}/{{ MAX_MESSAGE_LENGTH }}
              </span>
            </span>
            <textarea
              v-model="form.message"
              rows="5"
              :maxlength="MAX_MESSAGE_LENGTH"
              placeholder="请写下你点击了什么、看到什么提示、是否可以复现。"
              class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:focus:ring-violet-500/20"
            />
            <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
              最多 {{ MAX_MESSAGE_LENGTH }} 字。建议优先写复现步骤、实际提示和期望结果，不需要粘贴文件内容。
            </p>
          </label>

          <label class="block">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">联系邮箱，可选</span>
            <input
              v-model="form.email"
              type="email"
              placeholder="方便需要补充信息时联系你"
              class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:focus:ring-violet-500/20"
            >
          </label>

          <div class="rounded-2xl bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-500 dark:bg-slate-900 dark:text-slate-400">
            诊断码：{{ diagnosticCode }} · 当前页面：{{ currentDiagnostics().path }}
          </div>

          <p
            v-if="error"
            class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-100"
          >
            {{ error }}
          </p>

          <button
            type="submit"
            class="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="submitting"
          >
            <Loader2
              v-if="submitting"
              class="h-4 w-4 animate-spin"
            />
            {{ submitting ? '提交中...' : '提交反馈' }}
          </button>
        </form>
      </div>
    </section>
  </div>
</template>
