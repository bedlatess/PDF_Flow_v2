<script setup lang="ts">
import { computed } from 'vue'
import { Save, Settings2 } from 'lucide-vue-next'
import type { SiteSetting } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  settings: SiteSetting[]
  savingKey: string | null
}>()

const emit = defineEmits<{
  save: [setting: SiteSetting]
}>()

const publicCount = computed(() => props.settings.filter((setting) => setting.is_public).length)
const groupedSettings = computed(() => {
  const groups = new Map<string, SiteSetting[]>()
  for (const setting of props.settings) {
    const group = setting.group || 'general'
    groups.set(group, [...(groups.get(group) ?? []), setting])
  }
  return Array.from(groups.entries()).map(([group, items]) => ({ group, items }))
})
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Product"
        title="Site Settings"
        description="Manage public site configuration and operational display values. Public settings can be read by the frontend, so keep secrets and server-only values out of this module."
        :icon="Settings2"
      >
        <template #badges>
          <StatusPill tone="neutral">{{ settings.length }} settings</StatusPill>
          <StatusPill tone="info">{{ publicCount }} public</StatusPill>
        </template>
      </AdminSectionHeader>

      <AdminStateBlock
        class="mt-5"
        tone="info"
        title="Use for low-risk display configuration"
        description="Changes may affect public copy or presentation immediately after save. Environment-only secrets and provider credentials stay outside this module."
      />
    </AdminPanel>

    <section v-for="group in groupedSettings" :key="group.group" class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h3 class="text-base font-semibold text-slate-950 dark:text-white">{{ group.group }}</h3>
        <StatusPill>{{ group.items.length }} entries</StatusPill>
      </div>

      <div class="grid gap-4 xl:grid-cols-2">
        <AdminPanel v-for="setting in group.items" :key="setting.key" as="article">
          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <h4 class="text-lg font-semibold text-slate-950 dark:text-white">{{ setting.label }}</h4>
                  <StatusPill :tone="setting.is_public ? 'info' : 'neutral'">
                    {{ setting.is_public ? 'Public read' : 'Admin only' }}
                  </StatusPill>
                </div>
                <p class="mt-1 break-all text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {{ setting.key }} - {{ setting.value_type }}
                </p>
                <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ setting.description || 'No description configured yet.' }}
                </p>
              </div>

              <label class="inline-flex min-h-11 items-center justify-between gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:text-slate-200">
                <span>Public</span>
                <input
                  v-model="setting.is_public"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                >
              </label>
            </div>

            <label class="grid gap-2 text-sm">
              <span class="font-semibold text-slate-700 dark:text-slate-200">Value</span>
              <textarea
                v-if="setting.value_type === 'textarea'"
                v-model="setting.value"
                rows="5"
                class="min-h-28 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white"
              />
              <input
                v-else
                v-model="setting.value"
                type="text"
                class="min-h-11 w-full rounded-md border border-slate-200 bg-slate-50 px-4 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white"
              >
            </label>

            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p class="text-xs leading-5 text-slate-500 dark:text-slate-400">
                Last updated {{ setting.updated_at ? new Date(setting.updated_at).toLocaleString() : 'unknown' }}.
              </p>
              <AdminActionButton
                :disabled="savingKey === `setting:${setting.key}`"
                :loading="savingKey === `setting:${setting.key}`"
                @click="emit('save', setting)"
              >
                <template #icon>
                  <Save class="h-4 w-4" />
                </template>
                Save setting
              </AdminActionButton>
            </div>
          </div>
        </AdminPanel>
      </div>
    </section>

    <AdminStateBlock
      v-if="settings.length === 0"
      tone="neutral"
      title="No site settings"
      description="Site settings will appear here after the backend returns the product configuration catalog."
    />
  </div>
</template>
