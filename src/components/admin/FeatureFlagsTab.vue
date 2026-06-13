<script setup lang="ts">
import { Save } from 'lucide-vue-next'
import type { FeatureFlag } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'

defineProps<{
  flags: FeatureFlag[]
  savingKey: string | null
}>()

const emit = defineEmits<{
  save: [flag: FeatureFlag]
}>()
</script>

<template>
  <div class="grid gap-4 xl:grid-cols-2">
    <AdminPanel v-for="flag in flags" :key="flag.key" as="article">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-lg font-semibold">{{ flag.label }}</p>
          <p class="mt-1 text-xs uppercase tracking-[0.2em] text-sky-600 dark:text-sky-300/70">
            {{ flag.key }}
          </p>
          <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ flag.description }}
          </p>
        </div>
        <label class="relative inline-flex cursor-pointer items-center">
          <input v-model="flag.enabled" type="checkbox" class="peer sr-only" />
          <span
            class="h-7 w-12 rounded-full bg-slate-300 transition peer-checked:bg-emerald-400 dark:bg-slate-700"
          />
          <span
            class="absolute left-1 h-5 w-5 rounded-full bg-white transition peer-checked:translate-x-5"
          />
        </label>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2">
        <label
          class="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200"
        >
          <input
            v-model="flag.requires_login"
            type="checkbox"
            class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
          />
          需要登录
        </label>
        <label
          class="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200"
        >
          <input
            v-model="flag.requires_pro"
            type="checkbox"
            class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
          />
          需要 Pro
        </label>
      </div>

      <textarea
        v-model="flag.maintenance_message"
        rows="2"
        placeholder="维护提示，留空则使用默认提示"
        class="mt-4 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400 dark:text-white dark:focus:border-sky-400"
      />

      <AdminActionButton
        class="mt-4"
        :disabled="savingKey === `flag:${flag.key}`"
        :loading="savingKey === `flag:${flag.key}`"
        @click="emit('save', flag)"
      >
        <template #icon>
          <Save class="h-4 w-4" />
        </template>
        保存开关
      </AdminActionButton>
    </AdminPanel>
  </div>
</template>
