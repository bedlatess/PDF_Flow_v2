<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  CheckCircle2,
  FileStack,
  Gauge,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-vue-next'

import Button from '@/components/common/Button.vue'

const { tm } = useI18n()
const router = useRouter()

interface FeatureCopy {
  heroEyebrow: string
  heroTitle: string
  heroDescription: string
  primaryAction: string
  secondaryAction: string
  pillars: Array<{
    title: string
    body: string
  }>
  workflowTitle: string
  workflowDescription: string
  workflowSteps: string[]
  trustTitle: string
  trustItems: Array<{
    title: string
    body: string
  }>
  ctaTitle: string
  ctaDescription: string
}

const page = computed(() => tm('features.page') as FeatureCopy)

const pillarIcons = [FileStack, Gauge, RefreshCw]
const trustIcons = [ShieldCheck, LockKeyhole, Sparkles]
</script>

<template>
  <div class="bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-white">
    <section class="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div class="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(340px,0.75fr)] lg:px-8 lg:py-16">
        <div class="flex min-w-0 flex-col justify-center">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-blue-600 dark:text-blue-300">
            {{ page.heroEyebrow }}
          </p>
          <h1 class="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-5xl">
            {{ page.heroTitle }}
          </h1>
          <p class="mt-5 max-w-2xl text-base leading-8 text-slate-600 dark:text-slate-300">
            {{ page.heroDescription }}
          </p>
          <div class="mt-7 flex flex-col gap-3 sm:flex-row">
            <Button
              size="lg"
              class="gap-2"
              @click="router.push('/tools')"
            >
              {{ page.primaryAction }}
              <ArrowRight class="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              @click="router.push('/pricing')"
            >
              {{ page.secondaryAction }}
            </Button>
          </div>
        </div>

        <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/70">
          <div class="grid gap-3">
            <div
              v-for="(pillar, index) in page.pillars"
              :key="pillar.title"
              class="rounded-md border border-white bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/70"
            >
              <component :is="pillarIcons[index] ?? CheckCircle2" class="h-5 w-5 text-blue-600 dark:text-blue-300" />
              <h2 class="mt-3 text-base font-semibold text-slate-950 dark:text-white">
                {{ pillar.title }}
              </h2>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ pillar.body }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/40">
      <div class="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[0.8fr_1fr] lg:px-8">
        <div>
          <h2 class="text-3xl font-semibold leading-tight text-slate-950 dark:text-white">
            {{ page.workflowTitle }}
          </h2>
          <p class="mt-4 max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ page.workflowDescription }}
          </p>
        </div>

        <div class="grid gap-3">
          <div
            v-for="(step, index) in page.workflowSteps"
            :key="step"
            class="flex items-start gap-4 rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950/70"
          >
            <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-50 text-sm font-semibold text-blue-700 dark:bg-blue-500/10 dark:text-blue-200">
              {{ index + 1 }}
            </span>
            <p class="pt-1 text-sm leading-6 text-slate-700 dark:text-slate-200">
              {{ step }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="bg-white dark:bg-slate-950">
      <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div class="grid gap-8 lg:grid-cols-[0.8fr_1fr] lg:items-start">
          <h2 class="text-3xl font-semibold leading-tight text-slate-950 dark:text-white">
            {{ page.trustTitle }}
          </h2>

          <div class="grid gap-4 md:grid-cols-3">
            <div
              v-for="(item, index) in page.trustItems"
              :key="item.title"
              class="rounded-md border border-slate-200 p-4 dark:border-slate-800"
            >
              <component :is="trustIcons[index] ?? CheckCircle2" class="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
              <h3 class="mt-3 text-sm font-semibold text-slate-950 dark:text-white">
                {{ item.title }}
              </h3>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ item.body }}
              </p>
            </div>
          </div>
        </div>

        <div class="mt-12 rounded-lg border border-blue-200 bg-blue-50 p-6 dark:border-blue-900/60 dark:bg-blue-950/30 sm:p-8">
          <div class="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-2xl font-semibold text-slate-950 dark:text-white">
                {{ page.ctaTitle }}
              </h2>
              <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                {{ page.ctaDescription }}
              </p>
            </div>
            <Button
              size="lg"
              class="gap-2 md:shrink-0"
              @click="router.push('/tools')"
            >
              {{ page.primaryAction }}
              <ArrowRight class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
