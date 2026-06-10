<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const activeLocale = computed(() => locale.value)

const currentYear = new Date().getFullYear()

const socialLinks = [
  { name: 'GitHub', url: 'https://github.com', icon: 'github' },
  { name: 'Twitter', url: 'https://twitter.com', icon: 'twitter' },
]
</script>

<template>
  <footer
    class="border-t border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900"
    :data-locale="activeLocale"
  >
    <div class="container mx-auto px-4 py-8">
      <div class="grid gap-8 md:grid-cols-3">
        <div>
          <div class="mb-4 flex items-center gap-2">
            <div
              class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white"
            >
              <svg
                class="h-5 w-5"
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
            <span class="text-lg font-bold text-gray-900 dark:text-white">
              {{ t('app.title') }}
            </span>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-300">
            {{ t('app.tagline') }}
          </p>
        </div>

        <div>
          <h3 class="mb-3 text-sm font-semibold uppercase text-gray-900 dark:text-white">
            {{ t('footer.tools') }}
          </h3>
          <ul class="space-y-2 text-sm">
            <li>
              <a
                href="/tools/merge"
                class="text-gray-600 hover:text-primary dark:text-gray-300"
              >
                {{ t('tools.merge.title') }}
              </a>
            </li>
            <li>
              <a
                href="/tools/split"
                class="text-gray-600 hover:text-primary dark:text-gray-300"
              >
                {{ t('tools.split.title') }}
              </a>
            </li>
            <li>
              <a
                href="/tools/rotate"
                class="text-gray-600 hover:text-primary dark:text-gray-300"
              >
                {{ t('tools.rotate.title') }}
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h3 class="mb-3 text-sm font-semibold uppercase text-gray-900 dark:text-white">
            {{ t('footer.followUs') }}
          </h3>
          <div class="flex gap-3">
            <a
              v-for="link in socialLinks"
              :key="link.name"
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer"
              class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-gray-600 transition-colors hover:bg-primary hover:text-white dark:bg-gray-800 dark:text-gray-300"
            >
              <span class="sr-only">{{ link.name }}</span>
              <svg
                class="h-5 w-5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  v-if="link.icon === 'github'"
                  d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
                />
                <path
                  v-else-if="link.icon === 'twitter'"
                  d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>

      <div
        class="mt-8 border-t border-gray-200 pt-8 text-center text-sm text-gray-600 dark:border-gray-700 dark:text-gray-400"
      >
        <p>&copy; {{ currentYear }} {{ t('app.title') }}. {{ t('footer.madeWith') }}</p>
        <p class="mt-2">
          <a
            href="#"
            class="hover:text-primary"
          >{{ t('footer.privacyPolicy') }}</a>
          <span class="mx-2">&middot;</span>
          <a
            href="#"
            class="hover:text-primary"
          >{{ t('footer.termsOfService') }}</a>
        </p>
      </div>
    </div>
  </footer>
</template>
