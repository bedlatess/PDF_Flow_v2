<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCopy,
  Copy,
  CreditCard,
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
  type AdminPaymentProviderConfigUpdate,
  type AdminPaymentProviderConfigValidation,
  type AdminPaymentProviderHealth,
  type AdminPaymentSummary,
} from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

type FieldType = 'text' | 'url' | 'number' | 'password'

interface ProviderField {
  key: string
  label: string
  type: FieldType
  placeholder?: string
  min?: number
}

interface ProviderUiDefinition {
  key: string
  title: string
  summary: string
  publicFields: ProviderField[]
  secretFields: ProviderField[]
}

const props = defineProps<{
  paymentSummary: AdminPaymentSummary | null
  evidenceCopied: boolean
  savingKey: string | null
}>()

const emit = defineEmits<{
  refresh: []
  copyEvidence: []
}>()

const providerDefinitions: ProviderUiDefinition[] = [
  {
    key: 'stripe',
    title: 'Stripe',
    summary: '保存后立即用于创建 Stripe Checkout Session。付款成功仍然只认 Stripe webhook，不认前端 success 页面。',
    publicFields: [
      { key: 'price_id_monthly', label: 'Monthly Price ID', type: 'text', placeholder: 'price_...' },
      { key: 'price_id_yearly', label: 'Yearly Price ID', type: 'text', placeholder: 'price_...' },
    ],
    secretFields: [
      { key: 'secret_key', label: 'Secret Key', type: 'password', placeholder: '留空则不修改' },
      { key: 'webhook_secret', label: 'Webhook Secret', type: 'password', placeholder: '留空则不修改' },
    ],
  },
  {
    key: 'paypal',
    title: 'PayPal',
    summary: '保存后用于创建 PayPal checkout order 并返回 approval URL。capture 和 webhook 自动权益不在本轮扩展。',
    publicFields: [
      { key: 'api_base_url', label: 'API Base URL', type: 'url', placeholder: 'https://api-m.sandbox.paypal.com' },
      { key: 'client_id', label: 'Client ID', type: 'text' },
      { key: 'webhook_id', label: 'Webhook ID', type: 'text' },
    ],
    secretFields: [
      { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: '留空则不修改' },
    ],
  },
  {
    key: 'gmpay',
    title: 'GM Pay',
    summary: '已打通下单跳转，webhook 目前只保留入口，不会自动标记 paid 或开通 Pro。',
    publicFields: [
      { key: 'api_base_url', label: 'API Base URL', type: 'url', placeholder: 'https://pay.example.com' },
      { key: 'pid', label: 'PID', type: 'text' },
      { key: 'currency', label: 'Currency', type: 'text', placeholder: 'cny' },
      { key: 'token', label: 'Token', type: 'text', placeholder: 'usdt' },
      { key: 'network', label: 'Network', type: 'text', placeholder: 'tron' },
      { key: 'monthly_amount_cents', label: 'Monthly Amount Cents', type: 'number', min: 1 },
      { key: 'yearly_amount_cents', label: 'Yearly Amount Cents', type: 'number', min: 1 },
      { key: 'order_ttl_minutes', label: 'Order TTL Minutes', type: 'number', min: 5 },
      { key: 'return_url', label: 'Return URL Override', type: 'url', placeholder: '可选' },
    ],
    secretFields: [
      { key: 'secret_key', label: 'Secret Key', type: 'password', placeholder: '留空则不修改' },
    ],
  },
]

const copiedEndpointKey = ref<string | null>(null)
const paymentConfigs = ref<AdminPaymentProviderConfig[]>([])
const configsLoading = ref(false)
const savingProviderKey = ref<string | null>(null)
const validatingProviderKey = ref<string | null>(null)
const configError = ref<string | null>(null)
const savedProviderKey = ref<string | null>(null)
const validationResults = ref<Record<string, AdminPaymentProviderConfigValidation | null>>({})
const forms = reactive<Record<string, {
  enabled: boolean
  public_config: Record<string, string | number | boolean | undefined>
  secrets: Record<string, string>
}>>({})

const providers = computed(() => props.paymentSummary?.providers ?? [])
const enabledCount = computed(() => providers.value.filter((provider) => provider.enabled).length)
const configuredCount = computed(() => providers.value.filter((provider) => provider.configured).length)
const acceptedCount = computed(
  () => providers.value.filter((provider) => provider.acceptance_status === 'accepted').length,
)
const blockerCount = computed(() =>
  providers.value.reduce((total, provider) => total + provider.acceptance_blockers.length, 0),
)
const managedConfigs = computed(() =>
  providerDefinitions
    .map((definition) => paymentConfigs.value.find((config) => config.provider_key === definition.key))
    .filter((config): config is AdminPaymentProviderConfig => Boolean(config)),
)

const ensureForm = (definition: ProviderUiDefinition) => {
  if (forms[definition.key]) return forms[definition.key]
  forms[definition.key] = {
    enabled: false,
    public_config: {},
    secrets: Object.fromEntries(definition.secretFields.map((field) => [field.key, ''])),
  }
  return forms[definition.key]
}

providerDefinitions.forEach(ensureForm)

const providerConfig = (providerKey: string) =>
  paymentConfigs.value.find((config) => config.provider_key === providerKey) || null

const providerHealth = (providerKey: string) =>
  providers.value.find((provider) => provider.key === providerKey) || null

const secretStatus = (config: AdminPaymentProviderConfig | null, fieldKey: string) => {
  const status = config?.secret_fields[fieldKey]
  if (!status?.configured) return '未配置'
  return status.tail ? `已配置，尾号 ${status.tail}` : '已配置'
}

const inputMode = (field: ProviderField): 'numeric' | undefined =>
  field.type === 'number' ? 'numeric' : undefined

const acceptanceTone = (status: string) => {
  if (status === 'accepted') return 'success'
  if (status === 'needs_review') return 'danger'
  if (status === 'missing_config' || status === 'waiting_callback') return 'warning'
  if (status === 'ready_to_test') return 'info'
  return 'neutral'
}

const configTone = (provider: AdminPaymentProviderHealth) =>
  provider.missing_config_keys.length ? 'warning' : 'success'

const applyProviderConfig = (definition: ProviderUiDefinition, config: AdminPaymentProviderConfig | null) => {
  const form = ensureForm(definition)
  form.enabled = Boolean(config?.enabled)
  for (const field of definition.publicFields) {
    const value = config?.public_config[field.key]
    if (field.type === 'number') {
      form.public_config[field.key] = Number(value ?? field.min ?? 0)
    } else {
      form.public_config[field.key] = String(value ?? '')
    }
  }
  for (const field of definition.secretFields) {
    form.secrets[field.key] = ''
  }
}

const buildPayload = (definition: ProviderUiDefinition): AdminPaymentProviderConfigUpdate => {
  const form = ensureForm(definition)
  const secrets = Object.fromEntries(
    definition.secretFields
      .map((field) => [field.key, String(form.secrets[field.key] || '').trim()])
      .filter(([, value]) => value),
  )
  return {
    enabled: form.enabled,
    public_config: { ...form.public_config },
    secrets,
  }
}

const loadPaymentConfigs = async () => {
  configsLoading.value = true
  configError.value = null
  try {
    paymentConfigs.value = await adminAPI.listPaymentConfigs()
    for (const definition of providerDefinitions) {
      applyProviderConfig(definition, providerConfig(definition.key))
    }
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置读取失败'
  } finally {
    configsLoading.value = false
  }
}

const saveProviderConfig = async (definition: ProviderUiDefinition) => {
  if (configsLoading.value || savingProviderKey.value) return
  savingProviderKey.value = definition.key
  configError.value = null
  savedProviderKey.value = null
  validationResults.value[definition.key] = null
  try {
    const updated = await adminAPI.updatePaymentConfig(definition.key, buildPayload(definition))
    const next = paymentConfigs.value.filter((config) => config.provider_key !== updated.provider_key)
    paymentConfigs.value = [...next, updated]
    applyProviderConfig(definition, updated)
    savedProviderKey.value = definition.key
    emit('refresh')
    window.setTimeout(() => {
      if (savedProviderKey.value === definition.key) {
        savedProviderKey.value = null
      }
    }, 1800)
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置保存失败'
  } finally {
    savingProviderKey.value = null
  }
}

const validateProviderConfig = async (definition: ProviderUiDefinition) => {
  validatingProviderKey.value = definition.key
  configError.value = null
  try {
    validationResults.value[definition.key] = await adminAPI.validatePaymentConfig(
      definition.key,
      buildPayload(definition),
    )
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置校验失败'
  } finally {
    validatingProviderKey.value = null
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
            当前阶段只做后台配置化和下单入口。密钥加密存储且只写不读，旧环境变量继续作为 fallback；真实付款、webhook 自动 paid 和自动开通 Pro 后置。
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

    <div
      v-if="configError"
      class="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
    >
      {{ configError }}
    </div>

    <section class="grid min-w-0 gap-5 xl:grid-cols-2">
      <AdminPanel
        v-for="definition in providerDefinitions"
        :key="definition.key"
        as="section"
        padding="lg"
      >
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <CreditCard v-if="definition.key === 'stripe'" class="h-5 w-5 text-sky-600 dark:text-sky-300" />
              <KeyRound v-else class="h-5 w-5 text-sky-600 dark:text-sky-300" />
              <h3 class="text-lg font-semibold text-slate-950 dark:text-white">{{ definition.title }}</h3>
              <StatusPill :tone="ensureForm(definition).enabled ? 'success' : 'neutral'">
                {{ ensureForm(definition).enabled ? 'enabled' : 'disabled' }}
              </StatusPill>
              <StatusPill :tone="providerConfig(definition.key)?.configured ? 'success' : 'warning'">
                {{ providerConfig(definition.key)?.configured ? 'configured' : 'needs config' }}
              </StatusPill>
            </div>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {{ definition.summary }}
            </p>
          </div>

          <label class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold dark:border-slate-800">
            <input
              v-model="ensureForm(definition).enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            />
            启用 {{ definition.title }}
          </label>
        </div>

        <div
          v-if="providerConfig(definition.key) && !providerConfig(definition.key)?.encryption_available"
          class="mt-5 flex gap-3 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
        >
          <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
          <p>生产环境必须在服务器环境变量设置 PAYMENT_CONFIG_ENCRYPTION_KEY，否则不能保存或读取敏感支付密钥。</p>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <label
            v-for="field in definition.publicFields"
            :key="`${definition.key}-${field.key}`"
            class="space-y-2"
          >
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ field.label }}</span>
            <input
              v-model.trim="ensureForm(definition).public_config[field.key]"
              :type="field.type"
              :min="field.min"
              :inputmode="inputMode(field)"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              :placeholder="field.placeholder"
            />
          </label>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label
            v-for="field in definition.secretFields"
            :key="`${definition.key}-${field.key}`"
            class="space-y-2"
          >
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ field.label }}</span>
            <input
              v-model="ensureForm(definition).secrets[field.key]"
              type="password"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              autocomplete="new-password"
              :placeholder="field.placeholder || '留空则不修改'"
            />
            <span class="block text-xs text-slate-500 dark:text-slate-400">
              {{ secretStatus(providerConfig(definition.key), field.key) }}
            </span>
          </label>
        </div>

        <div class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex flex-wrap gap-2">
            <StatusPill
              v-for="key in providerConfig(definition.key)?.missing_config_keys || []"
              :key="`${definition.key}-missing-${key}`"
              tone="warning"
            >
              {{ key }}
            </StatusPill>
            <StatusPill v-if="providerConfig(definition.key)?.configured" tone="success">
              配置完整
            </StatusPill>
          </div>
          <div class="flex flex-col gap-3 sm:flex-row">
            <AdminActionButton
              tone="neutral"
              :loading="validatingProviderKey === definition.key"
              :disabled="Boolean(savingProviderKey)"
              @click="validateProviderConfig(definition)"
            >
              <template #icon>
                <TestTube2 class="h-4 w-4" />
              </template>
              本地校验
            </AdminActionButton>
            <AdminActionButton
              tone="primary"
              :loading="savingProviderKey === definition.key"
              :disabled="configsLoading || Boolean(savingProviderKey)"
              @click="saveProviderConfig(definition)"
            >
              <template #icon>
                <Save class="h-4 w-4" />
              </template>
              保存 {{ definition.title }}
            </AdminActionButton>
          </div>
        </div>

        <div
          v-if="validationResults[definition.key]"
          class="mt-5 rounded-md border p-4 text-sm leading-6"
          :class="validationResults[definition.key]?.valid ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100' : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'"
        >
          <div class="flex items-start gap-3">
            <CheckCircle2 v-if="validationResults[definition.key]?.valid" class="mt-0.5 h-4 w-4 shrink-0" />
            <AlertTriangle v-else class="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p class="font-semibold">
                {{ validationResults[definition.key]?.valid ? '本地校验通过' : '需要补齐配置' }}
              </p>
              <p v-if="validationResults[definition.key]?.signature_preview_tail" class="mt-1">
                签名生成检查通过，预览尾号 {{ validationResults[definition.key]?.signature_preview_tail }}
              </p>
              <p class="mt-1 text-xs uppercase tracking-wide">
                {{ validationResults[definition.key]?.checks.join(' / ') }}
              </p>
              <ul v-if="validationResults[definition.key]?.errors.length" class="mt-2 list-disc pl-5">
                <li
                  v-for="error in validationResults[definition.key]?.errors"
                  :key="`${definition.key}-${error}`"
                >
                  {{ error }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <p
          v-if="savedProviderKey === definition.key"
          class="mt-4 text-sm font-semibold text-emerald-700 dark:text-emerald-200"
        >
          {{ definition.title }} 配置已保存。
        </p>

        <div class="mt-5 min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex items-center gap-2">
            <ShieldCheck class="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
            <p class="font-semibold text-slate-950 dark:text-white">Webhook / Notify URL</p>
          </div>
          <div class="mt-3 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
            <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
              {{ providerConfig(definition.key)?.webhook_url || providerHealth(definition.key)?.webhook_url || '' }}
            </code>
            <button
              type="button"
              class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              :aria-label="`复制 ${definition.title} webhook`"
              @click="copyEndpoint(`${definition.key}:webhook`, providerConfig(definition.key)?.webhook_url || providerHealth(definition.key)?.webhook_url || '')"
            >
              <Copy class="h-4 w-4" />
            </button>
          </div>
          <div v-if="copiedEndpointKey === `${definition.key}:webhook`" class="mt-3 text-xs font-semibold text-emerald-700 dark:text-emerald-200">
            地址已复制。
          </div>
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

    <AdminPanel v-if="!providers.length && !managedConfigs.length" as="section" tone="subtle">
      <p class="text-center text-sm text-slate-500 dark:text-slate-400">
        暂无支付渠道配置数据。请刷新支付状态或检查后端 provider 注册表。
      </p>
    </AdminPanel>
  </div>
</template>
