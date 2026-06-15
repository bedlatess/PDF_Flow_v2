<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  EyeOff,
  RefreshCw,
  Save,
  ServerCog,
  TestTube2,
  Wrench,
} from 'lucide-vue-next'
import {
  adminAPI,
  type AdminServiceProviderConfig,
  type AdminServiceProviderConfigValidation,
  type AdminServiceProviderFieldMetadata,
} from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  serviceProviderConfigs: AdminServiceProviderConfig[]
  serviceFilter: string
  savingKey: string | null
}>()

const emit = defineEmits<{
  refresh: []
  save: [config: AdminServiceProviderConfig]
  'update:service-filter': [value: string]
}>()

const formState = reactive<Record<string, AdminServiceProviderConfig>>({})
const validationResults = ref<Record<string, AdminServiceProviderConfigValidation | null>>({})
const validationErrors = ref<Record<string, string | null>>({})
const validatingKey = ref<string | null>(null)
const saveResults = ref<Record<string, string[]>>({})

const serviceFilters = [
  { key: 'all', label: 'All' },
  { key: 'ocr', label: 'OCR' },
  { key: 'office', label: 'Office' },
  { key: 'ai', label: 'AI' },
]

const serviceCopy: Record<string, { controls: string; when: string; impact: string; risk: 'medium' | 'high' }> = {
  ocr: {
    controls: 'OCR runtime command and default recognition language used by scanned PDF text extraction.',
    when: 'Change this when Tesseract moves, language defaults change, or OCR smoke tests fail.',
    impact: 'Bad values can make OCR jobs fail or fall back to server defaults.',
    risk: 'medium',
  },
  office: {
    controls: 'LibreOffice runtime path and timeout used for Office to PDF conversion.',
    when: 'Change this after server package changes or when Office conversions time out.',
    impact: 'Bad values can break DOCX/XLSX/PPTX conversion while existing PDF tools keep working.',
    risk: 'medium',
  },
  ai: {
    controls: 'Gemini API endpoint, model, timeout, and write-only API key for AI-assisted PDF features.',
    when: 'Change this when rotating keys, changing model, or recovering from AI provider failures.',
    impact: 'Bad values can break AI analysis or increase failed AI requests. It does not affect local PDF tools.',
    risk: 'high',
  },
}

const configKey = (config: AdminServiceProviderConfig) =>
  `${config.service_key}:${config.provider_key}`

const cloneConfig = (config: AdminServiceProviderConfig): AdminServiceProviderConfig => ({
  ...config,
  public_config: { ...config.public_config },
  secret_fields: { ...config.secret_fields },
  secrets: {},
  required_public_fields: [...config.required_public_fields],
  required_secret_fields: [...config.required_secret_fields],
  missing_config_keys: [...config.missing_config_keys],
  metadata: {
    ...config.metadata,
    validation_checks: [...config.metadata.validation_checks],
    setup_notes: [...config.metadata.setup_notes],
    fields: {
      public: [...config.metadata.fields.public],
      secret: [...config.metadata.fields.secret],
    },
  },
  readiness: {
    ...config.readiness,
    missing_config_keys: [...config.readiness.missing_config_keys],
    validation_checks: [...config.readiness.validation_checks],
  },
})

const ensureFormState = (config: AdminServiceProviderConfig) => {
  const key = configKey(config)
  formState[key] = {
    ...cloneConfig(config),
    secrets: {},
  }
}

watch(
  () => props.serviceProviderConfigs,
  (configs) => {
    for (const config of configs) ensureFormState(config)
  },
  { immediate: true, deep: true },
)

const visibleConfigs = computed(() => {
  if (props.serviceFilter === 'all') return props.serviceProviderConfigs
  return props.serviceProviderConfigs.filter((config) => config.service_key === props.serviceFilter)
})

const summary = computed(() => {
  const enabled = props.serviceProviderConfigs.filter((config) => config.enabled).length
  const ready = props.serviceProviderConfigs.filter(
    (config) => config.enabled && config.readiness.status === 'ready',
  ).length
  const review = props.serviceProviderConfigs.filter(
    (config) => config.enabled && config.readiness.status !== 'ready',
  ).length
  const fallback = props.serviceProviderConfigs.filter((config) => !config.enabled || !config.configured).length
  return { enabled, ready, review, fallback }
})

const draftFor = (config: AdminServiceProviderConfig) =>
  formState[configKey(config)] ?? config

const inputType = (field: AdminServiceProviderFieldMetadata) =>
  field.secret ? 'password' : field.input_type

const inputMode = (field: AdminServiceProviderFieldMetadata): 'numeric' | undefined =>
  field.input_type === 'number' ? 'numeric' : undefined

const updateField = (config: AdminServiceProviderConfig, field: string, value: string | number | boolean) => {
  const key = configKey(config)
  const draft = draftFor(config)
  formState[key] = {
    ...draft,
    public_config: {
      ...draft.public_config,
      [field]: value,
    },
  }
}

const updateSecret = (config: AdminServiceProviderConfig, field: string, value: string) => {
  const key = configKey(config)
  const draft = draftFor(config)
  formState[key] = {
    ...draft,
    secrets: {
      ...(draft.secrets ?? {}),
      [field]: value,
    },
  }
}

const updateEnabled = (config: AdminServiceProviderConfig, value: boolean) => {
  const key = configKey(config)
  const draft = draftFor(config)
  formState[key] = { ...draft, enabled: value }
}

const updatePriority = (config: AdminServiceProviderConfig, value: number) => {
  const key = configKey(config)
  const draft = draftFor(config)
  formState[key] = { ...draft, priority: value }
}

const secretStatusLabel = (config: AdminServiceProviderConfig, field: string) => {
  const status = config.secret_fields[field]
  if (!status?.configured) return 'Not configured'
  return status.tail ? `Configured, ending ${status.tail}` : 'Configured'
}

const readinessTone = (config: AdminServiceProviderConfig) => {
  if (!draftFor(config).enabled) return 'neutral'
  return config.readiness.status === 'ready' ? 'success' : 'warning'
}

const riskTone = (config: AdminServiceProviderConfig) =>
  serviceCopy[config.service_key]?.risk === 'high' ? 'warning' : 'info'

const providerCopy = (config: AdminServiceProviderConfig) =>
  serviceCopy[config.service_key] ?? {
    controls: config.metadata.description,
    when: 'Use when this provider needs runtime configuration or readiness checks.',
    impact: 'Bad values can make this service unavailable until fixed or fallback takes over.',
    risk: 'medium' as const,
  }

const changedFieldSummary = (config: AdminServiceProviderConfig) => {
  const draft = draftFor(config)
  const changed = new Set<string>()
  if (draft.enabled !== config.enabled) changed.add('enabled')
  if (Number(draft.priority) !== Number(config.priority)) changed.add('priority')
  for (const field of config.metadata.fields.public) {
    if (String(draft.public_config[field.key] ?? '') !== String(config.public_config[field.key] ?? '')) {
      changed.add(field.key)
    }
  }
  for (const field of config.metadata.fields.secret) {
    if (String(draft.secrets?.[field.key] ?? '').trim()) changed.add(`${field.key} secret`)
  }
  return Array.from(changed)
}

const saveDraft = (config: AdminServiceProviderConfig) => {
  const key = configKey(config)
  saveResults.value[key] = changedFieldSummary(config)
  emit('save', draftFor(config))
}

const validateDraft = async (config: AdminServiceProviderConfig) => {
  const key = configKey(config)
  validatingKey.value = key
  validationErrors.value[key] = null
  try {
    const draft = draftFor(config)
    validationResults.value[key] = await adminAPI.validateServiceProviderConfig(
      draft.service_key,
      draft.provider_key,
      {
        enabled: draft.enabled,
        priority: Number(draft.priority || 100),
        public_config: draft.public_config,
        secrets: draft.secrets ?? {},
      },
    )
  } catch (error) {
    validationErrors.value[key] =
      error instanceof Error ? error.message : 'Validation request failed. Try again later.'
  } finally {
    validatingKey.value = null
  }
}
</script>

<template>
  <div class="space-y-6">
    <AdminPanel class="overflow-hidden" padding="lg">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            <Wrench class="h-4 w-4" />
            Service Provider Center
          </div>
          <h3 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
            OCR / Office / AI runtime configuration
          </h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Manage provider readiness as configuration objects. Database settings are used first; disabled, missing, or incomplete configs fall back to existing server settings.
          </p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-end">
          <label
            v-for="filter in serviceFilters"
            :key="filter.key"
            class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold dark:border-slate-800"
          >
            <input
              :checked="serviceFilter === filter.key"
              type="radio"
              name="service-filter"
              class="h-4 w-4 border-slate-300 text-sky-600 focus:ring-sky-500"
              @change="emit('update:service-filter', filter.key)"
            >
            {{ filter.label }}
          </label>
          <AdminActionButton
            tone="neutral"
            :loading="savingKey === 'service-providers:refresh'"
            @click="emit('refresh')"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            Refresh
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Enabled</p>
          <p class="mt-2 text-3xl font-semibold">{{ summary.enabled }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Runtime providers switched on</p>
        </div>
        <div class="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-200/75">Ready</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">{{ summary.ready }}</p>
          <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-200/75">Enabled and complete</p>
        </div>
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-xs font-semibold uppercase text-amber-700 dark:text-amber-200/75">Needs review</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">{{ summary.review }}</p>
          <p class="mt-1 text-xs text-amber-700 dark:text-amber-200/75">Enabled but not ready</p>
        </div>
        <div class="rounded-md border border-sky-200 bg-sky-50 p-4 dark:border-sky-500/30 dark:bg-sky-500/10">
          <p class="text-xs font-semibold uppercase text-sky-700 dark:text-sky-200/75">Fallback</p>
          <p class="mt-2 text-3xl font-semibold text-sky-800 dark:text-sky-100">{{ summary.fallback }}</p>
          <p class="mt-1 text-xs text-sky-700 dark:text-sky-200/75">Disabled or incomplete configs</p>
        </div>
      </div>
    </AdminPanel>

    <AdminPanel
      v-for="config in visibleConfigs"
      :key="`${config.service_key}:${config.provider_key}`"
      as="section"
      padding="lg"
    >
      <div class="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <div class="space-y-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <ServerCog class="h-5 w-5 text-sky-600 dark:text-sky-300" />
                <h3 class="text-lg font-semibold text-slate-950 dark:text-white">
                  {{ config.display_name }}
                </h3>
                <StatusPill tone="info">{{ config.service_key }}</StatusPill>
                <StatusPill :tone="draftFor(config).enabled ? 'success' : 'neutral'">
                  {{ draftFor(config).enabled ? 'enabled' : 'disabled' }}
                </StatusPill>
                <StatusPill :tone="readinessTone(config)">
                  {{ config.readiness.label }}
                </StatusPill>
                <StatusPill :tone="riskTone(config)">
                  {{ providerCopy(config).risk }} risk
                </StatusPill>
              </div>
              <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
                {{ config.metadata.description }}
              </p>
            </div>

            <label class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold dark:border-slate-800">
              <input
                :checked="draftFor(config).enabled"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                @change="updateEnabled(config, ($event.target as HTMLInputElement).checked)"
              >
              Enable
            </label>
          </div>

          <div class="grid gap-3">
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">What this controls</p>
              <p class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{{ providerCopy(config).controls }}</p>
            </div>
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">When to use</p>
              <p class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{{ providerCopy(config).when }}</p>
            </div>
            <div class="rounded-md border border-amber-200 bg-amber-50 p-4 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
              <div class="flex gap-3">
                <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <p class="text-xs font-semibold uppercase">Impact</p>
                  <p class="mt-2 text-sm leading-6">{{ providerCopy(config).impact }}</p>
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
              Fallback source: {{ config.metadata.runtime_fallback }}
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
        </div>

        <div class="space-y-5">
          <div
            v-if="!config.encryption_available"
            class="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
          >
            Encryption key is not available. Sensitive provider secrets cannot be saved safely.
          </div>

          <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-slate-950 dark:text-white">Public config</p>
                <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">Visible operational values used by the runtime resolver.</p>
              </div>
              <label class="w-28 space-y-1">
                <span class="text-xs font-semibold text-slate-500 dark:text-slate-400">Priority</span>
                <input
                  :value="draftFor(config).priority"
                  type="number"
                  min="1"
                  class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
                  @input="updatePriority(config, Number(($event.target as HTMLInputElement).value || 100))"
                >
              </label>
            </div>

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
                  :value="String(draftFor(config).public_config[field.key] ?? '')"
                  :type="inputType(field)"
                  :min="field.min_value ?? undefined"
                  :max="field.max_value ?? undefined"
                  :inputmode="inputMode(field)"
                  :placeholder="field.placeholder"
                  class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
                  @input="updateField(config, field.key, ($event.target as HTMLInputElement).value)"
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
                  Secrets are write-only. API responses never return plaintext. Leave a secret blank to keep the current encrypted value.
                </p>
              </div>
            </div>

            <div v-if="config.metadata.fields.secret.length" class="mt-4 grid gap-4 md:grid-cols-2">
              <label
                v-for="field in config.metadata.fields.secret"
                :key="`${config.provider_key}-secret-${field.key}`"
                class="space-y-2"
              >
                <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  {{ field.label }}<span v-if="field.required" class="text-rose-500"> *</span>
                </span>
                <input
                  :value="String(draftFor(config).secrets?.[field.key] ?? '')"
                  :type="inputType(field)"
                  :placeholder="field.placeholder || 'Leave blank to keep existing secret'"
                  autocomplete="new-password"
                  class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
                  @input="updateSecret(config, field.key, ($event.target as HTMLInputElement).value)"
                >
                <span class="block text-xs leading-5 text-slate-500 dark:text-slate-400">
                  {{ secretStatusLabel(config, field.key) }}. Blank means unchanged.
                </span>
              </label>
            </div>
            <p v-else class="mt-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              This local provider does not require a secret in the current phase.
            </p>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <AdminActionButton
              tone="neutral"
              :loading="validatingKey === configKey(config)"
              :disabled="Boolean(savingKey)"
              @click="validateDraft(config)"
            >
              <template #icon>
                <TestTube2 class="h-4 w-4" />
              </template>
              Validate
            </AdminActionButton>
            <AdminActionButton
              tone="primary"
              :loading="savingKey === `service-provider:${config.service_key}:${config.provider_key}`"
              :disabled="Boolean(savingKey)"
              @click="saveDraft(config)"
            >
              <template #icon>
                <Save class="h-4 w-4" />
              </template>
              Save {{ config.display_name }}
            </AdminActionButton>
          </div>

          <div
            v-if="saveResults[configKey(config)]"
            class="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100"
          >
            <div class="flex gap-3">
              <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p class="font-semibold">Save submitted</p>
                <p class="mt-1">
                  Changed fields:
                  {{ saveResults[configKey(config)].length ? saveResults[configKey(config)].join(', ') : 'none detected; save refreshes readiness' }}
                </p>
                <p class="mt-1 text-xs">Secret fields are submitted only when the input is non-empty.</p>
              </div>
            </div>
          </div>

          <div
            v-if="validationResults[configKey(config)] || validationErrors[configKey(config)]"
            class="rounded-md border p-4 text-sm leading-6"
            :class="validationResults[configKey(config)]?.valid ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100' : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'"
          >
            <div class="flex items-start gap-3">
              <CheckCircle2 v-if="validationResults[configKey(config)]?.valid" class="mt-0.5 h-4 w-4 shrink-0" />
              <AlertTriangle v-else class="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p class="font-semibold">
                  {{ validationResults[configKey(config)]?.valid ? 'Validation passed' : 'Validation needs attention' }}
                </p>
                <p v-if="validationErrors[configKey(config)]" class="mt-1">{{ validationErrors[configKey(config)] }}</p>
                <p v-if="validationResults[configKey(config)]?.signature_preview_tail" class="mt-1">
                  Signature/local check preview tail {{ validationResults[configKey(config)]?.signature_preview_tail }}
                </p>
                <p v-if="validationResults[configKey(config)]?.checks.length" class="mt-1 text-xs uppercase">
                  {{ validationResults[configKey(config)]?.checks.join(' / ') }}
                </p>
                <ul v-if="validationResults[configKey(config)]?.errors.length" class="mt-2 list-disc pl-5">
                  <li
                    v-for="error in validationResults[configKey(config)]?.errors"
                    :key="`${configKey(config)}-${error}`"
                  >
                    {{ error }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminPanel>
  </div>
</template>
