<script setup lang="ts">
import { computed, ref } from 'vue'
import { Save, Search, SlidersHorizontal } from 'lucide-vue-next'
import type { FeatureFlag } from '@/admin/api'
import { pdfTools, toolCategories, type ToolCategory } from '@/data/pdfTools'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  flags: FeatureFlag[]
  savingKey: string | null
}>()

const emit = defineEmits<{
  save: [flag: FeatureFlag]
}>()

type FeatureFlagWithMeta = FeatureFlag & {
  category: ToolCategory | 'other'
  route: string | null
  mode: string
}

const categoryLabels: Record<ToolCategory | 'other', string> = {
  organize: 'Organize & Edit',
  convert: 'Convert',
  optimize: 'Optimize',
  secure: 'Security & Signing',
  extract: 'Extract',
  advanced: 'Advanced',
  other: 'Other',
}

const query = ref('')

const toolByFeatureKey = computed(() =>
  Object.fromEntries(pdfTools.map((tool) => [tool.featureKey, tool])),
)

const flagsWithMeta = computed<FeatureFlagWithMeta[]>(() =>
  props.flags.map((flag) => {
    const tool = toolByFeatureKey.value[flag.key]
    return {
      ...flag,
      category: tool?.category ?? 'other',
      route: tool?.route ?? null,
      mode: tool?.mode ?? 'system',
    }
  }),
)

const normalizedQuery = computed(() => query.value.trim().toLowerCase())

const filteredFlags = computed(() =>
  flagsWithMeta.value.filter((flag) => {
    if (!normalizedQuery.value) return true
    return [
      flag.key,
      flag.label,
      flag.description || '',
      flag.route || '',
      categoryLabels[flag.category],
    ]
      .join(' ')
      .toLowerCase()
      .includes(normalizedQuery.value)
  }),
)

const groupedFlags = computed(() => {
  const order: Array<ToolCategory | 'other'> = [...toolCategories, 'other']
  return order
    .map((category) => ({
      category,
      label: categoryLabels[category],
      flags: filteredFlags.value.filter((flag) => flag.category === category),
    }))
    .filter((group) => group.flags.length > 0)
})

const stats = computed(() => [
  { label: 'Public', value: flagsWithMeta.value.filter((flag) => flag.enabled && flag.is_public).length, tone: 'info' as const },
  { label: 'Enabled', value: flagsWithMeta.value.filter((flag) => flag.enabled).length, tone: 'success' as const },
  { label: 'Login gated', value: flagsWithMeta.value.filter((flag) => flag.requires_login).length, tone: 'warning' as const },
  { label: 'Pro gated', value: flagsWithMeta.value.filter((flag) => flag.requires_pro).length, tone: 'warning' as const },
])

const accessLabel = (flag: FeatureFlagWithMeta) => {
  if (!flag.enabled) return 'Disabled'
  if (flag.requires_pro) return 'Pro'
  if (flag.requires_login) return 'Login'
  return 'Public'
}

const limitFields = [
  { key: 'free_daily_limit', label: 'Free daily', hint: 'Conversions per day' },
  { key: 'free_max_file_size_mb', label: 'Free size', hint: 'MB per file' },
  { key: 'free_batch_file_limit', label: 'Free batch', hint: 'Files per batch' },
  { key: 'pro_daily_limit', label: 'Pro daily', hint: 'Conversions per day' },
  { key: 'pro_max_file_size_mb', label: 'Pro size', hint: 'MB per file' },
  { key: 'pro_batch_file_limit', label: 'Pro batch', hint: 'Files per batch' },
] as const
</script>

<template>
  <div class="space-y-5">
    <AdminPanel padding="lg">
      <AdminSectionHeader
        eyebrow="Product"
        title="Tools & Features"
        description="Control tool visibility, enabled state, login requirement, Pro gates, and maintenance copy from one module. Public visibility controls discovery; enabled controls actual access."
        :icon="SlidersHorizontal"
      />

      <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <AdminStateBlock
          v-for="stat in stats"
          :key="stat.label"
          :tone="stat.tone"
          compact
          :title="stat.label"
          :description="`${stat.value} tools`"
        />
      </div>

      <label class="relative mt-4 block">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          v-model="query"
          type="search"
          placeholder="Search tool, feature key, route, or category"
          class="min-h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
        >
      </label>
    </AdminPanel>

    <section v-for="group in groupedFlags" :key="group.category" class="space-y-3">
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-base font-semibold text-slate-950 dark:text-white">{{ group.label }}</h3>
        <StatusPill>{{ group.flags.length }} tools</StatusPill>
      </div>

      <div class="grid gap-3 xl:grid-cols-2">
        <AdminPanel v-for="flag in group.flags" :key="flag.key" as="article">
          <div class="flex flex-col gap-4">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-lg font-semibold text-slate-950 dark:text-white">{{ flag.label }}</p>
                  <StatusPill
                    :tone="
                      !flag.enabled
                        ? 'danger'
                        : flag.requires_pro || flag.requires_login
                          ? 'warning'
                          : 'success'
                    "
                  >
                    {{ accessLabel(flag) }}
                  </StatusPill>
                </div>
                <p class="mt-1 break-all text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-300/70">
                  {{ flag.key }}
                </p>
                <p v-if="flag.route" class="mt-1 break-all text-xs text-slate-500 dark:text-slate-400">
                  {{ flag.route }} · {{ flag.mode }}
                </p>
                <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ flag.description || 'No description configured yet.' }}
                </p>
              </div>
            </div>

            <div class="grid gap-2 sm:grid-cols-2">
              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">Public display</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">Home / Tools / Footer entries</span>
                </span>
                <input v-model="flag.is_public" type="checkbox" class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300">
              </label>

              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">Enabled</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">Route and backend access</span>
                </span>
                <input v-model="flag.enabled" type="checkbox" class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300">
              </label>

              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">Require login</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">Unauthenticated users sign in</span>
                </span>
                <input v-model="flag.requires_login" type="checkbox" class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300">
              </label>

              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">Require Pro</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">Non-Pro users see Pricing</span>
                </span>
                <input v-model="flag.requires_pro" type="checkbox" class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300">
              </label>
            </div>

            <div class="grid gap-2 sm:grid-cols-2">
              <label
                v-for="field in limitFields"
                :key="field.key"
                class="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200"
              >
                <span class="block font-semibold">{{ field.label }}</span>
                <span class="block text-xs text-slate-500 dark:text-slate-400">{{ field.hint }}</span>
                <input
                  v-model.number="(flag as any)[field.key]"
                  type="number"
                  min="0"
                  class="mt-2 w-full rounded border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                >
              </label>
              <label class="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span class="block font-semibold">Pro unlimited</span>
                <span class="block text-xs text-slate-500 dark:text-slate-400">Ignore Pro quota caps</span>
                <input v-model="flag.pro_unlimited" type="checkbox" class="mt-3 rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300">
              </label>
            </div>

            <textarea
              v-model="flag.maintenance_message"
              rows="2"
              placeholder="Maintenance message. Leave blank to use the default disabled notice."
              class="w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
            />

            <AdminActionButton
              :disabled="savingKey === `flag:${flag.key}`"
              :loading="savingKey === `flag:${flag.key}`"
              @click="emit('save', flag)"
            >
              <template #icon>
                <Save class="h-4 w-4" />
              </template>
              Save tool config
            </AdminActionButton>
          </div>
        </AdminPanel>
      </div>
    </section>

    <AdminStateBlock
      v-if="!groupedFlags.length"
      tone="neutral"
      title="No matching tools"
      description="Clear the search field to return to the full tool list."
    />
  </div>
</template>
