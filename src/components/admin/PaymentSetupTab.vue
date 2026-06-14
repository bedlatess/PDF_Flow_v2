<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCopy,
  Copy,
  FileCog,
  KeyRound,
  RefreshCw,
  Save,
  ShieldCheck,
  TestTube2,
} from 'lucide-vue-next'
import {
  adminAPI,
  type AdminPaymentProviderConfig,
  type AdminPaymentProviderConfigValidation,
  type AdminPaymentProviderHealth,
  type AdminPaymentSummary,
} from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  paymentSummary: AdminPaymentSummary | null
  evidenceCopied: boolean
  savingKey: string | null
}>()

const emit = defineEmits<{
  refresh: []
  copyEvidence: []
}>()

const copiedEndpointKey = ref<string | null>(null)
const paymentConfigs = ref<AdminPaymentProviderConfig[]>([])
const configsLoading = ref(false)
const configsSaving = ref(false)
const configsValidating = ref(false)
const configError = ref<string | null>(null)
const configSaved = ref(false)
const validationResult = ref<AdminPaymentProviderConfigValidation | null>(null)
const secretKeyInput = ref('')

const gmpayForm = reactive({
  enabled: false,
  api_base_url: '',
  pid: '',
  currency: 'cny',
  token: 'usdt',
  network: 'tron',
  monthly_amount_cents: 990,
  yearly_amount_cents: 7900,
  order_ttl_minutes: 30,
  return_url: '',
})

const providers = computed(() => props.paymentSummary?.providers ?? [])
const gmpayConfig = computed(() =>
  paymentConfigs.value.find((config) => config.provider_key === 'gmpay') || null,
)
const gmpayHealth = computed(() =>
  providers.value.find((provider) => provider.key === 'gmpay') || null,
)
const enabledCount = computed(() => providers.value.filter((provider) => provider.enabled).length)
const configuredCount = computed(() => providers.value.filter((provider) => provider.configured).length)
const acceptedCount = computed(
  () => providers.value.filter((provider) => provider.acceptance_status === 'accepted').length,
)
const blockerCount = computed(() =>
  providers.value.reduce((total, provider) => total + provider.acceptance_blockers.length, 0),
)

const secretStatus = computed(() => {
  const status = gmpayConfig.value?.secret_fields.secret_key
  if (!status?.configured) return '未配置'
  return status.tail ? `已配置，尾号 ${status.tail}` : '已配置'
})

const canSave = computed(() => !configsLoading.value && !configsSaving.value)

const acceptanceTone = (status: string) => {
  if (status === 'accepted') return 'success'
  if (status === 'needs_review') return 'danger'
  if (status === 'missing_config' || status === 'waiting_callback') return 'warning'
  if (status === 'ready_to_test') return 'info'
  return 'neutral'
}

const configTone = (provider: AdminPaymentProviderHealth) =>
  provider.missing_config_keys.length ? 'warning' : 'success'

const applyGmpayConfig = (config: AdminPaymentProviderConfig | null) => {
  if (!config) return
  const publicConfig = config.public_config
  gmpayForm.enabled = config.enabled
  gmpayForm.api_base_url = String(publicConfig.api_base_url || '')
  gmpayForm.pid = String(publicConfig.pid || '')
  gmpayForm.currency = String(publicConfig.currency || 'cny')
  gmpayForm.token = String(publicConfig.token || 'usdt')
  gmpayForm.network = String(publicConfig.network || 'tron')
  gmpayForm.monthly_amount_cents = Number(publicConfig.monthly_amount_cents || 990)
  gmpayForm.yearly_amount_cents = Number(publicConfig.yearly_amount_cents || 7900)
  gmpayForm.order_ttl_minutes = Number(publicConfig.order_ttl_minutes || 30)
  gmpayForm.return_url = String(publicConfig.return_url || '')
  secretKeyInput.value = ''
}

const buildPayload = () => ({
  enabled: gmpayForm.enabled,
  public_config: {
    api_base_url: gmpayForm.api_base_url,
    pid: gmpayForm.pid,
    currency: gmpayForm.currency,
    token: gmpayForm.token,
    network: gmpayForm.network,
    monthly_amount_cents: gmpayForm.monthly_amount_cents,
    yearly_amount_cents: gmpayForm.yearly_amount_cents,
    order_ttl_minutes: gmpayForm.order_ttl_minutes,
    return_url: gmpayForm.return_url,
  },
  secrets: secretKeyInput.value.trim() ? { secret_key: secretKeyInput.value.trim() } : {},
})

const loadPaymentConfigs = async () => {
  configsLoading.value = true
  configError.value = null
  try {
    paymentConfigs.value = await adminAPI.listPaymentConfigs()
    applyGmpayConfig(gmpayConfig.value)
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置读取失败'
  } finally {
    configsLoading.value = false
  }
}

const saveGmpayConfig = async () => {
  if (!canSave.value) return
  configsSaving.value = true
  configError.value = null
  configSaved.value = false
  validationResult.value = null
  try {
    const updated = await adminAPI.updatePaymentConfig('gmpay', buildPayload())
    const next = paymentConfigs.value.filter((config) => config.provider_key !== updated.provider_key)
    paymentConfigs.value = [...next, updated]
    applyGmpayConfig(updated)
    configSaved.value = true
    emit('refresh')
    window.setTimeout(() => {
      configSaved.value = false
    }, 1800)
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置保存失败'
  } finally {
    configsSaving.value = false
  }
}

const validateGmpayConfig = async () => {
  configsValidating.value = true
  configError.value = null
  try {
    validationResult.value = await adminAPI.validatePaymentConfig('gmpay', buildPayload())
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置校验失败'
  } finally {
    configsValidating.value = false
  }
}

const copyEndpoint = async (key: string, value: string) => {
  if (!value) return
  await navigator.clipboard.writeText(value)
  copiedEndpointKey.value = key
  window.setTimeout(() => {
    if (copiedEndpointKey.value === key) {
      copiedEndpointKey.value = null
    }
  }, 1800)
}

onMounted(() => {
  void loadPaymentConfigs()
})
</script>

<template>
  <div class="space-y-6">
    <section class="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="flex items-center gap-3">
            <FileCog class="h-5 w-5 text-slate-700 dark:text-slate-200" />
            <h2 class="text-xl font-semibold text-slate-950 dark:text-white">支付配置中心</h2>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            第一阶段只接入 GM Pay 后台配置和下单跳转。Stripe、PayPal、支付宝、微信和旧网关继续使用服务器环境变量，GM Pay webhook 在拿到真实样本并完成严格验签前不会自动开通 Pro。
          </p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row">
          <AdminActionButton
            tone="neutral"
            class="min-h-11"
            :loading="savingKey === 'payments:refresh'"
            :disabled="savingKey === 'payments:refresh'"
            @click="emit('refresh')"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            刷新支付状态
          </AdminActionButton>
          <AdminActionButton
            tone="neutral"
            class="min-h-11"
            :loading="configsLoading"
            @click="loadPaymentConfigs"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            重新读取配置
          </AdminActionButton>
          <AdminActionButton
            tone="neutral"
            class="min-h-11"
            :disabled="!paymentSummary?.integration_evidence_packet"
            @click="emit('copyEvidence')"
          >
            <template #icon>
              <ClipboardCopy class="h-4 w-4" />
            </template>
            {{ evidenceCopied ? '已复制证据包' : '复制联调证据包' }}
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Providers</p>
          <p class="mt-2 text-3xl font-semibold">{{ providers.length }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">后端识别的支付渠道</p>
        </div>
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Enabled</p>
          <p class="mt-2 text-3xl font-semibold">{{ enabledCount }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">前台可选择渠道</p>
        </div>
        <div class="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-200/75">Configured</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">{{ configuredCount }}</p>
          <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-200/75">冒烟通过 {{ acceptedCount }}</p>
        </div>
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-xs font-semibold uppercase text-amber-700 dark:text-amber-200/75">Review</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">{{ blockerCount }}</p>
          <p class="mt-1 text-xs text-amber-700 dark:text-amber-200/75">待处理阻塞项</p>
        </div>
      </div>
    </section>

    <section class="grid min-w-0 gap-5 xl:grid-cols-[1.1fr_0.9fr]">
      <AdminPanel as="section" padding="lg">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div class="flex items-center gap-2">
              <KeyRound class="h-5 w-5 text-sky-600 dark:text-sky-300" />
              <h3 class="text-lg font-semibold text-slate-950 dark:text-white">GM Pay</h3>
              <StatusPill :tone="gmpayForm.enabled ? 'success' : 'neutral'">
                {{ gmpayForm.enabled ? 'enabled' : 'disabled' }}
              </StatusPill>
              <StatusPill :tone="gmpayConfig?.configured ? 'success' : 'warning'">
                {{ gmpayConfig?.configured ? 'configured' : 'needs config' }}
              </StatusPill>
            </div>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              配置保存后立即生效，不需要重启后端。Secret Key 只写不读，留空保存时会保留原密钥。
            </p>
          </div>

          <label class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold dark:border-slate-800">
            <input
              v-model="gmpayForm.enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            />
            启用 GM Pay
          </label>
        </div>

        <div v-if="configError" class="mt-5 rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
          {{ configError }}
        </div>

        <div
          v-if="gmpayConfig && !gmpayConfig.encryption_available"
          class="mt-5 flex gap-3 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
        >
          <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
          <p>生产环境必须在服务器环境变量设置 PAYMENT_CONFIG_ENCRYPTION_KEY，否则不能保存或读取敏感支付密钥。</p>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">API Base URL</span>
            <input
              v-model.trim="gmpayForm.api_base_url"
              type="url"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              placeholder="https://pay.example.com"
            />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">PID</span>
            <input
              v-model.trim="gmpayForm.pid"
              type="text"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              autocomplete="off"
            />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Secret Key</span>
            <input
              v-model="secretKeyInput"
              type="password"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              autocomplete="new-password"
              placeholder="留空则不修改"
            />
            <span class="block text-xs text-slate-500 dark:text-slate-400">{{ secretStatus }}</span>
          </label>
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">订单有效期</span>
            <input
              v-model.number="gmpayForm.order_ttl_minutes"
              type="number"
              min="5"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </label>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-3">
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Currency</span>
            <input
              v-model.trim="gmpayForm.currency"
              type="text"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Token</span>
            <input
              v-model.trim="gmpayForm.token"
              type="text"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Network</span>
            <input
              v-model.trim="gmpayForm.network"
              type="text"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </label>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Monthly Amount Cents</span>
            <input
              v-model.number="gmpayForm.monthly_amount_cents"
              type="number"
              min="1"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Yearly Amount Cents</span>
            <input
              v-model.number="gmpayForm.yearly_amount_cents"
              type="number"
              min="1"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </label>
        </div>

        <label class="mt-5 block space-y-2">
          <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Return URL Override</span>
          <input
            v-model.trim="gmpayForm.return_url"
            type="url"
            class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            placeholder="可选"
          />
        </label>

        <div class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex flex-wrap gap-2">
            <StatusPill v-for="key in gmpayConfig?.missing_config_keys || []" :key="key" tone="warning">
              {{ key }}
            </StatusPill>
            <StatusPill v-if="gmpayConfig?.configured" tone="success">
              配置完整
            </StatusPill>
          </div>
          <div class="flex flex-col gap-3 sm:flex-row">
            <AdminActionButton
              tone="neutral"
              :loading="configsValidating"
              :disabled="configsSaving"
              @click="validateGmpayConfig"
            >
              <template #icon>
                <TestTube2 class="h-4 w-4" />
              </template>
              本地校验
            </AdminActionButton>
            <AdminActionButton
              tone="primary"
              :loading="configsSaving"
              :disabled="!canSave"
              @click="saveGmpayConfig"
            >
              <template #icon>
                <Save class="h-4 w-4" />
              </template>
              保存 GM Pay
            </AdminActionButton>
          </div>
        </div>

        <div
          v-if="validationResult"
          class="mt-5 rounded-md border p-4 text-sm leading-6"
          :class="validationResult.valid ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100' : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'"
        >
          <div class="flex items-start gap-3">
            <CheckCircle2 v-if="validationResult.valid" class="mt-0.5 h-4 w-4 shrink-0" />
            <AlertTriangle v-else class="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p class="font-semibold">{{ validationResult.valid ? '本地校验通过' : '需要补齐配置' }}</p>
              <p v-if="validationResult.signature_preview_tail" class="mt-1">
                签名生成检查通过，预览尾号 {{ validationResult.signature_preview_tail }}
              </p>
              <ul v-if="validationResult.errors.length" class="mt-2 list-disc pl-5">
                <li v-for="error in validationResult.errors" :key="error">{{ error }}</li>
              </ul>
            </div>
          </div>
        </div>

        <p v-if="configSaved" class="mt-4 text-sm font-semibold text-emerald-700 dark:text-emerald-200">
          GM Pay 配置已保存。
        </p>
      </AdminPanel>

      <AdminPanel as="aside" padding="lg" tone="subtle">
        <div class="flex items-center gap-2">
          <ShieldCheck class="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
          <h3 class="text-lg font-semibold text-slate-950 dark:text-white">回调与验收状态</h3>
        </div>
        <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
          下单和自动开通分开验收。当前 GM Pay webhook endpoint 已存在，但只作为接收骨架。
        </p>

        <dl class="mt-5 space-y-4">
          <div>
            <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Webhook / Notify URL</dt>
            <dd class="mt-1 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
              <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
                {{ gmpayConfig?.webhook_url || gmpayHealth?.webhook_url || '' }}
              </code>
              <button
                type="button"
                class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                aria-label="复制 GM Pay webhook"
                @click="copyEndpoint('gmpay:webhook', gmpayConfig?.webhook_url || gmpayHealth?.webhook_url || '')"
              >
                <Copy class="h-4 w-4" />
              </button>
            </dd>
          </div>
          <div>
            <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Webhook Status</dt>
            <dd class="mt-2">
              <StatusPill tone="warning">skeleton, no entitlement</StatusPill>
            </dd>
          </div>
          <div v-if="gmpayHealth">
            <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Acceptance</dt>
            <dd class="mt-2 space-y-2">
              <StatusPill :tone="acceptanceTone(gmpayHealth.acceptance_status)">
                {{ gmpayHealth.acceptance_label }}
              </StatusPill>
              <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ gmpayHealth.acceptance_detail }}
              </p>
            </dd>
          </div>
        </dl>

        <div v-if="copiedEndpointKey === 'gmpay:webhook'" class="mt-3 text-xs font-semibold text-emerald-700 dark:text-emerald-200">
          地址已复制。
        </div>
      </AdminPanel>
    </section>

    <section class="grid min-w-0 gap-5 xl:grid-cols-2">
      <article
        v-for="provider in providers"
        :key="provider.key"
        class="min-w-0 max-w-full overflow-hidden rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
      >
        <div class="flex flex-wrap items-center gap-2">
          <h3 class="mr-auto text-lg font-semibold text-slate-950 dark:text-white">
            {{ provider.display_name }}
          </h3>
          <StatusPill :tone="provider.enabled ? 'success' : 'neutral'">
            {{ provider.enabled ? 'enabled' : 'disabled' }}
          </StatusPill>
          <StatusPill :tone="configTone(provider)">
            {{ provider.missing_config_keys.length ? 'needs config' : 'configured' }}
          </StatusPill>
          <StatusPill :tone="acceptanceTone(provider.acceptance_status)">
            {{ provider.acceptance_label }}
          </StatusPill>
        </div>

        <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ provider.acceptance_detail }}
        </p>

        <div class="mt-4 min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex items-center gap-2">
            <ShieldCheck class="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
            <p class="font-semibold text-slate-950 dark:text-white">商户后台配置</p>
          </div>
          <p class="mt-2 break-words text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ provider.merchant_console_hint }}
          </p>
          <div class="mt-4">
            <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              Webhook / Notify URL
            </p>
            <div class="mt-1 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
              <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
                {{ provider.webhook_url }}
              </code>
              <button
                type="button"
                class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                :aria-label="`复制 ${provider.display_name} webhook`"
                @click="copyEndpoint(`${provider.key}:webhook`, provider.webhook_url)"
              >
                <Copy class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <div class="mt-4 min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Required config</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <StatusPill
              v-for="key in provider.required_config_keys"
              :key="key"
              :tone="provider.missing_config_keys.includes(key) ? 'warning' : 'success'"
            >
              {{ key }}
            </StatusPill>
          </div>
        </div>

        <div v-if="provider.acceptance_blockers.length" class="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
          <p class="font-semibold">上线阻塞项</p>
          <ul class="mt-2 space-y-1">
            <li v-for="blocker in provider.acceptance_blockers" :key="`${provider.key}-${blocker}`">
              {{ blocker }}
            </li>
          </ul>
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-2">
          <div>
            <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Sandbox smoke test</p>
            <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
              <li v-for="(step, index) in provider.sandbox_runbook" :key="`${provider.key}-sandbox-${step}`">
                {{ index + 1 }}. {{ step }}
              </li>
            </ol>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Go-live checklist</p>
            <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
              <li v-for="(step, index) in provider.go_live_checklist" :key="`${provider.key}-live-${step}`">
                {{ index + 1 }}. {{ step }}
              </li>
            </ol>
          </div>
        </div>
      </article>
    </section>

    <AdminPanel v-if="!providers.length" as="section" tone="subtle">
      <p class="text-center text-sm text-slate-500 dark:text-slate-400">
        暂无支付渠道配置数据。请刷新支付状态或检查后端 provider 注册表。
      </p>
    </AdminPanel>
  </div>
</template>
