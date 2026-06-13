<script setup lang="ts">
import { Save } from 'lucide-vue-next'
import type { SiteSetting } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'

defineProps<{
  settings: SiteSetting[]
  savingKey: string | null
}>()

const emit = defineEmits<{
  save: [setting: SiteSetting]
}>()
</script>

<template>
  <div class="grid gap-4">
    <AdminPanel v-for="setting in settings" :key="setting.key" as="article">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="text-lg font-semibold">{{ setting.label }}</p>
          <p class="mt-1 text-xs uppercase tracking-[0.2em] text-sky-600 dark:text-sky-300/70">
            {{ setting.group }} / {{ setting.key }}
          </p>
          <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ setting.description }}
          </p>
        </div>
        <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input
            v-model="setting.is_public"
            type="checkbox"
            class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
          />
          可公开读取
        </label>
      </div>

      <textarea
        v-if="setting.value_type === 'textarea'"
        v-model="setting.value"
        rows="4"
        class="mt-4 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
      />
      <input
        v-else
        v-model="setting.value"
        type="text"
        class="mt-4 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
      />

      <AdminActionButton
        class="mt-4"
        :disabled="savingKey === `setting:${setting.key}`"
        :loading="savingKey === `setting:${setting.key}`"
        @click="emit('save', setting)"
      >
        <template #icon>
          <Save class="h-4 w-4" />
        </template>
        保存配置
      </AdminActionButton>
    </AdminPanel>
  </div>
</template>
