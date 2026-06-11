<script setup lang="ts">
import { ArrowLeft, Clock3, ShieldCheck, Sparkles } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import Button from '@/components/common/Button.vue'
import HistoryPanel from '@/components/common/HistoryPanel.vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.16),transparent_34%),linear-gradient(135deg,#f8fafc_0%,#eef2ff_44%,#faf5ff_100%)] dark:bg-[radial-gradient(circle_at_top_left,rgba(168,85,247,0.18),transparent_34%),linear-gradient(135deg,#020617_0%,#0f172a_55%,#1e1b4b_100%)]">
    <section class="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <button
        class="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-violet-200 hover:text-violet-700 dark:border-slate-800 dark:bg-slate-900/75 dark:text-slate-200 dark:hover:border-violet-500/40 dark:hover:text-violet-200"
        @click="goHome"
      >
        <ArrowLeft class="h-4 w-4" />
        返回首页
      </button>

      <div class="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
        <div>
          <div class="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/78 px-4 py-2 text-sm font-semibold text-violet-700 shadow-sm dark:border-violet-500/25 dark:bg-violet-500/10 dark:text-violet-200">
            <Clock3 class="h-4 w-4" />
            本机处理记录
          </div>
          <h1 class="mt-5 text-4xl font-black tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            处理记录
          </h1>
          <p class="mt-4 max-w-2xl text-base leading-8 text-slate-600 dark:text-slate-300">
            查看当前浏览器保存的最近 PDF 操作记录。记录只保存在你的设备上，用于快速回看处理过的文件与工具类型。
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-[26px] border border-white/70 bg-white/78 p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/72">
            <ShieldCheck class="h-6 w-6 text-emerald-500" />
            <p class="mt-3 font-semibold text-slate-900 dark:text-white">本地保存</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              不上传历史数据，清理浏览器数据后记录也会消失。
            </p>
          </div>
          <div class="rounded-[26px] border border-white/70 bg-white/78 p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/72">
            <Sparkles class="h-6 w-6 text-violet-500" />
            <p class="mt-3 font-semibold text-slate-900 dark:text-white">快速回看</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              适合确认刚才用了哪个工具、处理了哪些文件。
            </p>
          </div>
        </div>
      </div>

      <div class="mt-8 rounded-[34px] border border-white/75 bg-white/55 p-4 shadow-xl shadow-violet-100/60 backdrop-blur dark:border-slate-800 dark:bg-slate-950/45 dark:shadow-none sm:p-6">
        <HistoryPanel />
      </div>

      <div class="mt-6 flex justify-center">
        <Button
          variant="outline"
          class="rounded-full"
          @click="goHome"
        >
          继续处理 PDF
        </Button>
      </div>
    </section>
  </div>
</template>
