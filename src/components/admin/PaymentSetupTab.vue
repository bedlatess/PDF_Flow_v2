<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCopy,
  Copy,
  CreditCard,
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
  type AdminPaymentProviderFieldMetadata,
  type AdminPaymentProviderHealth,
  type AdminPaymentSummary,
} from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

type FormValue = string | number | boolean | undefined

interface ProviderFormState {
  enabled: boolean
  public_config: Record<string, FormValue>
  secrets: Record<string, string>
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

const copiedEndpointKey = ref<string | null>(null)
const paymentConfigs = ref<AdminPaymentProviderConfig[]>([])
const configsLoading = ref(false)
const savingProviderKey = ref<string | null>(null)
const validatingProviderKey = ref<string | null>(null)
const configError = ref<string | null>(null)
const savedProviderKey = ref<string | null>(null)
const validationResults = ref<Record<string, AdminPaymentProviderConfigValidation | null>>({})
const forms = reactive<Record<string, ProviderFormState>>({})

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
  paymentConfigs.value.slice().sort((a, b) => {
    const order = ['stripe', 'paypal', 'gmpay']
    return order.indexOf(a.provider_key) - order.indexOf(b.provider_key)
  }),
)

const ensureForm = (config: AdminPaymentProviderConfig) => {
  if (!forms[config.provider_key]) {
    forms[config.provider_key] = {
      enabled: false,
      public_config: {},
      secrets: {},
    }
  }
  return forms[config.provider_key]
}

const applyProviderConfig = (config: AdminPaymentProviderConfig) => {
  const form = ensureForm(config)
  form.enabled = Boolean(config.enabled)
  for (const field of config.metadata.fields.public) {
    const value = config.public_config[field.key]
    if (field.input_type === 'number') {
      form.public_config[field.key] = Number(value ?? field.min_value ?? 0)
    } else {
      form.public_config[field.key] = String(value ?? '')
    }
  }
  for (const field of config.metadata.fields.secret) {
    form.secrets[field.key] = ''
  }
}

const secretStatus = (config: AdminPaymentProviderConfig, fieldKey: string) => {
  const status = config.secret_fields[fieldKey]
  if (!status?.configured) return '未配置'
  return status.tail ? `已配置，尾号 ${status.tail}` : '已配置'
}

const inputType = (field: AdminPaymentProviderFieldMetadata) =>
  field.secret ? 'password' : field.input_type

const inputMode = (field: AdminPaymentProviderFieldMetadata): 'numeric' | undefined =>
  field.input_type === 'number' ? 'numeric' : undefined

const acceptanceTone = (status: string) => {
  if (status === 'accepted') return 'success'
  if (status === 'needs_review') return 'danger'
  if (status === 'missing_config' || status === 'waiting_callback') return 'warning'
  if (status === 'ready_to_test') return 'info'
  return 'neutral'
}

const readinessTone = (config: AdminPaymentProviderConfig) => {
  if (!config.enabled) return 'neutral'
  return config.configured ? 'success' : 'warning'
}

const configTone = (provider: AdminPaymentProviderHealth) =>
  provider.missing_config_keys.length ? 'warning' : 'success'

const buildPayload = (config: AdminPaymentProviderConfig): AdminPaymentProviderConfigUpdate => {
  const form = ensureForm(config)
  const secrets = Object.fromEntries(
    config.metadata.fields.secret
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
    for (const config of paymentConfigs.value) {
      applyProviderConfig(config)
    }
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置读取失败'
  } finally {
    configsLoading.value = false
  }
}

const replaceConfig = (updated: AdminPaymentProviderConfig) => {
  const next = paymentConfigs.value.filter((config) => config.provider_key !== updated.provider_key)
  paymentConfigs.value = [...next, updated]
  applyProviderConfig(updated)
}

const saveProviderConfig = async (config: AdminPaymentProviderConfig) => {
  if (configsLoading.value || savingProviderKey.value) return
  savingProviderKey.value = config.provider_key
  configError.value = null
  savedProviderKey.value = null
  validationResults.value[config.provider_key] = null
  try {
    const updated = await adminAPI.updatePaymentConfig(config.provider_key, buildPayload(config))
    replaceConfig(updated)
    savedProviderKey.value = config.provider_key
    emit('refresh')
    window.setTimeout(() => {
      if (savedProviderKey.value === config.provider_key) {
        savedProviderKey.value = null
      }
    }, 1800)
  } catch (error) {
    configError.value = error instanceof Error ? error.message : '支付配置保存失败'
  } finally {
    savingProviderKey.value = null
  }
}

const validateProviderConfig = async (config: AdminPaymentProviderConfig) => {
  validatingProviderKey.value = config.provider_key
  configError.value = null
  try {
    validationResults.value[config.provider_key] = await adminAPI.validatePaymentConfig(
      config.provider_key,
      buildPayload(config),
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
            <CreditCard class="h-5 w-5 text-slate-700 dark:text-slate-200" />
            <h2 class="text-xl font-semibold text-slate-950 dark:text-white">支付配置中心</h2>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            这里由后端 provider registry 驱动字段、校验和就绪状态。密钥只写不读并加密保存，数据库配置优先，旧环境变量继续作为 fallback；真实付款、webhook 自动 paid 和自动开通 Pro 不在本阶段处理。
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
          <p class="mt-2 text-3xl font-semibold">{{ managedConfigs.length }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">统一配置中心管理</p>
        </div>
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Enabled</p>
          <p class="mt-2 text-3xl font-semibold">{{ enabledCount }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">前台可选择渠道</p>
        </div>
        <div class="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-200/75">Configured</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">{{ configuredCount }}</p>
          <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-200/75">已通过联调 {{ acceptedCount }}</p>
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
        v-for="config in managedConfigs"
        :key="config.provider_key"
        as="section"
        padding="lg"
      >
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <CreditCard v-if="config.provider_key === 'stripe'" class="h-5 w-5 text-sky-600 dark:text-sky-300" />
              <KeyRound v-else class="h-5 w-5 text-sky-600 dark:text-sky-300" />
              <h3 class="text-lg font-semibold text-slate-950 dark:text-white">{{ config.display_name }}</h3>
              <StatusPill :tone="ensureForm(config).enabled ? 'success' : 'neutral'">
                {{ ensureForm(config).enabled ? 'enabled' : 'disabled' }}
              </StatusPill>
              <StatusPill :tone="readinessTone(config)">
                {{ config.readiness.label }}
              </StatusPill>
            </div>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {{ config.metadata.description }}
            </p>
          </div>

          <label class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold dark:border-slate-800">
            <input
              v-model="ensureForm(config).enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            />
            启用 {{ config.display_name }}
          </label>
        </div>

        <div
          v-if="!config.encryption_available"
          class="mt-5 flex gap-3 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
        >
          <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
          <p>生产环境必须在服务器环境变量设置 PAYMENT_CONFIG_ENCRYPTION_KEY，否则不能保存或读取敏感支付密钥。</p>
        </div>

        <div class="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex flex-wrap items-start gap-3">
            <StatusPill :tone="config.configured ? 'success' : 'warning'">
              {{ config.configured ? '配置完整' : '配置未完整' }}
            </StatusPill>
            <p class="min-w-0 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {{ config.readiness.detail }}
            </p>
          </div>
          <div v-if="config.readiness.missing_config_keys.length" class="mt-3 flex flex-wrap gap-2">
            <StatusPill
              v-for="key in config.readiness.missing_config_keys"
              :key="`${config.provider_key}-missing-${key}`"
              tone="warning"
            >
              {{ key }}
            </StatusPill>
          </div>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <label
            v-for="field in config.metadata.fields.public"
            :key="`${config.provider_key}-${field.key}`"
            class="space-y-2"
          >
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {{ field.label }}<span v-if="field.required" class="text-rose-500"> *</span>
            </span>
            <input
              v-model.trim="ensureForm(config).public_config[field.key]"
              :type="inputType(field)"
              :min="field.min_value ?? undefined"
              :max="field.max_value ?? undefined"
              :inputmode="inputMode(field)"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              :placeholder="field.placeholder"
            />
            <span v-if="field.help_text" class="block text-xs leading-5 text-slate-500 dark:text-slate-400">
              {{ field.help_text }}
            </span>
          </label>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label
            v-for="field in config.metadata.fields.secret"
            :key="`${config.provider_key}-${field.key}`"
            class="space-y-2"
          >
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {{ field.label }}<span v-if="field.required" class="text-rose-500"> *</span>
            </span>
            <input
              v-model="ensureForm(config).secrets[field.key]"
              type="password"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              autocomplete="new-password"
              :placeholder="field.placeholder || '留空则不修改'"
            />
            <span class="block text-xs text-slate-500 dark:text-slate-400">
              {{ secretStatus(config, field.key) }}
            </span>
            <span v-if="field.help_text" class="block text-xs leading-5 text-slate-500 dark:text-slate-400">
              {{ field.help_text }}
            </span>
          </label>
        </div>

        <div class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex flex-wrap gap-2">
            <StatusPill
              v-for="check in config.readiness.validation_checks"
              :key="`${config.provider_key}-check-${check}`"
              tone="info"
            >
              {{ check }}
            </StatusPill>
          </div>
          <div class="flex flex-col gap-3 sm:flex-row">
            <AdminActionButton
              tone="neutral"
              :loading="validatingProviderKey === config.provider_key"
              :disabled="Boolean(savingProviderKey)"
              @click="validateProviderConfig(config)"
            >
              <template #icon>
                <TestTube2 class="h-4 w-4" />
              </template>
              本地校验
            </AdminActionButton>
            <AdminActionButton
              tone="primary"
              :loading="savingProviderKey === config.provider_key"
              :disabled="configsLoading || Boolean(savingProviderKey)"
              @click="saveProviderConfig(config)"
            >
              <template #icon>
                <Save class="h-4 w-4" />
              </template>
              保存 {{ config.display_name }}
            </AdminActionButton>
          </div>
        </div>

        <div
          v-if="validationResults[config.provider_key]"
          class="mt-5 rounded-md border p-4 text-sm leading-6"
          :class="validationResults[config.provider_key]?.valid ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100' : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'"
        >
          <div class="flex items-start gap-3">
            <CheckCircle2 v-if="validationResults[config.provider_key]?.valid" class="mt-0.5 h-4 w-4 shrink-0" />
            <AlertTriangle v-else class="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p class="font-semibold">
                {{ validationResults[config.provider_key]?.valid ? '本地校验通过' : '需要补齐配置' }}
              </p>
              <p v-if="validationResults[config.provider_key]?.signature_preview_tail" class="mt-1">
                签名生成检查通过，预览尾号 {{ validationResults[config.provider_key]?.signature_preview_tail }}
              </p>
              <p class="mt-1 text-xs uppercase tracking-wide">
                {{ validationResults[config.provider_key]?.checks.join(' / ') }}
              </p>
              <ul v-if="validationResults[config.provider_key]?.errors.length" class="mt-2 list-disc pl-5">
                <li
                  v-for="error in validationResults[config.provider_key]?.errors"
                  :key="`${config.provider_key}-${error}`"
                >
                  {{ error }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <p
          v-if="savedProviderKey === config.provider_key"
          class="mt-4 text-sm font-semibold text-emerald-700 dark:text-emerald-200"
        >
          {{ config.display_name }} 配置已保存。
        </p>

        <div class="mt-5 min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex items-center gap-2">
            <ShieldCheck class="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
            <p class="font-semibold text-slate-950 dark:text-white">Webhook / Notify URL</p>
          </div>
          <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ config.metadata.merchant_console_hint }}
          </p>
          <div class="mt-3 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
            <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
              {{ config.webhook_url }}
            </code>
            <button
              type="button"
              class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              :aria-label="`复制 ${config.display_name} webhook`"
              @click="copyEndpoint(`${config.provider_key}:webhook`, config.webhook_url)"
            >
              <Copy class="h-4 w-4" />
            </button>
          </div>
          <div v-if="copiedEndpointKey === `${config.provider_key}:webhook`" class="mt-3 text-xs font-semibold text-emerald-700 dark:text-emerald-200">
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
        暂无支付渠道配置数据。请刷新支付状态或检查后端 provider registry。
      </p>
    </AdminPanel>
  </div>
</template>
