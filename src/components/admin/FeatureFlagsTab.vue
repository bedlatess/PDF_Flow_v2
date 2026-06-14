<script setup lang="ts">
import { computed, ref } from 'vue'
import { Save, Search, SlidersHorizontal } from 'lucide-vue-next'
import type { FeatureFlag } from '@/admin/api'
import { pdfTools, toolCategories, type ToolCategory } from '@/data/pdfTools'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'

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
  organize: '整理与编排',
  convert: '转换',
  optimize: '优化',
  secure: '安全与签署',
  extract: '提取',
  advanced: '高级能力',
  other: '其他功能',
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
  { label: '公开展示', value: flagsWithMeta.value.filter((flag) => flag.enabled && flag.is_public).length },
  { label: '可使用', value: flagsWithMeta.value.filter((flag) => flag.enabled).length },
  { label: '需登录', value: flagsWithMeta.value.filter((flag) => flag.requires_login).length },
  { label: '需 Pro', value: flagsWithMeta.value.filter((flag) => flag.requires_pro).length },
])

const accessLabel = (flag: FeatureFlagWithMeta) => {
  if (!flag.enabled) return '已停用'
  if (flag.requires_pro) return 'Pro'
  if (flag.requires_login) return '登录'
  return '公开'
}
</script>

<template>
  <div class="space-y-5">
    <AdminPanel>
      <div class="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            <SlidersHorizontal class="h-4 w-4" />
            Tools & Features
          </div>
          <h3 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
            工具可见性与访问控制
          </h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            后台统一控制工具是否出现在公开入口、是否可用、是否需要登录或 Pro，以及停用时展示的维护提示。
          </p>
        </div>

        <div class="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:min-w-[460px]">
          <div
            v-for="stat in stats"
            :key="stat.label"
            class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <p class="text-lg font-semibold text-slate-950 dark:text-white">{{ stat.value }}</p>
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ stat.label }}</p>
          </div>
        </div>
      </div>

      <label class="relative mt-4 block">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          v-model="query"
          type="search"
          placeholder="搜索工具、feature key 或路由"
          class="h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
        >
      </label>
    </AdminPanel>

    <section
      v-for="group in groupedFlags"
      :key="group.category"
      class="space-y-3"
    >
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-base font-semibold text-slate-950 dark:text-white">{{ group.label }}</h3>
        <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {{ group.flags.length }}
        </span>
      </div>

      <div class="grid gap-3 xl:grid-cols-2">
        <AdminPanel
          v-for="flag in group.flags"
          :key="flag.key"
          as="article"
        >
          <div class="flex flex-col gap-4">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-lg font-semibold text-slate-950 dark:text-white">{{ flag.label }}</p>
                  <span
                    class="rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="
                      flag.enabled
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200'
                        : 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200'
                    "
                  >
                    {{ accessLabel(flag) }}
                  </span>
                </div>
                <p class="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-sky-600 dark:text-sky-300/70">
                  {{ flag.key }}
                </p>
                <p
                  v-if="flag.route"
                  class="mt-1 text-xs text-slate-500 dark:text-slate-400"
                >
                  {{ flag.route }} · {{ flag.mode }}
                </p>
                <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {{ flag.description || '暂无描述' }}
                </p>
              </div>
            </div>

            <div class="grid gap-2 sm:grid-cols-2">
              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">公开显示</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">Home / Tools / Footer 入口</span>
                </span>
                <input
                  v-model="flag.is_public"
                  type="checkbox"
                  class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
                >
              </label>

              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">允许使用</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">路由与后端接口保护</span>
                </span>
                <input
                  v-model="flag.enabled"
                  type="checkbox"
                  class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
                >
              </label>

              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">需要登录</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">未登录跳转登录页</span>
                </span>
                <input
                  v-model="flag.requires_login"
                  type="checkbox"
                  class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
                >
              </label>

              <label class="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-950/45 dark:text-slate-200">
                <span>
                  <span class="block font-semibold">需要 Pro</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">未授权跳转定价页</span>
                </span>
                <input
                  v-model="flag.requires_pro"
                  type="checkbox"
                  class="rounded border-white/20 bg-white text-sky-600 dark:bg-slate-900 dark:text-sky-300"
                >
              </label>
            </div>

            <textarea
              v-model="flag.maintenance_message"
              rows="2"
              placeholder="维护提示，留空则使用默认停用提示"
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
              保存工具配置
            </AdminActionButton>
          </div>
        </AdminPanel>
      </div>
    </section>
  </div>
</template>
