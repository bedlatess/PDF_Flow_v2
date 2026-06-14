<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { RefreshCw, Save, TestTube2, Wrench } from 'lucide-vue-next'
import type { AdminServiceProviderConfig, AdminServiceProviderFieldMetadata } from '@/admin/api'
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
  validate: [config: AdminServiceProviderConfig]
  'update:service-filter': [value: string]
}>()

const formState = reactive<Record<string, AdminServiceProviderConfig>>({})

const serviceFilters = [
  { key: 'all', label: 'All' },
  { key: 'ocr', label: 'OCR' },
  { key: 'office', label: 'Office' },
  { key: 'ai', label: 'AI' },
]

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
</script>

<template>
  <div class="space-y-5">
    <AdminPanel class="overflow-hidden">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            <Wrench class="h-4 w-4" />
            Service Providers
          </div>
          <h3 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
            OCR / Office / AI Provider Center
          </h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Manage runtime provider configuration from the admin console. Database settings are used first; disabled, missing, or incomplete configs fall back to the existing server settings.
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
    </AdminPanel>

    <AdminPanel
      v-for="config in visibleConfigs"
      :key="`${config.service_key}:${config.provider_key}`"
      as="section"
      padding="lg"
    >
      <template #default>
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="text-lg font-semibold text-slate-950 dark:text-white">
                {{ config.display_name }}
              </h3>
              <StatusPill tone="info">
                {{ config.service_key }}
              </StatusPill>
              <StatusPill :tone="draftFor(config).enabled ? 'success' : 'neutral'">
                {{ draftFor(config).enabled ? 'enabled' : 'disabled' }}
              </StatusPill>
              <StatusPill :tone="config.readiness.status === 'ready' ? 'success' : 'warning'">
                {{ config.readiness.label }}
              </StatusPill>
            </div>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              {{ config.metadata.description }}
            </p>
            <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Fallback: {{ config.metadata.runtime_fallback }}
            </p>
          </div>

          <label class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold dark:border-slate-800">
            <input
              :checked="draftFor(config).enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
              @change="updateEnabled(config, ($event.target as HTMLInputElement).checked)"
            >
            Enable {{ config.display_name }}
          </label>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <StatusPill
            v-for="check in config.readiness.validation_checks"
            :key="`${config.provider_key}-check-${check}`"
            tone="info"
          >
            {{ check }}
          </StatusPill>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-[minmax(0,160px)_minmax(0,1fr)]">
          <label class="space-y-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">Priority</span>
            <input
              :value="draftFor(config).priority"
              type="number"
              min="1"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
              @input="updatePriority(config, Number(($event.target as HTMLInputElement).value || 100))"
            >
          </label>

          <div class="grid gap-4 md:grid-cols-2">
            <label
              v-for="field in config.metadata.fields.public"
              :key="`${config.provider_key}-${field.key}`"
              class="space-y-2"
            >
              <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">
                {{ field.label }}
                <span
                  v-if="field.required"
                  class="text-rose-500"
                >
                  *
                </span>
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
              <span
                v-if="field.help_text"
                class="block text-xs leading-5 text-slate-500 dark:text-slate-400"
              >
                {{ field.help_text }}
              </span>
            </label>

            <label
              v-for="field in config.metadata.fields.secret"
              :key="`${config.provider_key}-secret-${field.key}`"
              class="space-y-2"
            >
              <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">
                {{ field.label }}
                <span
                  v-if="field.required"
                  class="text-rose-500"
                >
                  *
                </span>
              </span>
              <input
                :value="String(draftFor(config).secrets?.[field.key] ?? '')"
                :type="inputType(field)"
                :placeholder="field.placeholder"
                autocomplete="new-password"
                class="min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
                @input="updateSecret(config, field.key, ($event.target as HTMLInputElement).value)"
              >
              <span class="block text-xs leading-5 text-slate-500 dark:text-slate-400">
                {{ secretStatusLabel(config, field.key) }}. Leave blank to keep the existing value.
              </span>
              <span
                v-if="field.help_text"
                class="block text-xs leading-5 text-slate-500 dark:text-slate-400"
              >
                {{ field.help_text }}
              </span>
            </label>
          </div>
        </div>

        <div
          v-if="config.readiness.missing_config_keys.length"
          class="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
        >
          Missing or invalid: {{ config.readiness.missing_config_keys.join(', ') }}
        </div>

        <div class="mt-5 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <AdminActionButton
            tone="neutral"
            :loading="savingKey === `service-provider:${config.service_key}:${config.provider_key}:validate`"
            :disabled="Boolean(savingKey)"
            @click="emit('validate', draftFor(config))"
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
            @click="emit('save', draftFor(config))"
          >
            <template #icon>
              <Save class="h-4 w-4" />
            </template>
            Save {{ config.display_name }}
          </AdminActionButton>
        </div>
      </template>
    </AdminPanel>
  </div>
</template>
