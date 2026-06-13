<script setup lang="ts">
import { Save } from 'lucide-vue-next'
import type { ContentBlock } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'

defineProps<{
  blocks: ContentBlock[]
  selectedContent: ContentBlock | null
  savingKey: string | null
}>()

const emit = defineEmits<{
  select: [block: ContentBlock]
  save: [block: ContentBlock]
}>()
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[280px_1fr]">
    <AdminPanel as="aside" padding="sm">
      <button
        v-for="block in blocks"
        :key="`${block.key}:${block.locale}`"
        type="button"
        class="mb-2 w-full rounded-md px-4 py-3 text-left text-sm transition"
        :class="
          selectedContent?.id === block.id
            ? 'bg-slate-950 text-white dark:bg-emerald-400 dark:text-slate-950'
            : 'text-slate-600 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-300'
        "
        @click="emit('select', block)"
      >
        <span class="block font-semibold">{{ block.title }}</span>
        <span class="mt-1 block text-xs opacity-70">{{ block.key }} / {{ block.locale }}</span>
      </button>
    </AdminPanel>

    <AdminPanel v-if="selectedContent" as="article">
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="text-sm text-slate-600 dark:text-slate-300">
          标题
          <input
            v-model="selectedContent.title"
            type="text"
            class="mt-2 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none focus:border-emerald-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-emerald-400"
          />
        </label>
        <label class="text-sm text-slate-600 dark:text-slate-300">
          语言
          <input
            v-model="selectedContent.locale"
            type="text"
            class="mt-2 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none focus:border-emerald-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-emerald-400"
          />
        </label>
      </div>
      <label class="mt-4 block text-sm text-slate-600 dark:text-slate-300">
        描述
        <input
          v-model="selectedContent.description"
          type="text"
          class="mt-2 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none focus:border-emerald-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-emerald-400"
        />
      </label>
      <label class="mt-4 block text-sm text-slate-600 dark:text-slate-300">
        正文内容
        <textarea
          v-model="selectedContent.content"
          rows="12"
          class="mt-2 w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-950 outline-none focus:border-emerald-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-emerald-400"
        />
      </label>
      <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
        <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input
            v-model="selectedContent.is_public"
            type="checkbox"
            class="rounded border-white/20 bg-white text-emerald-600 dark:bg-slate-900 dark:text-emerald-300"
          />
          可公开读取
        </label>
        <AdminActionButton
          tone="success"
          :disabled="savingKey === `content:${selectedContent.key}:${selectedContent.locale}`"
          :loading="savingKey === `content:${selectedContent.key}:${selectedContent.locale}`"
          @click="emit('save', selectedContent)"
        >
          <template #icon>
            <Save class="h-4 w-4" />
          </template>
          保存内容
        </AdminActionButton>
      </div>
    </AdminPanel>
  </div>
</template>
