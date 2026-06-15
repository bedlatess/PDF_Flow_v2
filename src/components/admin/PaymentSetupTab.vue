<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCopy,
  Copy,
  CreditCard,
  Database,
  EyeOff,
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

const managedProviderOrder = ['stripe', 'paypal', 'gmpay']
const copiedEndpointKey = ref<string | null>(null)
const paymentConfigs = ref<AdminPaymentProviderConfig[]>([])
const configsLoading = ref(false)
const savingProviderKey = ref<string | null>(null)
const validatingProviderKey = ref<string | null>(null)
const configError = ref<string | null>(null)
const saveResults = ref<Record<string, string[]>>({})
const validationResults = ref<Record<string, AdminPaymentProviderConfigValidation | null>>({})
const forms = reactive<Record<string, ProviderFormState>>({})

const providerCopy: Record<string, { controls: string; when: string; impact: string; fallback: string; risk: 'high' | 'critical' }> = {
  stripe: {
    controls: 'Stripe hosted checkout, price mapping, and webhook readiness for card subscription payments.',
    when: 'Use when rotating Stripe keys, changing price IDs, fixing checkout readiness, or validating webhook setup.',
    impact: 'Bad values can break Stripe checkout redirects or webhook processing. Existing env fallback remains available when DB config is incomplete or disabled.',
    fallback: 'Legacy STRIPE_* server environment variables.',
    risk: 'critical',
  },
  paypal: {
    controls: 'PayPal checkout order configuration, client credentials, plan/product mapping, and webhook readiness.',
    when: 'Use when rotating PayPal credentials, changing plan IDs, or repairing PayPal checkout readiness.',
    impact: 'Bad values can break PayPal approval links or checkout creation. Existing PAYPAL_* fallback remains available when DB config is incomplete or disabled.',
    fallback: 'Legacy PAYPAL_* server environment variables.',
    risk: 'critical',
  },
  gmpay: {
    controls: 'GM Pay cashier creation for crypto checkout, merchant PID, amount/currency/token/network, and notify URL readiness.',
    when: 'Use for controlled GM Pay smoke tests, merchant credential rotation, or amount/network corrections.',
    impact: 'Bad values can create wrong cashier requests. This phase does not auto-mark paid or auto-open Pro from GM Pay webhook.',
    fallback: 'Provider config defaults plus legacy gateway compatibility where applicable.',
    risk: 'critical',
  },
}

const providers = computed(() =>
  (props.paymentSummary?.providers ?? []).filter((provider) =>
    managedProviderOrder.includes(provider.key),
  ),
)
const managedConfigs = computed(() =>
  paymentConfigs.value
    .filter((config) => managedProviderOrder.includes(config.provider_key))
    .slice()
    .sort((a, b) => managedProviderOrder.indexOf(a.provider_key) - managedProviderOrder.indexOf(b.provider_key)),
)
const enabledCount = computed(() => managedConfigs.value.filter((provider) => provider.enabled).length)
const configuredCount = computed(() => managedConfigs.value.filter((provider) => provider.configured).length)
const readyCount = computed(
  () => managedConfigs.value.filter((provider) => provider.enabled && provider.readiness.status === 'ready').length,
)
const reviewCount = computed(
  () => managedConfigs.value.filter((provider) => provider.enabled && provider.readiness.status !== 'ready').length,
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
  if (!status?.configured) return 'Not configured'
  return status.tail ? `Configured, ending ${status.tail}` : 'Configured'
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
  if (!ensureForm(config).enabled) return 'neutral'
  return config.readiness.status === 'ready' ? 'success' : 'warning'
}

const providerInfo = (config: AdminPaymentProviderConfig) =>
  providerCopy[config.provider_key] ?? {
    controls: config.metadata.description,
    when: 'Use when this payment provider needs configuration or readiness checks.',
    impact: 'Bad values can affect checkout for this provider.',
    fallback: 'Legacy server environment fallback when available.',
    risk: 'high' as const,
  }

const matchingHealth = (config: AdminPaymentProviderConfig): AdminPaymentProviderHealth | null =>
  providers.value.find((provider) => provider.key === config.provider_key) ?? null

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

const changedFieldSummary = (config: AdminPaymentProviderConfig) => {
  const form = ensureForm(config)
  const changed = new Set<string>()
  if (form.enabled !== config.enabled) changed.add('enabled')
  for (const field of config.metadata.fields.public) {
    if (String(form.public_config[field.key] ?? '') !== String(config.public_config[field.key] ?? '')) {
      changed.add(field.key)
    }
  }
  for (const field of config.metadata.fields.secret) {
    if (String(form.secrets[field.key] ?? '').trim()) changed.add(`${field.key} secret`)
  }
  return Array.from(changed)
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
    configError.value = error instanceof Error ? error.message : 'Payment provider config failed to load.'
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
  validationResults.value[config.provider_key] = null
  saveResults.value[config.provider_key] = changedFieldSummary(config)
  try {
    const updated = await adminAPI.updatePaymentConfig(config.provider_key, buildPayload(config))
    replaceConfig(updated)
    emit('refresh')
  } catch (error) {
    configError.value = error instanceof Error ? error.message : 'Payment provider config save failed.'
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
    configError.value = error instanceof Error ? error.message : 'Payment provider config validation failed.'
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
    <AdminPanel as="section" padding="lg">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            <CreditCard class="h-4 w-4" />
            Payment Provider Center
          </div>
          <h2 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">Stripe / PayPal / GM Pay configuration</h2>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Manage payment providers as configuration objects. Database config is preferred, legacy environment fallback stays intact, and secrets remain write-only.
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
            Refresh health
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
            Reload config
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
            {{ evidenceCopied ? 'Evidence copied' : 'Copy evidence' }}
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Managed</p>
          <p class="mt-2 text-3xl font-semibold">{{ managedConfigs.length }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Stripe, PayPal, GM Pay</p>
        </div>
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Enabled</p>
          <p class="mt-2 text-3xl font-semibold">{{ enabledCount }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Visible checkout providers</p>
        </div>
        <div class="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-200/75">Configured</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">{{ configuredCount }}</p>
          <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-200/75">{{ readyCount }} enabled and ready</p>
        </div>
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-xs font-semibold uppercase text-amber-700 dark:text-amber-200/75">Needs review</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">{{ reviewCount }}</p>
          <p class="mt-1 text-xs text-amber-700 dark:text-amber-200/75">Enabled but not ready</p>
        </div>
      </div>
    </AdminPanel>

    <div
      v-if="configError"
      class="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
    >
      {{ configError }}
    </div>

    <AdminPanel
      v-for="config in managedConfigs"
      :key="config.provider_key"
      as="section"
      padding="lg"
    >
      <div class="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <div class="space-y-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
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
                <StatusPill tone="danger">{{ providerInfo(config).risk }} risk</StatusPill>
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
              >
              Enable
            </label>
          </div>

          <div class="grid gap-3">
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">What this controls</p>
              <p class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{{ providerInfo(config).controls }}</p>
            </div>
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">When to use</p>
              <p class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{{ providerInfo(config).when }}</p>
            </div>
            <div class="rounded-md border border-amber-200 bg-amber-50 p-4 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
              <div class="flex gap-3">
                <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <p class="text-xs font-semibold uppercase">Impact</p>
                  <p class="mt-2 text-sm leading-6">{{ providerInfo(config).impact }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950/40">
            <div class="flex items-center gap-2">
              <Database class="h-4 w-4 text-slate-600 dark:text-slate-300" />
              <p class="font-semibold text-slate-950 dark:text-white">Readiness</p>
            </div>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ config.readiness.detail }}</p>
            <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Fallback source: {{ providerInfo(config).fallback }}
            </p>
            <div class="mt-3 flex flex-wrap gap-2">
              <StatusPill
                v-for="check in config.readiness.validation_checks"
                :key="`${config.provider_key}-check-${check}`"
                tone="info"
              >
                {{ check }}
              </StatusPill>
              <StatusPill
                v-for="field in config.required_public_fields"
                :key="`${config.provider_key}-required-${field}`"
                :tone="config.readiness.missing_config_keys.includes(field) ? 'warning' : 'success'"
              >
                {{ field }}
              </StatusPill>
              <StatusPill
                v-for="field in config.required_secret_fields"
                :key="`${config.provider_key}-secret-required-${field}`"
                :tone="config.readiness.missing_config_keys.includes(field) ? 'warning' : 'success'"
              >
                {{ field }} secret
              </StatusPill>
            </div>
          </div>

          <div
            v-if="matchingHealth(config)"
            class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center gap-2">
              <p class="mr-auto font-semibold text-slate-950 dark:text-white">Operational status</p>
              <StatusPill :tone="acceptanceTone(matchingHealth(config)!.acceptance_status)">
                {{ matchingHealth(config)!.acceptance_label }}
              </StatusPill>
            </div>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {{ matchingHealth(config)!.acceptance_detail }}
            </p>
          </div>
        </div>

        <div class="space-y-5">
          <div
            v-if="!config.encryption_available"
            class="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
          >
            PAYMENT_CONFIG_ENCRYPTION_KEY is missing. Sensitive payment secrets cannot be saved or read safely in production.
          </div>

          <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
            <p class="font-semibold text-slate-950 dark:text-white">Public config</p>
            <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">Non-secret provider values used by checkout creation and readiness checks.</p>
            <div class="mt-4 grid gap-4 md:grid-cols-2">
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
                >
                <span v-if="field.help_text" class="block text-xs leading-5 text-slate-500 dark:text-slate-400">
                  {{ field.help_text }}
                </span>
              </label>
            </div>
          </div>

          <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
            <div class="flex items-start gap-3">
              <EyeOff class="mt-0.5 h-4 w-4 text-slate-600 dark:text-slate-300" />
              <div>
                <p class="font-semibold text-slate-950 dark:text-white">Secret config</p>
                <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                  Secrets are write-only. Leave blank to keep the encrypted value. API, audit logs, and snapshots must not expose plaintext.
                </p>
              </div>
            </div>
            <div class="mt-4 grid gap-4 md:grid-cols-2">
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
                  :placeholder="field.placeholder || 'Leave blank to keep existing secret'"
                >
                <span class="block text-xs text-slate-500 dark:text-slate-400">
                  {{ secretStatus(config, field.key) }}. Blank means unchanged.
                </span>
              </label>
            </div>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <AdminActionButton
              tone="neutral"
              :loading="validatingProviderKey === config.provider_key"
              :disabled="Boolean(savingProviderKey)"
              @click="validateProviderConfig(config)"
            >
              <template #icon>
                <TestTube2 class="h-4 w-4" />
              </template>
              Validate
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
              Save {{ config.display_name }}
            </AdminActionButton>
          </div>

          <div
            v-if="saveResults[config.provider_key]"
            class="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100"
          >
            <div class="flex gap-3">
              <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p class="font-semibold">Save submitted</p>
                <p class="mt-1">
                  Changed fields:
                  {{ saveResults[config.provider_key].length ? saveResults[config.provider_key].join(', ') : 'none detected; save refreshes readiness' }}
                </p>
                <p class="mt-1 text-xs">Secret fields are submitted only when the input is non-empty.</p>
              </div>
            </div>
          </div>

          <div
            v-if="validationResults[config.provider_key]"
            class="rounded-md border p-4 text-sm leading-6"
            :class="validationResults[config.provider_key]?.valid ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100' : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'"
          >
            <div class="flex items-start gap-3">
              <CheckCircle2 v-if="validationResults[config.provider_key]?.valid" class="mt-0.5 h-4 w-4 shrink-0" />
              <AlertTriangle v-else class="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p class="font-semibold">
                  {{ validationResults[config.provider_key]?.valid ? 'Validation passed' : 'Validation needs attention' }}
                </p>
                <p v-if="validationResults[config.provider_key]?.signature_preview_tail" class="mt-1">
                  Signature/local check preview tail {{ validationResults[config.provider_key]?.signature_preview_tail }}
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

          <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
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
                :aria-label="`Copy ${config.display_name} webhook`"
                @click="copyEndpoint(`${config.provider_key}:webhook`, config.webhook_url)"
              >
                <Copy class="h-4 w-4" />
              </button>
            </div>
            <div v-if="copiedEndpointKey === `${config.provider_key}:webhook`" class="mt-3 text-xs font-semibold text-emerald-700 dark:text-emerald-200">
              URL copied.
            </div>
          </div>
        </div>
      </div>
    </AdminPanel>

    <AdminPanel v-if="!managedConfigs.length" as="section" tone="subtle">
      <p class="text-center text-sm text-slate-500 dark:text-slate-400">
        No managed payment provider config is available. Reload config or check the backend provider registry.
      </p>
    </AdminPanel>
  </div>
</template>
