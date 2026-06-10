<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ChevronRight,
  Crown,
  LayoutPanelTop,
  Menu,
  Moon,
  Sparkles,
  SunMedium,
  X,
} from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { useUserStore } from '@/stores/user'
import { useSiteConfigStore } from '@/stores/siteConfig'
import Button from '@/components/common/Button.vue'

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const settingsStore = useSettingsStore()
const userStore = useUserStore()
const siteConfigStore = useSiteConfigStore()

const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)

const localeOptions = [
  { value: 'zh', label: '\u7b80\u4f53\u4e2d\u6587' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Espa\u00f1ol' },
] as const

const publicLinks = computed(() => [
  {
    key: 'features',
    label: t('nav.features'),
    route: '/features',
    icon: LayoutPanelTop,
    accent: 'from-violet-500/16 to-fuchsia-500/12 text-violet-700 ring-violet-200/80 dark:text-violet-200 dark:ring-violet-500/20',
    activeAccent: 'from-violet-600 to-fuchsia-500 text-white ring-violet-400/60 shadow-lg shadow-violet-500/25',
  },
  {
    key: 'pricing',
    label: t('nav.pricing'),
    route: '/pricing',
    icon: Crown,
    accent: 'from-sky-500/15 to-cyan-500/12 text-sky-700 ring-sky-200/80 dark:text-sky-200 dark:ring-sky-500/20',
    activeAccent: 'from-sky-500 to-cyan-500 text-white ring-sky-400/60 shadow-lg shadow-sky-500/25',
  },
])

const userInitial = computed(() => {
  const name = userStore.user?.full_name || userStore.user?.email || '?'
  return name.charAt(0).toUpperCase()
})

const brandName = computed(() => siteConfigStore.getSettingValue('site_name', 'PDF-Flow'))

const isRouteActive = (target: string) => route.path === target

const navigateHome = () => {
  router.push('/')
  mobileMenuOpen.value = false
}

const navigateTo = (target: string) => {
  router.push(target)
  mobileMenuOpen.value = false
}

const goToLogin = () => {
  router.push('/auth/login')
  mobileMenuOpen.value = false
}

const goToProfile = () => {
  router.push('/auth/profile')
  userMenuOpen.value = false
  mobileMenuOpen.value = false
}

const handleLogout = async () => {
  await userStore.logout()
  userMenuOpen.value = false
  mobileMenuOpen.value = false
  router.push('/')
}

const toggleTheme = () => {
  const newTheme = settingsStore.theme === 'light' ? 'dark' : 'light'
  settingsStore.setTheme(newTheme)
}

const changeLocale = (newLocale: 'en' | 'zh' | 'es') => {
  settingsStore.setLocale(newLocale)
}

onMounted(() => {
  userStore.checkAuth()
  siteConfigStore.fetchPublicConfig()
})
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-white/60 bg-white/78 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/72">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-20 items-center justify-between gap-4">
        <button
          class="group flex items-center gap-3 rounded-full border border-violet-200/80 bg-white/88 px-3.5 py-2 shadow-sm shadow-violet-100/70 transition hover:-translate-y-0.5 hover:border-violet-300 hover:shadow-lg hover:shadow-violet-200/60 dark:border-violet-500/20 dark:bg-slate-900/80 dark:shadow-none dark:hover:border-violet-400/40"
          @click="navigateHome"
        >
          <div class="relative flex h-11 w-11 items-center justify-center overflow-hidden rounded-[18px] bg-[linear-gradient(155deg,#240046_0%,#5b21b6_52%,#a855f7_100%)] text-white shadow-lg shadow-violet-500/30">
            <div class="absolute inset-[6px] rounded-[13px] border border-white/14 bg-[radial-gradient(circle_at_28%_22%,rgba(255,255,255,0.34),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.08),rgba(255,255,255,0))]" />
            <div class="absolute inset-y-[8px] left-[11px] w-[2.5px] rounded-full bg-white/92 shadow-[0_0_10px_rgba(255,255,255,0.18)]" />
            <svg
              class="relative h-7 w-7"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                d="M9 7.5h3.9c2.15 0 3.6 1.18 3.6 3.02 0 1.9-1.45 3.08-3.6 3.08H9"
                stroke="white"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.75"
              />
              <path
                d="M9 12.4h5.55"
                stroke="white"
                stroke-linecap="round"
                stroke-width="1.75"
              />
              <path
                d="M9 16.55h4.15"
                stroke="white"
                stroke-linecap="round"
                stroke-width="1.75"
              />
            </svg>
            <span class="absolute right-[8px] top-[8px] h-1.5 w-1.5 rounded-full bg-fuchsia-100/90 shadow-[0_0_10px_rgba(255,255,255,0.7)]" />
          </div>

          <div class="text-left">
            <p class="text-base font-semibold tracking-[0.01em] text-slate-950 dark:text-white sm:text-[1.05rem]">
              {{ brandName }}
            </p>
          </div>
        </button>

        <div class="hidden items-center gap-3 md:flex">
          <button
            class="group inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/80 px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-violet-200 hover:text-slate-950 dark:border-slate-800 dark:bg-slate-900/75 dark:text-slate-200 dark:hover:border-violet-400/30 dark:hover:text-white"
            @click="navigateHome"
          >
            <Sparkles class="h-4 w-4 text-violet-500 transition group-hover:rotate-6" />
            {{ t('nav.home') }}
          </button>

          <button
            v-for="link in publicLinks"
            :key="link.key"
            :class="[
              'group inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold ring-1 transition-all',
              isRouteActive(link.route)
                ? ['bg-gradient-to-r', link.activeAccent]
                : ['bg-gradient-to-r shadow-sm hover:-translate-y-0.5 hover:shadow-md', link.accent],
            ]"
            @click="navigateTo(link.route)"
          >
            <component :is="link.icon" class="h-4 w-4" />
            <span>{{ link.label }}</span>
            <ChevronRight class="h-4 w-4 opacity-70 transition group-hover:translate-x-0.5" />
          </button>
        </div>

        <div class="hidden items-center gap-3 md:flex">
          <select
            :value="locale"
            class="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm text-slate-700 outline-none transition hover:border-violet-200 focus:border-violet-400 dark:border-slate-800 dark:bg-slate-900/75 dark:text-slate-100 dark:hover:border-violet-400/30"
            @change="changeLocale(($event.target as HTMLSelectElement).value as 'en' | 'zh' | 'es')"
          >
            <option
              v-for="option in localeOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>

          <button
            class="inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white/80 text-slate-600 shadow-sm transition hover:border-violet-200 hover:text-slate-950 dark:border-slate-800 dark:bg-slate-900/75 dark:text-slate-300 dark:hover:border-violet-400/30 dark:hover:text-white"
            @click="toggleTheme"
          >
            <Moon
              v-if="settingsStore.theme === 'light'"
              class="h-5 w-5"
            />
            <SunMedium
              v-else
              class="h-5 w-5"
            />
          </button>

          <div
            v-if="userStore.isAuthenticated"
            class="relative"
          >
            <button
              class="flex h-11 w-11 items-center justify-center rounded-full bg-[linear-gradient(135deg,#2e1065_0%,#7c3aed_68%,#d8b4fe_100%)] text-sm font-bold text-white shadow-lg shadow-violet-500/20 transition hover:-translate-y-0.5"
              @click="userMenuOpen = !userMenuOpen"
            >
              {{ userInitial }}
            </button>
            <div
              v-if="userMenuOpen"
              class="absolute right-0 mt-3 w-60 rounded-[24px] border border-slate-200/80 bg-white/92 p-2 shadow-2xl shadow-slate-200/70 backdrop-blur dark:border-slate-800 dark:bg-slate-900/92 dark:shadow-none"
            >
              <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
                <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                  {{ userStore.user?.full_name || userStore.user?.email }}
                </p>
              </div>
              <button
                class="mt-2 flex w-full items-center justify-between rounded-2xl px-4 py-3 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800/80"
                @click="goToProfile"
              >
                <span>{{ t('account.myAccount') }}</span>
                <ChevronRight class="h-4 w-4" />
              </button>
              <button
                class="mt-1 flex w-full items-center justify-between rounded-2xl px-4 py-3 text-left text-sm font-medium text-rose-600 transition hover:bg-rose-50 dark:hover:bg-rose-500/10"
                @click="handleLogout"
              >
                <span>{{ t('auth.logout') }}</span>
                <ChevronRight class="h-4 w-4" />
              </button>
            </div>
          </div>

          <Button
            v-else
            variant="primary"
            size="sm"
            class="rounded-full px-5 py-2.5"
            @click="goToLogin"
          >
            {{ t('auth.login') }}
          </Button>
        </div>

        <button
          class="inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white/80 text-slate-700 shadow-sm transition hover:border-violet-200 hover:text-slate-950 dark:border-slate-800 dark:bg-slate-900/75 dark:text-slate-200 dark:hover:border-violet-400/30 dark:hover:text-white md:hidden"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <Menu
            v-if="!mobileMenuOpen"
            class="h-5 w-5"
          />
          <X
            v-else
            class="h-5 w-5"
          />
        </button>
      </div>

      <div
        v-if="mobileMenuOpen"
        class="border-t border-slate-200/80 py-4 dark:border-slate-800 md:hidden"
      >
        <div class="space-y-3">
          <div class="grid gap-3">
            <button
              class="flex items-center justify-between rounded-[24px] border border-slate-200 bg-white/85 px-4 py-3 text-left shadow-sm dark:border-slate-800 dark:bg-slate-900/75"
              @click="navigateHome"
            >
              <span class="flex items-center gap-3 text-sm font-semibold text-slate-800 dark:text-slate-100">
                <Sparkles class="h-4 w-4 text-violet-500" />
                {{ t('nav.home') }}
              </span>
              <ChevronRight class="h-4 w-4 text-slate-400" />
            </button>

            <button
              v-for="link in publicLinks"
              :key="`${link.key}-mobile`"
              :class="[
                'flex items-center justify-between rounded-[24px] px-4 py-3 text-left shadow-sm ring-1 transition',
                isRouteActive(link.route)
                  ? ['bg-gradient-to-r', link.activeAccent]
                  : ['bg-white/85 dark:bg-slate-900/75', link.accent],
              ]"
              @click="navigateTo(link.route)"
            >
              <span class="flex items-center gap-3 text-sm font-semibold">
                <component :is="link.icon" class="h-4 w-4" />
                {{ link.label }}
              </span>
              <ChevronRight class="h-4 w-4 opacity-70" />
            </button>
          </div>

          <div class="grid gap-3 rounded-[28px] border border-slate-200 bg-white/80 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/72">
            <select
              :value="locale"
              class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-violet-400 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-100"
              @change="changeLocale(($event.target as HTMLSelectElement).value as 'en' | 'zh' | 'es')"
            >
              <option
                v-for="option in localeOptions"
                :key="`mobile-${option.value}`"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>

            <button
              class="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-violet-200 dark:border-slate-800 dark:text-slate-200 dark:hover:border-violet-400/30"
              @click="toggleTheme"
            >
              <span>{{ settingsStore.theme === 'light' ? t('nav.themeToDark') : t('nav.themeToLight') }}</span>
              <Moon
                v-if="settingsStore.theme === 'light'"
                class="h-4 w-4"
              />
              <SunMedium
                v-else
                class="h-4 w-4"
              />
            </button>

            <template v-if="userStore.isAuthenticated">
              <button
                class="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-violet-200 dark:border-slate-800 dark:text-slate-200 dark:hover:border-violet-400/30"
                @click="goToProfile"
              >
                <span>{{ t('account.myAccount') }}</span>
                <ChevronRight class="h-4 w-4" />
              </button>
              <button
                class="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50/70 px-4 py-3 text-sm font-medium text-rose-600 transition hover:border-rose-300 dark:border-rose-500/20 dark:bg-rose-500/10"
                @click="handleLogout"
              >
                <span>{{ t('auth.logout') }}</span>
                <ChevronRight class="h-4 w-4" />
              </button>
            </template>
            <Button
              v-else
              variant="primary"
              size="sm"
              full-width
              class="rounded-2xl py-3"
              @click="goToLogin"
            >
              {{ t('auth.login') }}
            </Button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
