<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  ClipboardList,
  EyeOff,
  FileText,
  Flag,
  Flame,
  GaugeCircle,
  Loader2,
  LockKeyhole,
  Save,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Trash2,
  UserCog,
} from 'lucide-vue-next'
import {
  adminAPI,
  type AdminAuditLog,
  type AdminApiError,
  type AdminDiagnostics,
  type AdminFeedback,
  type AdminJob,
  type AdminOperations,
  type AdminOverview,
  type AdminUser,
  type ContentBlock,
  type FeatureFlag,
  type SiteSetting,
} from '@/services/api'
import { useSiteConfigStore } from '@/stores/siteConfig'

type TabId = 'overview' | 'flags' | 'settings' | 'content' | 'users' | 'jobs' | 'feedback' | 'errors' | 'audit'

const siteConfigStore = useSiteConfigStore()
const loading = ref(true)
const savingKey = ref<string | null>(null)
const activeTab = ref<TabId>('overview')
const error = ref('')
const success = ref('')

const overview = ref<AdminOverview | null>(null)
const operations = ref<AdminOperations | null>(null)
const settings = ref<SiteSetting[]>([])
const flags = ref<FeatureFlag[]>([])
const contentBlocks = ref<ContentBlock[]>([])
const auditLogs = ref<AdminAuditLog[]>([])
const users = ref<AdminUser[]>([])
const jobs = ref<AdminJob[]>([])
const feedbackReports = ref<AdminFeedback[]>([])
const apiErrors = ref<AdminApiError[]>([])
const diagnostics = ref<AdminDiagnostics | null>(null)
const userSearch = ref('')
const jobStatusFilter = ref('')
const jobSearch = ref('')
const feedbackStatusFilter = ref('')

const tabs = [
  { id: 'overview' as const, label: '运营总览', icon: GaugeCircle },
  { id: 'flags' as const, label: '功能开关', icon: Flag },
  { id: 'settings' as const, label: '站点配置', icon: Settings2 },
  { id: 'content' as const, label: '内容块', icon: FileText },
  { id: 'users' as const, label: '用户管理', icon: UserCog },
  { id: 'jobs' as const, label: '任务观察', icon: GaugeCircle },
  { id: 'feedback' as const, label: '问题反馈', icon: ClipboardList },
  { id: 'errors' as const, label: '错误观察', icon: Flame },
  { id: 'audit' as const, label: '审计日志', icon: Activity },
]

const enabledFlagCount = computed(() => flags.value.filter((flag) => flag.enabled).length)
const lockedFlagCount = computed(() => flags.value.filter((flag) => flag.requires_login || flag.requires_pro).length)
const selectedContent = ref<ContentBlock | null>(null)
const filteredJobs = computed(() => {
  const keyword = jobSearch.value.trim().toLowerCase()
  if (!keyword) return jobs.value
  return jobs.value.filter((job) => [
    job.job_id,
    job.job_type,
    job.status,
    job.user_email || '',
    job.input_file_name,
    job.error_message || '',
  ].some((value) => value.toLowerCase().includes(keyword)))
})

const refreshAdminMeta = async () => {
  const [overviewData, operationsData, auditData] = await Promise.all([
    adminAPI.getOverview(),
    adminAPI.getOperations(),
    adminAPI.listAuditLogs(),
  ])
  overview.value = overviewData
  operations.value = operationsData
  auditLogs.value = auditData
}

const formatDate = (value: string) => new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium',
  timeStyle: 'short',
}).format(new Date(value))

const setMessage = (message: string) => {
  success.value = message
  window.setTimeout(() => {
    if (success.value === message) {
      success.value = ''
    }
  }, 2200)
}

const serviceTone = (status?: string) => {
  if (status === 'healthy') return 'border-emerald-300/20 bg-emerald-300/10 text-emerald-100'
  if (status === 'unhealthy') return 'border-rose-300/20 bg-rose-500/10 text-rose-100'
  if (status === 'degraded') return 'border-amber-300/20 bg-amber-300/10 text-amber-100'
  return 'border-slate-300/20 bg-white/10 text-slate-200'
}

const loadAdminData = async () => {
  loading.value = true
  error.value = ''

  try {
    const [overviewData, operationsData, settingsData, flagsData, contentData, usersData, jobsData, feedbackData, diagnosticsData, auditData] = await Promise.all([
      adminAPI.getOverview(),
      adminAPI.getOperations(),
      adminAPI.listSettings(),
      adminAPI.listFeatureFlags(),
      adminAPI.listContentBlocks(),
      adminAPI.listUsers(),
      adminAPI.listJobs(),
      adminAPI.listFeedback(),
      adminAPI.getDiagnostics(),
      adminAPI.listAuditLogs(),
    ])

    overview.value = overviewData
    operations.value = operationsData
    settings.value = settingsData
    flags.value = flagsData
    contentBlocks.value = contentData
    users.value = usersData
    jobs.value = jobsData
    feedbackReports.value = feedbackData
    diagnostics.value = diagnosticsData
    apiErrors.value = diagnosticsData.recent_errors
    auditLogs.value = auditData
    selectedContent.value = contentData[0] ?? null
  } catch (err: any) {
    error.value = err?.response?.status === 403
      ? '当前账号没有后台权限。'
      : '后台数据加载失败，请稍后重试或检查服务端日志。'
  } finally {
    loading.value = false
  }
}

const saveFlag = async (flag: FeatureFlag) => {
  savingKey.value = `flag:${flag.key}`
  error.value = ''

  try {
    const updated = await adminAPI.updateFeatureFlag(flag.key, {
      label: flag.label,
      description: flag.description,
      enabled: flag.enabled,
      requires_login: flag.requires_login,
      requires_pro: flag.requires_pro,
      maintenance_message: flag.maintenance_message,
    })
    const index = flags.value.findIndex((item) => item.key === updated.key)
    if (index >= 0) flags.value[index] = updated
    auditLogs.value = await adminAPI.listAuditLogs()
    await siteConfigStore.fetchPublicConfig(true)
    setMessage(`已保存：${updated.label}`)
  } catch {
    error.value = '功能开关保存失败，请检查输入或稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const saveSetting = async (setting: SiteSetting) => {
  savingKey.value = `setting:${setting.key}`
  error.value = ''

  try {
    const updated = await adminAPI.updateSetting(setting.key, {
      value: setting.value,
      value_type: setting.value_type,
      group: setting.group,
      label: setting.label,
      description: setting.description,
      is_public: setting.is_public,
    })
    const index = settings.value.findIndex((item) => item.key === updated.key)
    if (index >= 0) settings.value[index] = updated
    auditLogs.value = await adminAPI.listAuditLogs()
    await siteConfigStore.fetchPublicConfig(true)
    setMessage(`已保存：${updated.label}`)
  } catch {
    error.value = '站点配置保存失败，请检查输入或稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const saveContentBlock = async (block: ContentBlock) => {
  savingKey.value = `content:${block.key}:${block.locale}`
  error.value = ''

  try {
    const updated = await adminAPI.updateContentBlock(block.key, block.locale, {
      locale: block.locale,
      title: block.title,
      content: block.content,
      description: block.description,
      is_public: block.is_public,
    })
    const index = contentBlocks.value.findIndex(
      (item) => item.key === updated.key && item.locale === updated.locale
    )
    if (index >= 0) contentBlocks.value[index] = updated
    selectedContent.value = updated
    auditLogs.value = await adminAPI.listAuditLogs()
    await siteConfigStore.fetchPublicConfig(true)
    setMessage(`已保存：${updated.title}`)
  } catch {
    error.value = '内容块保存失败，请检查输入或稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const searchUsers = async () => {
  savingKey.value = 'users:search'
  error.value = ''

  try {
    users.value = await adminAPI.listUsers({
      search: userSearch.value.trim() || undefined,
    })
  } catch {
    error.value = '用户列表加载失败，请稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const saveUser = async (user: AdminUser) => {
  savingKey.value = `user:${user.id}`
  error.value = ''

  try {
    const updated = await adminAPI.updateUser(user.id, {
      role: user.role,
      is_active: user.is_active,
      is_verified: user.is_verified,
    })
    const index = users.value.findIndex((item) => item.id === updated.id)
    if (index >= 0) users.value[index] = updated
    await refreshAdminMeta()
    setMessage(`已更新用户：${updated.email}`)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || '用户更新失败，请确认权限和输入后重试。'
    users.value = await adminAPI.listUsers({
      search: userSearch.value.trim() || undefined,
    })
  } finally {
    savingKey.value = null
  }
}

const toggleUserBan = async (user: AdminUser) => {
  const nextActive = !user.is_active
  savingKey.value = `ban:${user.id}`
  error.value = ''

  try {
    const updated = await adminAPI.updateUser(user.id, {
      is_active: nextActive,
    })
    const index = users.value.findIndex((item) => item.id === updated.id)
    if (index >= 0) users.value[index] = updated
    await refreshAdminMeta()
    setMessage(nextActive ? `已解封用户：${updated.email}` : `已封禁用户：${updated.email}`)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || '账号状态更新失败，请稍后重试。'
    await searchUsers()
  } finally {
    savingKey.value = null
  }
}

const deleteUser = async (user: AdminUser) => {
  const confirmed = window.confirm(`确认删除 ${user.email}？此操作会移除该账号及其关联数据，不能直接撤销。`)
  if (!confirmed) return

  savingKey.value = `delete:${user.id}`
  error.value = ''

  try {
    await adminAPI.deleteUser(user.id)
    users.value = users.value.filter((item) => item.id !== user.id)
    await refreshAdminMeta()
    setMessage(`已删除用户：${user.email}`)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || '删除用户失败，请确认不是当前管理员账号。'
  } finally {
    savingKey.value = null
  }
}

const loadJobs = async () => {
  savingKey.value = 'jobs:refresh'
  error.value = ''

  try {
    jobs.value = await adminAPI.listJobs({
      status_filter: jobStatusFilter.value || undefined,
    })
    operations.value = await adminAPI.getOperations()
  } catch {
    error.value = '任务列表加载失败，请稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const loadFeedback = async () => {
  savingKey.value = 'feedback:refresh'
  error.value = ''

  try {
    feedbackReports.value = await adminAPI.listFeedback({
      status_filter: feedbackStatusFilter.value || undefined,
    })
    overview.value = await adminAPI.getOverview()
  } catch {
    error.value = '问题反馈加载失败，请稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const saveFeedback = async (report: AdminFeedback) => {
  savingKey.value = `feedback:${report.id}`
  error.value = ''

  try {
    const updated = await adminAPI.updateFeedback(report.id, {
      status: report.status,
      admin_note: report.admin_note,
    })
    const index = feedbackReports.value.findIndex((item) => item.id === updated.id)
    if (index >= 0) feedbackReports.value[index] = updated
    auditLogs.value = await adminAPI.listAuditLogs()
    overview.value = await adminAPI.getOverview()
    setMessage(`已更新反馈 #${updated.id}`)
  } catch {
    error.value = '反馈状态保存失败，请稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const loadDiagnostics = async () => {
  savingKey.value = 'errors:refresh'
  error.value = ''

  try {
    const data = await adminAPI.getDiagnostics()
    diagnostics.value = data
    apiErrors.value = data.recent_errors
    overview.value = await adminAPI.getOverview()
  } catch {
    error.value = '错误观察数据加载失败，请稍后重试。'
  } finally {
    savingKey.value = null
  }
}

const formatBytes = (value: number) => {
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

onMounted(loadAdminData)
</script>

<template>
  <div class="min-h-screen overflow-hidden bg-[#09111f] text-white">
    <div class="pointer-events-none fixed inset-0">
      <div class="absolute left-[-10%] top-[-12%] h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
      <div class="absolute right-[-8%] top-24 h-[28rem] w-[28rem] rounded-full bg-emerald-400/10 blur-3xl" />
      <div class="absolute bottom-[-20%] left-[35%] h-[26rem] w-[26rem] rounded-full bg-blue-500/10 blur-3xl" />
    </div>

    <main class="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section class="rounded-[34px] border border-white/10 bg-white/[0.06] p-6 shadow-2xl shadow-black/30 backdrop-blur-xl sm:p-8">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-100">
              <EyeOff class="h-4 w-4" />
              Hidden Operations
            </div>
            <h1 class="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
              PDF-Flow Control Room
            </h1>
            <p class="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              这是隐藏后台的第一阶段。这里不会出现在普通用户导航里，但真正的保护来自后端 ADMIN 权限、接口鉴权和审计日志。
            </p>
          </div>

          <div class="grid grid-cols-2 gap-3 text-center sm:grid-cols-6">
            <div class="rounded-3xl border border-white/10 bg-white/[0.07] p-4">
              <p class="text-2xl font-semibold">{{ enabledFlagCount }}</p>
              <p class="mt-1 text-xs text-slate-400">已开启</p>
            </div>
            <div class="rounded-3xl border border-white/10 bg-white/[0.07] p-4">
              <p class="text-2xl font-semibold">{{ lockedFlagCount }}</p>
              <p class="mt-1 text-xs text-slate-400">受限功能</p>
            </div>
            <div class="rounded-3xl border border-white/10 bg-white/[0.07] p-4">
              <p class="text-2xl font-semibold">{{ overview?.content_blocks_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-400">内容块</p>
            </div>
            <div class="rounded-3xl border border-white/10 bg-white/[0.07] p-4">
              <p class="text-2xl font-semibold">{{ overview?.active_users_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-400">活跃用户</p>
            </div>
            <div class="rounded-3xl border border-white/10 bg-white/[0.07] p-4">
              <p class="text-2xl font-semibold">{{ overview?.failed_jobs_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-400">失败任务</p>
            </div>
            <div class="rounded-3xl border border-white/10 bg-white/[0.07] p-4">
              <p class="text-2xl font-semibold">{{ overview?.open_feedback_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-400">待处理反馈</p>
            </div>
          </div>
        </div>
      </section>

      <div v-if="error" class="mt-6 rounded-3xl border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
        <div class="flex items-start gap-3">
          <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" />
          <span>{{ error }}</span>
        </div>
      </div>

      <div v-if="success" class="mt-6 rounded-3xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
        <div class="flex items-start gap-3">
          <CheckCircle2 class="mt-0.5 h-5 w-5 shrink-0" />
          <span>{{ success }}</span>
        </div>
      </div>

      <div v-if="loading" class="mt-10 flex items-center justify-center rounded-[34px] border border-white/10 bg-white/[0.05] p-16">
        <Loader2 class="h-8 w-8 animate-spin text-cyan-200" />
      </div>

      <section v-else class="mt-8 grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside class="rounded-[30px] border border-white/10 bg-white/[0.06] p-3 backdrop-blur-xl">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition"
            :class="activeTab === tab.id ? 'bg-cyan-300 text-slate-950 shadow-lg shadow-cyan-950/20' : 'text-slate-300 hover:bg-white/[0.08] hover:text-white'"
            @click="activeTab = tab.id"
          >
            <component :is="tab.icon" class="h-4 w-4" />
            <span class="font-semibold">{{ tab.label }}</span>
          </button>
        </aside>

        <div class="min-w-0">
          <div v-if="activeTab === 'overview'" class="space-y-5">
            <section class="grid gap-4 xl:grid-cols-4">
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <p class="text-sm text-slate-400">全部用户</p>
                <p class="mt-3 text-3xl font-semibold">{{ operations?.total_users ?? overview?.users_count ?? 0 }}</p>
                <p class="mt-2 text-xs text-slate-500">测试账号 {{ operations?.test_users ?? 0 }} 个</p>
              </article>
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <p class="text-sm text-slate-400">可登录用户</p>
                <p class="mt-3 text-3xl font-semibold">{{ operations?.active_users ?? overview?.active_users_count ?? 0 }}</p>
                <p class="mt-2 text-xs text-slate-500">封禁 {{ operations?.banned_users ?? 0 }} 个</p>
              </article>
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <p class="text-sm text-slate-400">近期可见任务</p>
                <p class="mt-3 text-3xl font-semibold">{{ operations?.visible_jobs ?? jobs.length }}</p>
                <p class="mt-2 text-xs text-slate-500">处理中 {{ operations?.running_jobs ?? 0 }} 个</p>
              </article>
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <p class="text-sm text-slate-400">失败任务</p>
                <p class="mt-3 text-3xl font-semibold text-rose-100">{{ operations?.failed_jobs ?? overview?.failed_jobs_count ?? 0 }}</p>
                <p class="mt-2 text-xs text-slate-500">优先排查最近错误</p>
              </article>
            </section>

            <section class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <div class="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p class="text-lg font-semibold">服务状态</p>
                    <p class="mt-1 text-sm text-slate-400">数据库、Redis 和任务队列线索。</p>
                  </div>
                  <button
                    type="button"
                    class="rounded-2xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200"
                    @click="loadAdminData"
                  >
                    刷新
                  </button>
                </div>
                <div class="space-y-3">
                  <div
                    v-for="(service, name) in operations?.services"
                    :key="name"
                    class="rounded-2xl border p-4"
                    :class="serviceTone(service.status)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div class="flex items-center gap-2">
                        <CircleDot class="h-4 w-4" />
                        <span class="font-semibold">{{ name }}</span>
                      </div>
                      <span class="text-xs uppercase tracking-[0.18em]">{{ service.status }}</span>
                    </div>
                    <p class="mt-2 text-sm opacity-80">{{ service.detail }}</p>
                  </div>
                </div>
              </article>

              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <div class="mb-4 flex items-center justify-between">
                  <div>
                    <p class="text-lg font-semibold">最近失败任务</p>
                    <p class="mt-1 text-sm text-slate-400">这里有内容时，优先看错误摘要和 job_id。</p>
                  </div>
                </div>
                <div class="space-y-3">
                  <div
                    v-for="job in operations?.recent_failed_jobs"
                    :key="job.job_id"
                    class="rounded-2xl border border-rose-300/20 bg-rose-500/10 p-4"
                  >
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="rounded-full bg-rose-300/15 px-3 py-1 text-xs font-semibold text-rose-100">{{ job.job_type }}</span>
                      <span class="text-xs text-rose-100/70">{{ formatDate(job.created_at) }}</span>
                    </div>
                    <p class="mt-2 break-all font-semibold text-white">{{ job.job_id }}</p>
                    <p class="mt-2 text-sm text-rose-100">{{ job.error_message || '暂无错误摘要' }}</p>
                  </div>
                  <div v-if="!operations?.recent_failed_jobs?.length" class="rounded-2xl border border-white/10 bg-black/20 p-6 text-center text-sm text-slate-400">
                    最近没有失败任务，状态不错。
                  </div>
                </div>
              </article>
            </section>

            <section class="grid gap-5 xl:grid-cols-2">
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <p class="text-lg font-semibold">最近注册用户</p>
                <div class="mt-4 space-y-3">
                  <div
                    v-for="user in operations?.recent_users"
                    :key="user.id"
                    class="flex items-center justify-between gap-3 rounded-2xl bg-black/20 p-3"
                  >
                    <div>
                      <p class="font-semibold text-white">{{ user.email }}</p>
                      <p class="mt-1 text-xs text-slate-500">{{ user.role }} · {{ user.is_test_account ? '测试账号' : '真实用户' }}</p>
                    </div>
                    <span
                      class="rounded-full px-3 py-1 text-xs font-semibold"
                      :class="user.is_active ? 'bg-emerald-400/15 text-emerald-100' : 'bg-rose-400/15 text-rose-100'"
                    >
                      {{ user.is_active ? '正常' : '已封禁' }}
                    </span>
                  </div>
                </div>
              </article>

              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <p class="text-lg font-semibold">最近任务</p>
                <div class="mt-4 space-y-3">
                  <div
                    v-for="job in operations?.recent_jobs"
                    :key="job.job_id"
                    class="rounded-2xl bg-black/20 p-3"
                  >
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <span class="font-semibold text-white">{{ job.job_type }}</span>
                      <span
                        class="rounded-full px-3 py-1 text-xs font-semibold"
                        :class="job.status === 'failed' ? 'bg-rose-400/15 text-rose-100' : job.status === 'completed' ? 'bg-emerald-400/15 text-emerald-100' : 'bg-amber-300/15 text-amber-100'"
                      >
                        {{ job.status }}
                      </span>
                    </div>
                    <p class="mt-2 break-all text-xs text-slate-500">{{ job.job_id }}</p>
                  </div>
                  <div v-if="!operations?.recent_jobs?.length" class="rounded-2xl border border-white/10 bg-black/20 p-6 text-center text-sm text-slate-400">
                    暂无近期任务。
                  </div>
                </div>
              </article>
            </section>
          </div>

          <div v-else-if="activeTab === 'flags'" class="grid gap-4 xl:grid-cols-2">
            <article
              v-for="flag in flags"
              :key="flag.key"
              class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-lg font-semibold">{{ flag.label }}</p>
                  <p class="mt-1 text-xs uppercase tracking-[0.2em] text-cyan-200/70">{{ flag.key }}</p>
                  <p class="mt-3 text-sm leading-6 text-slate-300">{{ flag.description }}</p>
                </div>
                <label class="relative inline-flex cursor-pointer items-center">
                  <input v-model="flag.enabled" type="checkbox" class="peer sr-only" />
                  <span class="h-7 w-12 rounded-full bg-slate-700 transition peer-checked:bg-emerald-400" />
                  <span class="absolute left-1 h-5 w-5 rounded-full bg-white transition peer-checked:translate-x-5" />
                </label>
              </div>

              <div class="mt-5 grid gap-3 sm:grid-cols-2">
                <label class="flex items-center gap-2 rounded-2xl bg-black/20 px-3 py-2 text-sm text-slate-200">
                  <input v-model="flag.requires_login" type="checkbox" class="rounded border-white/20 bg-slate-900 text-cyan-300" />
                  需要登录
                </label>
                <label class="flex items-center gap-2 rounded-2xl bg-black/20 px-3 py-2 text-sm text-slate-200">
                  <input v-model="flag.requires_pro" type="checkbox" class="rounded border-white/20 bg-slate-900 text-cyan-300" />
                  需要 Pro
                </label>
              </div>

              <textarea
                v-model="flag.maintenance_message"
                rows="2"
                placeholder="维护提示，留空则使用默认提示"
                class="mt-4 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
              />

              <button
                type="button"
                class="mt-4 inline-flex items-center gap-2 rounded-2xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="savingKey === `flag:${flag.key}`"
                @click="saveFlag(flag)"
              >
                <Loader2 v-if="savingKey === `flag:${flag.key}`" class="h-4 w-4 animate-spin" />
                <Save v-else class="h-4 w-4" />
                保存开关
              </button>
            </article>
          </div>

          <div v-else-if="activeTab === 'settings'" class="grid gap-4">
            <article
              v-for="setting in settings"
              :key="setting.key"
              class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl"
            >
              <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p class="text-lg font-semibold">{{ setting.label }}</p>
                  <p class="mt-1 text-xs uppercase tracking-[0.2em] text-cyan-200/70">{{ setting.group }} / {{ setting.key }}</p>
                  <p class="mt-3 text-sm leading-6 text-slate-300">{{ setting.description }}</p>
                </div>
                <label class="flex items-center gap-2 text-sm text-slate-300">
                  <input v-model="setting.is_public" type="checkbox" class="rounded border-white/20 bg-slate-900 text-cyan-300" />
                  可公开读取
                </label>
              </div>

              <textarea
                v-if="setting.value_type === 'textarea'"
                v-model="setting.value"
                rows="4"
                class="mt-4 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300/60"
              />
              <input
                v-else
                v-model="setting.value"
                type="text"
                class="mt-4 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300/60"
              />

              <button
                type="button"
                class="mt-4 inline-flex items-center gap-2 rounded-2xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="savingKey === `setting:${setting.key}`"
                @click="saveSetting(setting)"
              >
                <Loader2 v-if="savingKey === `setting:${setting.key}`" class="h-4 w-4 animate-spin" />
                <Save v-else class="h-4 w-4" />
                保存配置
              </button>
            </article>
          </div>

          <div v-else-if="activeTab === 'content'" class="grid gap-5 xl:grid-cols-[280px_1fr]">
            <aside class="rounded-[28px] border border-white/10 bg-white/[0.07] p-3">
              <button
                v-for="block in contentBlocks"
                :key="`${block.key}:${block.locale}`"
                type="button"
                class="mb-2 w-full rounded-2xl px-4 py-3 text-left text-sm transition"
                :class="selectedContent?.id === block.id ? 'bg-emerald-300 text-slate-950' : 'text-slate-300 hover:bg-white/[0.08]'"
                @click="selectedContent = block"
              >
                <span class="block font-semibold">{{ block.title }}</span>
                <span class="mt-1 block text-xs opacity-70">{{ block.key }} / {{ block.locale }}</span>
              </button>
            </aside>

            <article v-if="selectedContent" class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5">
              <div class="grid gap-4 sm:grid-cols-2">
                <label class="text-sm text-slate-300">
                  标题
                  <input
                    v-model="selectedContent.title"
                    type="text"
                    class="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-emerald-300/60"
                  />
                </label>
                <label class="text-sm text-slate-300">
                  语言
                  <input
                    v-model="selectedContent.locale"
                    type="text"
                    class="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-emerald-300/60"
                  />
                </label>
              </div>
              <label class="mt-4 block text-sm text-slate-300">
                描述
                <input
                  v-model="selectedContent.description"
                  type="text"
                  class="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none focus:border-emerald-300/60"
                />
              </label>
              <label class="mt-4 block text-sm text-slate-300">
                正文内容
                <textarea
                  v-model="selectedContent.content"
                  rows="12"
                  class="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm leading-7 text-white outline-none focus:border-emerald-300/60"
                />
              </label>
              <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
                <label class="flex items-center gap-2 text-sm text-slate-300">
                  <input v-model="selectedContent.is_public" type="checkbox" class="rounded border-white/20 bg-slate-900 text-emerald-300" />
                  可公开读取
                </label>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-2xl bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="savingKey === `content:${selectedContent.key}:${selectedContent.locale}`"
                  @click="saveContentBlock(selectedContent)"
                >
                  <Loader2 v-if="savingKey === `content:${selectedContent.key}:${selectedContent.locale}`" class="h-4 w-4 animate-spin" />
                  <Save v-else class="h-4 w-4" />
                  保存内容
                </button>
              </div>
            </article>
          </div>

          <div v-else-if="activeTab === 'users'" class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-xl font-semibold">用户管理</p>
                <p class="mt-2 text-sm leading-6 text-slate-400">
                  Smoke 测试会自动创建 `smoke-*`、`ocr-*`、`office-*` 账号，这些会标记为测试账号。封禁会阻止登录，删除会移除账号数据；当前管理员不能封禁、降级或删除自己。
                </p>
              </div>
              <div class="flex flex-col gap-2 sm:flex-row">
                <input
                  v-model="userSearch"
                  type="search"
                  placeholder="搜索邮箱或姓名"
                  class="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
                  @keyup.enter="searchUsers"
                />
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="savingKey === 'users:search'"
                  @click="searchUsers"
                >
                  <Loader2 v-if="savingKey === 'users:search'" class="h-4 w-4 animate-spin" />
                  搜索
                </button>
              </div>
            </div>

            <div class="mt-5 overflow-hidden rounded-3xl border border-white/10">
              <div class="hidden grid-cols-[1.5fr_0.8fr_0.9fr_1.2fr] gap-3 bg-white/[0.08] px-4 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 lg:grid">
                <span>用户</span>
                <span>角色</span>
                <span>状态</span>
                <span>操作</span>
              </div>
              <div
                v-for="user in users"
                :key="user.id"
                class="grid gap-4 border-t border-white/10 px-4 py-4 lg:grid-cols-[1.5fr_0.8fr_0.9fr_1.2fr] lg:items-center"
              >
                <div>
                  <div class="flex flex-wrap items-center gap-2">
                    <p class="font-semibold text-white">{{ user.email }}</p>
                    <span
                      v-if="user.is_test_account"
                      class="rounded-full border border-amber-300/20 bg-amber-300/10 px-2.5 py-1 text-[11px] font-semibold text-amber-100"
                    >
                      测试账号
                    </span>
                  </div>
                  <p class="mt-1 text-sm text-slate-400">{{ user.full_name || '未填写姓名' }}</p>
                  <p class="mt-1 text-xs text-slate-500">
                    注册：{{ formatDate(user.created_at) }} · 邮箱状态：{{ user.is_verified ? '已验证' : '未验证' }}
                  </p>
                </div>
                <select
                  v-model="user.role"
                  class="rounded-2xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-300/60"
                >
                  <option value="free">Free</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                  <option value="admin">Admin</option>
                </select>
                <div>
                  <span
                    class="inline-flex rounded-full px-3 py-1 text-xs font-semibold"
                    :class="user.is_active ? 'bg-emerald-400/15 text-emerald-100' : 'bg-rose-400/15 text-rose-100'"
                  >
                    {{ user.is_active ? '正常' : '已封禁' }}
                  </span>
                  <p class="mt-2 text-xs leading-5 text-slate-500">
                    {{ user.last_login_at ? `最后登录：${formatDate(user.last_login_at)}` : '尚无登录记录' }}
                  </p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="savingKey === `user:${user.id}`"
                    @click="saveUser(user)"
                  >
                    <Loader2 v-if="savingKey === `user:${user.id}`" class="h-4 w-4 animate-spin" />
                    <Save v-else class="h-4 w-4" />
                    保存角色
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60"
                    :class="user.is_active ? 'border-amber-300/20 bg-amber-300/10 text-amber-100 hover:bg-amber-300/20' : 'border-emerald-300/20 bg-emerald-300/10 text-emerald-100 hover:bg-emerald-300/20'"
                    :disabled="savingKey === `ban:${user.id}`"
                    @click="toggleUserBan(user)"
                  >
                    <Loader2 v-if="savingKey === `ban:${user.id}`" class="h-4 w-4 animate-spin" />
                    {{ user.is_active ? '封禁' : '解封' }}
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-300/20 bg-rose-500/10 px-4 py-2 text-sm font-semibold text-rose-100 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="savingKey === `delete:${user.id}`"
                    @click="deleteUser(user)"
                  >
                    <Loader2 v-if="savingKey === `delete:${user.id}`" class="h-4 w-4 animate-spin" />
                    <Trash2 v-else class="h-4 w-4" />
                    删除
                  </button>
                </div>
              </div>
              <div v-if="users.length === 0" class="border-t border-white/10 px-4 py-10 text-center text-sm text-slate-400">
                没有找到匹配用户。
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'jobs'" class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-xl font-semibold">任务观察</p>
                <p class="mt-2 text-sm leading-6 text-slate-400">
                  快速查看最近云端处理任务，优先定位失败、卡住或异常耗时的用户操作。这里会合并显示最近 1 小时 Redis 队列状态和数据库任务记录。
                </p>
              </div>
              <div class="flex flex-col gap-2 sm:flex-row">
                <input
                  v-model="jobSearch"
                  type="search"
                  placeholder="搜索 job_id / 用户 / 类型 / 错误"
                  class="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
                />
                <select
                  v-model="jobStatusFilter"
                  class="rounded-2xl border border-white/10 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300/60"
                >
                  <option value="">全部状态</option>
                  <option value="pending">Pending</option>
                  <option value="processing">Processing</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="savingKey === 'jobs:refresh'"
                  @click="loadJobs"
                >
                  <Loader2 v-if="savingKey === 'jobs:refresh'" class="h-4 w-4 animate-spin" />
                  刷新
                </button>
              </div>
            </div>

            <div class="mt-5 space-y-3">
              <article
                v-for="job in filteredJobs"
                :key="job.job_id"
                class="rounded-3xl border border-white/10 bg-black/20 p-4"
              >
                <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="rounded-full bg-cyan-300/15 px-3 py-1 text-xs font-semibold text-cyan-100">{{ job.job_type }}</span>
                      <span
                        class="rounded-full px-3 py-1 text-xs font-semibold"
                        :class="job.status === 'failed' ? 'bg-rose-400/15 text-rose-100' : job.status === 'completed' ? 'bg-emerald-400/15 text-emerald-100' : 'bg-amber-300/15 text-amber-100'"
                      >
                        {{ job.status }}
                      </span>
                    </div>
                    <p class="mt-3 font-semibold text-white">{{ job.input_file_name }}</p>
                    <p class="mt-1 break-all text-sm text-slate-400">{{ job.job_id }}</p>
                    <p class="mt-2 text-sm text-slate-400">
                      用户：{{ job.user_email || (job.user_id ? `#${job.user_id}` : '未记录') }} · 大小：{{ formatBytes(job.input_file_size) }} · 创建：{{ formatDate(job.created_at) }}
                    </p>
                    <p v-if="job.error_message" class="mt-3 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
                      {{ job.error_message }}
                    </p>
                  </div>
                  <div class="min-w-[180px]">
                    <div class="flex items-center justify-between text-xs text-slate-400">
                      <span>进度</span>
                      <span>{{ job.progress }}%</span>
                    </div>
                    <div class="mt-2 h-2 rounded-full bg-white/10">
                      <div class="h-2 rounded-full bg-cyan-300" :style="{ width: `${job.progress}%` }" />
                    </div>
                  </div>
                </div>
              </article>
              <div v-if="filteredJobs.length === 0" class="rounded-3xl border border-white/10 bg-black/20 px-4 py-10 text-center text-sm text-slate-400">
                当前没有匹配任务。运行一次业务、OCR 或 Office smoke test 后，再点刷新；如果已刷新仍为空，说明最近 1 小时 Redis 状态和数据库任务里都没有匹配记录。
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'feedback'" class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-xl font-semibold">问题反馈</p>
                <p class="mt-2 text-sm leading-6 text-slate-400">
                  收集真实用户在页面右下角提交的问题，包含页面地址、诊断码、浏览器信息和用户描述，方便上线测试时快速复现。
                </p>
              </div>
              <div class="flex flex-col gap-2 sm:flex-row">
                <select
                  v-model="feedbackStatusFilter"
                  class="rounded-2xl border border-white/10 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-300/60"
                >
                  <option value="">全部状态</option>
                  <option value="new">New</option>
                  <option value="reviewing">Reviewing</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="savingKey === 'feedback:refresh'"
                  @click="loadFeedback"
                >
                  <Loader2 v-if="savingKey === 'feedback:refresh'" class="h-4 w-4 animate-spin" />
                  刷新
                </button>
              </div>
            </div>

            <div class="mt-5 space-y-4">
              <article
                v-for="report in feedbackReports"
                :key="report.id"
                class="rounded-3xl border border-white/10 bg-black/20 p-4"
              >
                <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="rounded-full bg-cyan-300/15 px-3 py-1 text-xs font-semibold text-cyan-100">#{{ report.id }}</span>
                      <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-200">{{ report.category }}</span>
                      <span
                        class="rounded-full px-3 py-1 text-xs font-semibold"
                        :class="report.severity === 'critical' ? 'bg-rose-400/15 text-rose-100' : report.severity === 'high' ? 'bg-amber-300/15 text-amber-100' : 'bg-emerald-400/15 text-emerald-100'"
                      >
                        {{ report.severity }}
                      </span>
                    </div>
                    <p class="mt-3 text-lg font-semibold text-white">{{ report.title }}</p>
                    <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-300">{{ report.message }}</p>
                    <div class="mt-3 space-y-1 text-xs leading-5 text-slate-500">
                      <p>提交：{{ formatDate(report.created_at) }} · 联系：{{ report.email || '未提供' }}</p>
                      <p v-if="report.page_url" class="break-all">页面：{{ report.page_url }}</p>
                      <p v-if="report.diagnostic_code">诊断码：{{ report.diagnostic_code }}</p>
                      <p v-if="report.user_agent" class="break-all">浏览器：{{ report.user_agent }}</p>
                      <p v-if="report.diagnostics" class="break-all">诊断信息：{{ report.diagnostics }}</p>
                    </div>
                  </div>

                  <div class="w-full space-y-3 xl:w-72">
                    <select
                      v-model="report.status"
                      class="w-full rounded-2xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-300/60"
                    >
                      <option value="new">New</option>
                      <option value="reviewing">Reviewing</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </select>
                    <textarea
                      v-model="report.admin_note"
                      rows="4"
                      placeholder="内部备注，例如：已复现 / 等截图 / 已修复待上线"
                      class="w-full rounded-2xl border border-white/10 bg-slate-950 px-3 py-2 text-sm leading-6 text-white outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
                    />
                    <button
                      type="button"
                      class="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-60"
                      :disabled="savingKey === `feedback:${report.id}`"
                      @click="saveFeedback(report)"
                    >
                      <Loader2 v-if="savingKey === `feedback:${report.id}`" class="h-4 w-4 animate-spin" />
                      <Save v-else class="h-4 w-4" />
                      保存反馈状态
                    </button>
                  </div>
                </div>
              </article>
              <div v-if="feedbackReports.length === 0" class="rounded-3xl border border-white/10 bg-black/20 px-4 py-10 text-center text-sm text-slate-400">
                当前没有匹配的问题反馈。用户可通过页面右下角“反馈问题”提交。
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'errors'" class="space-y-5">
            <section class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
              <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p class="text-xl font-semibold">错误观察</p>
                  <p class="mt-2 text-sm leading-6 text-slate-400">
                    把最近 API 500 错误、失败任务和用户反馈放在一起看。这里不会记录请求体或文件内容，只保留排查所需的摘要信息。
                  </p>
                </div>
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="savingKey === 'errors:refresh'"
                  @click="loadDiagnostics"
                >
                  <Loader2 v-if="savingKey === 'errors:refresh'" class="h-4 w-4 animate-spin" />
                  刷新诊断
                </button>
              </div>

              <div class="mt-5 grid gap-4 md:grid-cols-3">
                <div class="rounded-3xl border border-rose-300/20 bg-rose-500/10 p-4">
                  <p class="text-sm text-rose-100/70">API 错误</p>
                  <p class="mt-2 text-3xl font-semibold text-rose-50">{{ diagnostics?.api_error_count ?? 0 }}</p>
                </div>
                <div class="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-4">
                  <p class="text-sm text-amber-100/70">失败任务</p>
                  <p class="mt-2 text-3xl font-semibold text-amber-50">{{ diagnostics?.failed_jobs_count ?? operations?.failed_jobs ?? 0 }}</p>
                </div>
                <div class="rounded-3xl border border-cyan-300/20 bg-cyan-300/10 p-4">
                  <p class="text-sm text-cyan-100/70">待处理反馈</p>
                  <p class="mt-2 text-3xl font-semibold text-cyan-50">{{ diagnostics?.open_feedback_count ?? overview?.open_feedback_count ?? 0 }}</p>
                </div>
              </div>
            </section>

            <section class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
              <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                <div class="mb-4 flex items-center gap-3">
                  <Flame class="h-5 w-5 text-rose-200" />
                  <div>
                    <p class="font-semibold">最近 API 错误</p>
                    <p class="text-sm text-slate-400">优先看路径、状态码、错误类型和时间。</p>
                  </div>
                </div>
                <div class="space-y-3">
                  <div
                    v-for="item in apiErrors"
                    :key="item.id"
                    class="rounded-3xl border border-rose-300/20 bg-black/20 p-4"
                  >
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="rounded-full bg-rose-400/15 px-3 py-1 text-xs font-semibold text-rose-100">{{ item.status_code }}</span>
                      <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-200">{{ item.method }}</span>
                      <span class="text-xs text-slate-500">{{ formatDate(item.created_at) }}</span>
                    </div>
                    <p class="mt-3 break-all font-semibold text-white">{{ item.path }}</p>
                    <p v-if="item.error_type || item.error_message" class="mt-2 whitespace-pre-wrap text-sm leading-6 text-rose-100">
                      {{ item.error_type || 'Error' }}：{{ item.error_message || item.traceback_summary || '无错误摘要' }}
                    </p>
                    <p class="mt-2 break-all text-xs text-slate-500">
                      Request ID: {{ item.request_id || '未记录' }} · IP: {{ item.ip_address || '未知' }}
                    </p>
                  </div>
                  <div v-if="apiErrors.length === 0" class="rounded-3xl border border-white/10 bg-black/20 px-4 py-10 text-center text-sm text-slate-400">
                    目前没有记录到 API 500 级错误。
                  </div>
                </div>
              </article>

              <div class="space-y-5">
                <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                  <p class="font-semibold">最近失败任务</p>
                  <div class="mt-4 space-y-3">
                    <div
                      v-for="job in diagnostics?.recent_failed_jobs || []"
                      :key="job.job_id"
                      class="rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4"
                    >
                      <p class="font-semibold text-white">{{ job.job_type }}</p>
                      <p class="mt-1 break-all text-xs text-slate-400">{{ job.job_id }}</p>
                      <p class="mt-2 text-sm text-amber-100">{{ job.error_message || '暂无错误摘要' }}</p>
                    </div>
                    <div v-if="!diagnostics?.recent_failed_jobs?.length" class="rounded-2xl border border-white/10 bg-black/20 p-6 text-center text-sm text-slate-400">
                      最近没有失败任务。
                    </div>
                  </div>
                </article>

                <article class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
                  <p class="font-semibold">待处理反馈</p>
                  <div class="mt-4 space-y-3">
                    <div
                      v-for="item in diagnostics?.recent_feedback || []"
                      :key="item.id"
                      class="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-4"
                    >
                      <div class="flex flex-wrap items-center gap-2">
                        <span class="rounded-full bg-cyan-300/15 px-2.5 py-1 text-xs font-semibold text-cyan-100">#{{ item.id }}</span>
                        <span class="rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold text-slate-200">{{ item.status }}</span>
                      </div>
                      <p class="mt-2 font-semibold text-white">{{ item.title }}</p>
                      <p v-if="item.page_url" class="mt-1 break-all text-xs text-slate-400">{{ item.page_url }}</p>
                    </div>
                    <div v-if="!diagnostics?.recent_feedback?.length" class="rounded-2xl border border-white/10 bg-black/20 p-6 text-center text-sm text-slate-400">
                      没有待处理反馈。
                    </div>
                  </div>
                </article>
              </div>
            </section>
          </div>

          <div v-else class="rounded-[28px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-xl">
            <div class="mb-5 flex items-center gap-3">
              <ShieldCheck class="h-5 w-5 text-cyan-200" />
              <div>
                <p class="font-semibold">最近管理员操作</p>
                <p class="text-sm text-slate-400">只展示最近 50 条，完整留存由后端审计表负责。</p>
              </div>
            </div>

            <div class="space-y-3">
              <div
                v-for="log in auditLogs"
                :key="log.id"
                class="flex flex-col gap-2 rounded-2xl border border-white/10 bg-black/20 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p class="font-medium">{{ log.action }} {{ log.target_type }}</p>
                  <p class="mt-1 text-sm text-slate-400">{{ log.target_key }}</p>
                </div>
                <div class="flex items-center gap-3 text-sm text-slate-400">
                  <LockKeyhole class="h-4 w-4" />
                  <span>{{ formatDate(log.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="mt-8 rounded-[28px] border border-amber-300/20 bg-amber-300/10 p-5 text-sm leading-7 text-amber-50">
        <div class="flex items-start gap-3">
          <SlidersHorizontal class="mt-1 h-5 w-5 shrink-0" />
          <p>
            当前阶段已经能通过后台维护配置、功能开关和内容块。下一阶段需要把公开页面和工具页统一接入这些后端开关，让“关闭功能 / 维护提示 / 登录要求 / Pro 要求”真正影响用户界面和 API 行为。
          </p>
        </div>
      </section>
    </main>
  </div>
</template>
