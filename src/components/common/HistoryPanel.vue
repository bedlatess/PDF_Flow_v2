<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  formatHistoryTime,
  formatToolType,
  historyManager,
  type HistoryItem,
} from '@/utils/history-manager'
import { formatFileSize } from '@/utils/file-validator'
import Button from '@/components/common/Button.vue'

const history = ref<HistoryItem[]>([])
const stats = computed(() => historyManager.getStats(history.value))

const loadHistory = () => {
  history.value = historyManager.getHistory()
}

const removeItem = (id: string) => {
  historyManager.removeHistory(id)
  loadHistory()
}

const clearAll = () => {
  if (confirm('确定要清除所有历史记录吗？')) {
    historyManager.clearHistory()
    loadHistory()
  }
}

onMounted(loadHistory)

const groupedHistory = computed(() => {
  const today: HistoryItem[] = []
  const yesterday: HistoryItem[] = []
  const older: HistoryItem[] = []

  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)
  const yesterdayStart = new Date(todayStart)
  yesterdayStart.setDate(yesterdayStart.getDate() - 1)

  history.value.forEach((item) => {
    if (item.timestamp >= todayStart.getTime()) {
      today.push(item)
    } else if (item.timestamp >= yesterdayStart.getTime()) {
      yesterday.push(item)
    } else {
      older.push(item)
    }
  })

  return { today, yesterday, older }
})

const getToolIcon = (type: HistoryItem['type']) => {
  const icons: Record<HistoryItem['type'], string> = {
    merge: 'M',
    split: 'S',
    rotate: 'R',
    compress: 'C',
    imageToPdf: 'I',
    pdfToImage: 'P',
    deletePages: 'D',
    organize: 'O',
    pageNumbers: '#',
    crop: 'C',
    protect: 'L',
    unlock: 'U',
    sign: 'S',
    extractText: 'T',
    extractImages: 'I',
    watermark: 'W',
  }
  return icons[type]
}

const getToolColor = (type: HistoryItem['type']) => {
  const colors: Record<HistoryItem['type'], string> = {
    merge: 'bg-blue-500',
    split: 'bg-emerald-500',
    rotate: 'bg-violet-500',
    compress: 'bg-indigo-500',
    imageToPdf: 'bg-orange-500',
    pdfToImage: 'bg-rose-500',
    deletePages: 'bg-red-500',
    organize: 'bg-emerald-500',
    pageNumbers: 'bg-blue-500',
    crop: 'bg-lime-500',
    protect: 'bg-slate-700',
    unlock: 'bg-emerald-600',
    sign: 'bg-amber-500',
    extractText: 'bg-cyan-500',
    extractImages: 'bg-rose-500',
    watermark: 'bg-cyan-500',
  }
  return colors[type]
}

const historyGroups = computed(() => [
  { key: 'today', label: '今天', items: groupedHistory.value.today },
  { key: 'yesterday', label: '昨天', items: groupedHistory.value.yesterday },
  { key: 'older', label: '更早', items: groupedHistory.value.older },
])
</script>

<template>
  <div class="history-panel">
    <div
      v-if="history.length > 0"
      class="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4"
    >
      <div class="rounded-[24px] border border-white/70 bg-white/90 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/85">
        <p class="text-sm text-slate-500 dark:text-slate-400">总文件</p>
        <p class="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
          {{ stats.totalFiles }}
        </p>
      </div>

      <div class="rounded-[24px] border border-white/70 bg-white/90 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/85">
        <p class="text-sm text-slate-500 dark:text-slate-400">今日处理</p>
        <p class="mt-1 text-2xl font-bold text-violet-600 dark:text-violet-300">
          {{ stats.todayFiles }}
        </p>
      </div>

      <div class="rounded-[24px] border border-white/70 bg-white/90 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/85">
        <p class="text-sm text-slate-500 dark:text-slate-400">最常用</p>
        <p class="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
          {{ stats.mostUsedTool ? formatToolType(stats.mostUsedTool) : '暂无' }}
        </p>
      </div>

      <div class="rounded-[24px] border border-white/70 bg-white/90 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/85">
        <p class="text-sm text-slate-500 dark:text-slate-400">节省空间</p>
        <p class="mt-1 text-sm font-bold text-emerald-600 dark:text-emerald-300">
          {{ stats.totalSaved ? formatFileSize(stats.totalSaved) : '暂无' }}
        </p>
      </div>
    </div>

    <div
      v-if="history.length === 0"
      class="rounded-[28px] border border-dashed border-slate-300 bg-white/82 p-10 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900/72"
    >
      <svg
        class="mx-auto h-12 w-12 text-violet-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="mt-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
        暂无历史记录
      </p>
      <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">
        处理 PDF 文件后，最近操作会保存在当前浏览器里，方便你回看文件名、工具类型和处理时间。
      </p>
    </div>

    <div
      v-else
      class="space-y-6"
    >
      <div
        v-for="group in historyGroups"
        v-show="group.items.length > 0"
        :key="group.key"
      >
        <h3 class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
          {{ group.label }}
        </h3>

        <div class="space-y-2">
          <div
            v-for="item in group.items"
            :key="item.id"
            class="group flex items-center gap-3 rounded-[22px] border border-white/70 bg-white/90 p-3 transition-all hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/85"
          >
            <div :class="['flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg text-white', getToolColor(item.type)]">
              <span class="text-xl font-bold">{{ getToolIcon(item.type) }}</span>
            </div>

            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-slate-900 dark:text-white">
                {{ item.fileName }}
              </p>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                {{ formatToolType(item.type) }} · {{ formatHistoryTime(item.timestamp) }}
              </p>
            </div>

            <button
              class="rounded-full p-2 opacity-70 transition hover:bg-rose-50 hover:opacity-100 group-hover:opacity-100 dark:hover:bg-rose-500/10"
              aria-label="删除这条历史记录"
              @click="removeItem(item.id)"
            >
              <svg
                class="h-5 w-5 text-slate-400 hover:text-rose-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="pt-4">
        <Button
          variant="ghost"
          size="sm"
          full-width
          @click="clearAll"
        >
          清除所有历史记录
        </Button>
      </div>
    </div>
  </div>
</template>
