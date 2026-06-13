<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ChevronRight,
  Crown,
  Clock3,
  LayoutPanelTop,
  Menu,
  Moon,
  Sparkles,
  SunMedium,
  Wrench,
  X,
} from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { useUserStore } from '@/stores/user'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { localeRegistry, withLocalePrefix, type SupportedLocale } from '@/locales/registry'
import Button from '@/components/common/Button.vue'

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const settingsStore = useSettingsStore()
const userStore = useUserStore()
const siteConfigStore = useSiteConfigStore()

const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)
const mobileMenuId = 'mobile-navigation-menu'
const accountMenuId = 'account-navigation-menu'

const localeOptions = localeRegistry

const publicLinks = computed(() => [
  {
    key: 'tools',
    label: t('nav.tools'),
    route: '/tools',
    icon: Wrench,
  },
  {
    key: 'features',
    label: t('nav.features'),
    route: '/features',
    icon: LayoutPanelTop,
  },
  {
    key: 'pricing',
    label: t('nav.pricing'),
    route: '/pricing',
    icon: Crown,
  },
])

const userInitial = computed(() => {
  const name = userStore.user?.full_name || userStore.user?.email || '?'
  return name.charAt(0).toUpperCase()
})

const brandName = computed(() => siteConfigStore.getSettingValue('site_name', 'PDF-Flow'))
const mobileMenuLabel = computed(() =>
  mobileMenuOpen.value ? t('nav.closeMenu') : t('nav.openMenu')
)

const isRouteActive = (target: string) =>
  target === '/tools'
    ? route.path === localizedPath(target) || route.path.startsWith(`${localizedPath(target)}/`)
    : route.path === localizedPath(target)

const localizedPath = (target: string, targetLocale = settingsStore.locale) =>
  withLocalePrefix(target, targetLocale)

const navigateHome = () => {
  router.push(localizedPath('/'))
  mobileMenuOpen.value = false
}

const navigateTo = (target: string) => {
  router.push(localizedPath(target))
  mobileMenuOpen.value = false
}

const closeMenus = () => {
  mobileMenuOpen.value = false
  userMenuOpen.value = false
}

const goToLogin = () => {
  router.push(localizedPath('/auth/login'))
  mobileMenuOpen.value = false
}

const goToProfile = () => {
  router.push(localizedPath('/auth/profile'))
  userMenuOpen.value = false
  mobileMenuOpen.value = false
}

const goToHistory = () => {
  router.push(localizedPath('/history'))
  userMenuOpen.value = false
  mobileMenuOpen.value = false
}

const handleLogout = async () => {
  await userStore.logout()
  userMenuOpen.value = false
  mobileMenuOpen.value = false
  router.push(localizedPath('/'))
}

const toggleTheme = () => {
  const newTheme = settingsStore.theme === 'light' ? 'dark' : 'light'
  settingsStore.setTheme(newTheme)
}

const changeLocale = (newLocale: SupportedLocale) => {
  settingsStore.setLocale(newLocale)
  router.push(localizedPath(route.path, newLocale))
}

onMounted(() => {
  userStore.checkAuth()
  siteConfigStore.fetchPublicConfig()
})
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-white/60 bg-white/78 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/72">
    <div
      class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8"
      @keydown.esc="closeMenus"
    >
      <div class="flex h-20 items-center justify-between gap-4">
        <button
          class="group flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3.5 py-2 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
          :aria-label="brandName"
          @click="navigateHome"
        >
          <div class="relative flex h-11 w-11 items-center justify-center overflow-hidden rounded-lg bg-slate-950 text-white dark:bg-sky-500">
            <div class="absolute inset-[6px] rounded-md border border-white/14 bg-white/5" />
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
          </div>

          <div class="text-left">
            <p class="text-base font-semibold tracking-[0.01em] text-slate-950 dark:text-white sm:text-[1.05rem]">
              {{ brandName }}
            </p>
          </div>
        </button>

        <nav
          class="hidden items-center gap-3 md:flex"
          :aria-label="t('nav.primaryNavigation')"
        >
          <button
            class="group inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
            @click="navigateHome"
          >
            <Sparkles class="h-4 w-4 text-sky-600 dark:text-sky-300" />
            {{ t('nav.home') }}
          </button>

          <button
            v-for="link in publicLinks"
            :key="link.key"
            :class="[
              'group inline-flex items-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold ring-1 transition-all',
              isRouteActive(link.route)
                ? 'bg-slate-950 text-white ring-slate-950 dark:bg-sky-500 dark:ring-sky-500'
                : 'bg-white text-slate-700 shadow-sm ring-slate-200 hover:border-sky-200 hover:text-sky-700 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-800 dark:hover:text-sky-300',
            ]"
            @click="navigateTo(link.route)"
          >
            <component :is="link.icon" class="h-4 w-4" />
            <span>{{ link.label }}</span>
            <ChevronRight class="h-4 w-4 opacity-70 transition group-hover:translate-x-0.5" />
          </button>
        </nav>

        <div class="hidden items-center gap-3 md:flex">
          <select
            :value="locale"
            class="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 outline-none transition hover:border-sky-200 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:border-sky-500/40"
            :aria-label="t('nav.language')"
            @change="changeLocale(($event.target as HTMLSelectElement).value as SupportedLocale)"
          >
            <option
              v-for="option in localeOptions"
              :key="option.id"
              :value="option.id"
            >
              {{ option.label }}
            </option>
          </select>

          <button
            class="inline-flex h-11 w-11 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
            :aria-label="settingsStore.theme === 'light' ? t('nav.themeToDark') : t('nav.themeToLight')"
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
              class="flex h-11 w-11 items-center justify-center rounded-md bg-slate-950 text-sm font-bold text-white shadow-sm transition hover:bg-sky-700 dark:bg-sky-500 dark:hover:bg-sky-400"
              :aria-label="t('account.myAccount')"
              :aria-controls="accountMenuId"
              :aria-expanded="userMenuOpen"
              aria-haspopup="menu"
              @click="userMenuOpen = !userMenuOpen"
            >
              {{ userInitial }}
            </button>
            <div
              v-if="userMenuOpen"
              :id="accountMenuId"
              role="menu"
              class="absolute right-0 mt-3 w-60 rounded-lg border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-800 dark:bg-slate-900"
            >
              <div class="rounded-md bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
                <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                  {{ userStore.user?.full_name || userStore.user?.email }}
                </p>
              </div>
              <button
                role="menuitem"
                class="mt-2 flex w-full items-center justify-between rounded-md px-4 py-3 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800/80"
                @click="goToProfile"
              >
                <span>{{ t('account.myAccount') }}</span>
                <ChevronRight class="h-4 w-4" />
              </button>
              <button
                role="menuitem"
                class="mt-1 flex w-full items-center justify-between rounded-md px-4 py-3 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800/80"
                @click="goToHistory"
              >
                <span class="inline-flex items-center gap-2">
                  <Clock3 class="h-4 w-4 text-sky-600 dark:text-sky-300" />
                  {{ t('history.title') }}
                </span>
                <ChevronRight class="h-4 w-4" />
              </button>
              <button
                role="menuitem"
                class="mt-1 flex w-full items-center justify-between rounded-md px-4 py-3 text-left text-sm font-medium text-rose-600 transition hover:bg-rose-50 dark:hover:bg-rose-500/10"
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
            class="rounded-md px-5 py-2.5"
            @click="goToLogin"
          >
            {{ t('auth.login') }}
          </Button>
        </div>

        <button
          class="inline-flex h-11 w-11 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300 md:hidden"
          :aria-label="mobileMenuLabel"
          :aria-controls="mobileMenuId"
          :aria-expanded="mobileMenuOpen"
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
        :id="mobileMenuId"
        class="border-t border-slate-200/80 py-4 dark:border-slate-800 md:hidden"
      >
        <div class="space-y-3">
          <div class="grid gap-3">
            <button
              class="flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-3 text-left shadow-sm dark:border-slate-800 dark:bg-slate-900"
              @click="navigateHome"
            >
              <span class="flex items-center gap-3 text-sm font-semibold text-slate-800 dark:text-slate-100">
                <Sparkles class="h-4 w-4 text-sky-600 dark:text-sky-300" />
                {{ t('nav.home') }}
              </span>
              <ChevronRight class="h-4 w-4 text-slate-400" />
            </button>

            <button
              v-for="link in publicLinks"
              :key="`${link.key}-mobile`"
              :class="[
                'flex items-center justify-between rounded-md px-4 py-3 text-left shadow-sm ring-1 transition',
                isRouteActive(link.route)
                  ? 'bg-slate-950 text-white ring-slate-950 dark:bg-sky-500 dark:ring-sky-500'
                  : 'bg-white text-slate-700 ring-slate-200 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-800',
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

          <div class="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <select
              :value="locale"
              class="rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-100"
              :aria-label="t('nav.language')"
              @change="changeLocale(($event.target as HTMLSelectElement).value as SupportedLocale)"
            >
              <option
              v-for="option in localeOptions"
                :key="`mobile-${option.id}`"
                :value="option.id"
              >
                {{ option.label }}
              </option>
            </select>

            <button
              class="flex items-center justify-between rounded-md border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-sky-200 dark:border-slate-800 dark:text-slate-200 dark:hover:border-sky-500/40"
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
                class="flex items-center justify-between rounded-md border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-sky-200 dark:border-slate-800 dark:text-slate-200 dark:hover:border-sky-500/40"
                @click="goToProfile"
              >
                <span>{{ t('account.myAccount') }}</span>
                <ChevronRight class="h-4 w-4" />
              </button>
              <button
                class="flex items-center justify-between rounded-md border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-sky-200 dark:border-slate-800 dark:text-slate-200 dark:hover:border-sky-500/40"
                @click="goToHistory"
              >
                <span class="inline-flex items-center gap-2">
                  <Clock3 class="h-4 w-4 text-sky-600 dark:text-sky-300" />
                  {{ t('history.title') }}
                </span>
                <ChevronRight class="h-4 w-4" />
              </button>
              <button
                class="flex items-center justify-between rounded-md border border-rose-200 bg-rose-50/70 px-4 py-3 text-sm font-medium text-rose-600 transition hover:border-rose-300 dark:border-rose-500/20 dark:bg-rose-500/10"
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
              class="rounded-md py-3"
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
