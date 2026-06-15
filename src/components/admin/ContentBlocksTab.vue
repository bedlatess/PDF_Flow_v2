<script setup lang="ts">
import { computed } from 'vue'
import { FileText, Save } from 'lucide-vue-next'
import type { ContentBlock } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  blocks: ContentBlock[]
  selectedContent: ContentBlock | null
  savingKey: string | null
}>()

const emit = defineEmits<{
  select: [block: ContentBlock]
  save: [block: ContentBlock]
}>()

const publicCount = computed(() => props.blocks.filter((block) => block.is_public).length)
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Product"
        title="Content Blocks"
        description="Edit reusable public copy without a code deploy. Keep content concise and avoid placing secrets, server paths, or operational debug details in public blocks."
        :icon="FileText"
      >
        <template #badges>
          <StatusPill tone="neutral">{{ blocks.length }} blocks</StatusPill>
          <StatusPill tone="info">{{ publicCount }} public</StatusPill>
        </template>
      </AdminSectionHeader>
    </AdminPanel>

    <div class="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
      <AdminPanel as="aside" padding="sm" class="h-fit">
        <div class="mb-3 px-2">
          <p class="text-sm font-semibold text-slate-950 dark:text-white">Blocks</p>
          <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
            Select a locale-specific block to edit.
          </p>
        </div>
        <div class="space-y-2">
          <button
            v-for="block in blocks"
            :key="`${block.key}:${block.locale}`"
            type="button"
            class="w-full rounded-md px-4 py-3 text-left text-sm transition"
            :class="
              selectedContent?.id === block.id
                ? 'bg-slate-950 text-white shadow-sm dark:bg-sky-400 dark:text-slate-950'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
            "
            @click="emit('select', block)"
          >
            <span class="block truncate font-semibold">{{ block.title || block.key }}</span>
            <span class="mt-1 block break-all text-xs opacity-70">{{ block.key }} - {{ block.locale }}</span>
          </button>
        </div>
      </AdminPanel>

      <AdminPanel v-if="selectedContent" as="article" padding="lg">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="text-xl font-semibold text-slate-950 dark:text-white">
                {{ selectedContent.title || selectedContent.key }}
              </h3>
              <StatusPill :tone="selectedContent.is_public ? 'info' : 'neutral'">
                {{ selectedContent.is_public ? 'Public' : 'Hidden' }}
              </StatusPill>
            </div>
            <p class="mt-1 break-all text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {{ selectedContent.key }} - {{ selectedContent.locale }}
            </p>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
              Public content changes may affect landing, tool, or support surfaces immediately after save.
            </p>
          </div>

          <AdminActionButton
            :disabled="savingKey === `content:${selectedContent.key}:${selectedContent.locale}`"
            :loading="savingKey === `content:${selectedContent.key}:${selectedContent.locale}`"
            @click="emit('save', selectedContent)"
          >
            <template #icon>
              <Save class="h-4 w-4" />
            </template>
            Save content
          </AdminActionButton>
        </div>

        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="grid gap-2 text-sm">
            <span class="font-semibold text-slate-700 dark:text-slate-200">Title</span>
            <input
              v-model="selectedContent.title"
              type="text"
              class="min-h-11 rounded-md border border-slate-200 bg-slate-50 px-4 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white"
            >
          </label>
          <label class="grid gap-2 text-sm">
            <span class="font-semibold text-slate-700 dark:text-slate-200">Locale</span>
            <input
              v-model="selectedContent.locale"
              type="text"
              class="min-h-11 rounded-md border border-slate-200 bg-slate-50 px-4 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white"
            >
          </label>
        </div>

        <label class="mt-4 grid gap-2 text-sm">
          <span class="font-semibold text-slate-700 dark:text-slate-200">Description</span>
          <input
            v-model="selectedContent.description"
            type="text"
            class="min-h-11 rounded-md border border-slate-200 bg-slate-50 px-4 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white"
          >
        </label>

        <label class="mt-4 grid gap-2 text-sm">
          <span class="font-semibold text-slate-700 dark:text-slate-200">Content</span>
          <textarea
            v-model="selectedContent.content"
            rows="12"
            class="min-h-72 rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white"
          />
        </label>

        <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <label class="inline-flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:text-slate-200">
            <input
              v-model="selectedContent.is_public"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            >
            Publicly readable
          </label>
          <p class="text-xs leading-5 text-slate-500 dark:text-slate-400">
            Last updated {{ selectedContent.updated_at ? new Date(selectedContent.updated_at).toLocaleString() : 'unknown' }}.
          </p>
        </div>
      </AdminPanel>

      <AdminStateBlock
        v-else
        tone="neutral"
        title="No content block selected"
        description="Choose a block from the list to edit its title, locale, description, and content."
      />
    </div>
  </div>
</template>
