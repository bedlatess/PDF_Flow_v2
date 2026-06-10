<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import { useUserStore } from '@/stores/user'
import Button from '@/components/common/Button.vue'

const router = useRouter()
const { t, locale } = useI18n()
const settingsStore = useSettingsStore()
const userStore = useUserStore()

const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)

const localeOptions = [
  { value: 'en', label: 'English' },
  { value: 'zh', label: '简体中文' },
  { value: 'es', label: 'Español' },
] as const

const userInitial = computed(() => {
  const name = userStore.user?.full_name || userStore.user?.email || '?'
  return name.charAt(0).toUpperCase()
})

const navigateHome = () => {
  router.push('/')
  mobileMenuOpen.value = false
}

const goToFeatures = () => {
  router.push('/features')
  mobileMenuOpen.value = false
}

const goToPricing = () => {
  router.push('/pricing')
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
})
</script>

<template>
  <header class="glass sticky top-0 z-50 border-b border-gray-200/50 dark:border-gray-700/50">
    <div class="container mx-auto px-4">
      <div class="flex h-16 items-center justify-between">
        <div
          class="cursor-pointer flex items-center gap-2"
          @click="navigateHome"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white">
            <svg
              class="h-6 w-6"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <span class="text-xl font-bold text-gray-900 dark:text-white">
            {{ t('app.title') }}
          </span>
        </div>

        <div class="hidden items-center gap-4 md:flex">
          <select
            :value="locale"
            class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
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
            class="rounded-lg p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            @click="toggleTheme"
          >
            <svg
              v-if="settingsStore.theme === 'light'"
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
            <svg
              v-else
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
          </button>

          <Button
            variant="outline"
            size="sm"
            @click="navigateHome"
          >
            {{ t('nav.home') }}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            @click="goToFeatures"
          >
            {{ t('nav.features') }}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            @click="goToPricing"
          >
            {{ t('nav.pricing') }}
          </Button>

          <div
            v-if="userStore.isAuthenticated"
            class="relative"
          >
            <button
              class="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-bold text-white"
              @click="userMenuOpen = !userMenuOpen"
            >
              {{ userInitial }}
            </button>
            <div
              v-if="userMenuOpen"
              class="absolute right-0 mt-2 w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800"
            >
              <div class="border-b border-gray-100 px-4 py-2 dark:border-gray-700">
                <p class="truncate text-sm font-medium text-gray-900 dark:text-white">
                  {{ userStore.user?.full_name || userStore.user?.email }}
                </p>
              </div>
              <button
                class="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
                @click="goToProfile"
              >
                {{ t('account.myAccount') }}
              </button>
              <button
                class="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                @click="handleLogout"
              >
                {{ t('auth.logout') }}
              </button>
            </div>
          </div>
          <Button
            v-else
            variant="primary"
            size="sm"
            @click="goToLogin"
          >
            {{ t('auth.login') }}
          </Button>
        </div>

        <button
          class="rounded-lg p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 md:hidden"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <svg
            class="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              v-if="!mobileMenuOpen"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
            <path
              v-else
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div
        v-if="mobileMenuOpen"
        class="border-t border-gray-200 py-4 dark:border-gray-700 md:hidden"
      >
        <div class="flex flex-col gap-3">
          <select
            :value="locale"
            class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
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
          <Button
            variant="ghost"
            size="sm"
            full-width
            @click="toggleTheme"
          >
            {{ settingsStore.theme === 'light' ? t('nav.themeToDark') : t('nav.themeToLight') }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            full-width
            @click="navigateHome"
          >
            {{ t('nav.home') }}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            full-width
            @click="goToFeatures"
          >
            {{ t('nav.features') }}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            full-width
            @click="goToPricing"
          >
            {{ t('nav.pricing') }}
          </Button>
          <template v-if="userStore.isAuthenticated">
            <Button
              variant="outline"
              size="sm"
              full-width
              @click="goToProfile"
            >
              {{ t('account.myAccount') }}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              full-width
              @click="handleLogout"
            >
              {{ t('auth.logout') }}
            </Button>
          </template>
          <Button
            v-else
            variant="primary"
            size="sm"
            full-width
            @click="goToLogin"
          >
            {{ t('auth.login') }}
          </Button>
        </div>
      </div>
    </div>
  </header>
</template>
