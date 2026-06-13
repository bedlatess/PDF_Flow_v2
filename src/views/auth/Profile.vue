<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-6xl">
      <header class="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700 dark:text-sky-300">
            PDF-Flow
          </p>
          <h1 class="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
            {{ t('account.myAccount') }}
          </h1>
          <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ t('account.workspaceDescription') }}
          </p>
        </div>
        <button
          class="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
          @click="refreshAccount"
        >
          <RefreshCw class="mr-2 h-4 w-4" :class="{ 'animate-spin': userStore.loading || userStore.statsLoading }" />
          {{ t('account.refresh') }}
        </button>
      </header>

      <section v-if="initialLoading" class="rounded-lg border border-white/70 bg-white p-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <Loader2 class="mx-auto h-8 w-8 animate-spin text-sky-600" />
        <p class="mt-4 text-sm font-medium text-slate-600 dark:text-slate-300">
          {{ t('account.loading') }}
        </p>
      </section>

      <DiagnosticAlert
        v-else-if="!userStore.user"
        :title="t('account.emptyTitle')"
        :message="t('account.emptyMessage')"
        :support-hint="t('account.emptyHint')"
        tone="warning"
      />

      <template v-else>
        <DiagnosticAlert
          v-if="accountError"
          class="mb-6"
          :title="accountError.title"
          :message="accountError.message"
          :diagnostic-code="accountError.diagnosticCode"
          :support-hint="accountError.supportHint"
        />

        <div class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <section class="rounded-lg border border-white/70 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
                  {{ t('account.profile') }}
                </h2>
                <p class="mt-1 break-all text-sm text-slate-500 dark:text-slate-400">
                  {{ userStore.user.email }}
                </p>
              </div>
              <button
                v-if="!editing"
                class="inline-flex items-center rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-200 hover:text-sky-700 dark:border-slate-700 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
                @click="startEdit"
              >
                <Pencil class="mr-2 h-4 w-4" />
                {{ t('account.editProfile') }}
              </button>
            </div>

            <div class="mt-6 flex items-center gap-4 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xl font-semibold text-white dark:bg-sky-500">
                {{ initials }}
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950 dark:text-white">
                  {{ displayName }}
                </p>
                <span
                  class="mt-2 inline-flex rounded-full px-3 py-1 text-xs font-semibold"
                  :class="planBadgeClass"
                >
                  {{ planLabel }}
                </span>
              </div>
            </div>

            <form v-if="editing" class="mt-6 space-y-4" @submit.prevent="saveProfile">
              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200">
                  {{ t('auth.fullName') }}
                </span>
                <input
                  v-model="editForm.full_name"
                  type="text"
                  class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                >
              </label>
              <div class="flex flex-col gap-3 sm:flex-row">
                <button
                  type="submit"
                  :disabled="userStore.loading"
                  class="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-sky-500 dark:hover:bg-sky-400"
                >
                  <Loader2 v-if="userStore.loading" class="mr-2 h-4 w-4 animate-spin" />
                  {{ t('account.save') }}
                </button>
                <button
                  type="button"
                  class="inline-flex items-center justify-center rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                  @click="cancelEdit"
                >
                  {{ t('account.cancel') }}
                </button>
              </div>
            </form>

            <div v-else class="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <span class="font-semibold text-slate-800 dark:text-slate-100">{{ t('auth.fullName') }}:</span>
              {{ userStore.user.full_name || t('account.notSet') }}
            </div>

            <div v-if="updateMessage" class="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200">
              {{ updateMessage }}
            </div>
          </section>

          <section class="rounded-lg border border-white/70 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
                  {{ t('account.usage') }}
                </h2>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  {{ t('account.usageDescription') }}
                </p>
              </div>
              <button
                v-if="userStore.isFreeTier"
                class="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-700 dark:bg-sky-500 dark:hover:bg-sky-400"
                @click="router.push(localePath('/pricing'))"
              >
                {{ t('account.upgradeToPro') }}
              </button>
            </div>

            <div v-if="userStore.statsLoading" class="mt-5 rounded-md border border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-800 dark:bg-slate-950/45">
              <Loader2 class="mx-auto h-6 w-6 animate-spin text-sky-600" />
              <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">{{ t('account.usageLoading') }}</p>
            </div>

            <DiagnosticAlert
              v-else-if="userStore.statsError"
              class="mt-5"
              :title="userStore.statsError.title"
              :message="userStore.statsError.message"
              :diagnostic-code="userStore.statsError.diagnosticCode"
              :support-hint="userStore.statsError.supportHint"
              tone="warning"
            />

            <div v-else-if="!userStore.stats" class="mt-5 rounded-md border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-sm font-semibold text-slate-950 dark:text-white">{{ t('account.usageEmptyTitle') }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ t('account.usageEmptyMessage') }}</p>
            </div>

            <template v-else>
              <div class="mt-5 grid gap-4 sm:grid-cols-3">
                <div
                  v-for="item in usageItems"
                  :key="item.label"
                  class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
                >
                  <p class="text-2xl font-semibold text-slate-950 dark:text-white">
                    {{ item.value }}
                  </p>
                  <p class="mt-1 text-xs font-medium uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
                    {{ item.label }}
                  </p>
                </div>
              </div>

              <div v-if="userStore.isFreeTier" class="mt-5">
                <div class="mb-2 flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
                  <span>{{ t('account.todayQuota') }}</span>
                  <span>{{ userStore.quotaUsagePercentage }}%</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    class="h-full bg-sky-600 transition-all dark:bg-sky-400"
                    :style="{ width: `${userStore.quotaUsagePercentage}%` }"
                  />
                </div>
              </div>
            </template>
          </section>
        </div>

        <section class="mt-6 rounded-lg border border-red-100 bg-white p-6 shadow-sm dark:border-red-900/30 dark:bg-slate-900">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 class="text-lg font-semibold text-slate-950 dark:text-white">
                {{ t('account.dangerZone') }}
              </h2>
              <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                {{ t('account.deleteDescription') }}
              </p>
            </div>
            <button
              class="inline-flex items-center justify-center rounded-md border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition hover:border-red-300 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900/50 dark:text-red-300 dark:hover:bg-red-950/30 dark:hover:text-red-200"
              :disabled="userStore.loading"
              @click="confirmDelete"
            >
              <Trash2 class="mr-2 h-4 w-4" />
              {{ t('account.deleteAccount') }}
            </button>
          </div>
        </section>

        <ConfirmationDialog
          v-model="showDeleteConfirmation"
          :title="t('account.deleteDialog.title')"
          :summary="t('account.deleteDialog.summary', { email: userStore.user.email })"
          :details="deleteDialogDetails"
          :confirm-label="t('account.deleteDialog.confirm')"
          :cancel-label="t('account.cancel')"
          :loading="userStore.loading"
          @confirm="deleteAccount"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Loader2, Pencil, RefreshCw, Trash2 } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { useLocalePath } from '@/composables/useLocalePath'

const router = useRouter()
const userStore = useUserStore()
const { t } = useI18n()
const { localePath } = useLocalePath()

const editing = ref(false)
const updateMessage = ref('')
const accountError = ref<FormattedUserError | null>(null)
const showDeleteConfirmation = ref(false)
const editForm = reactive({ full_name: '' })

const initialLoading = computed(() => userStore.loading && !userStore.user)
const displayName = computed(() => userStore.user?.full_name || userStore.user?.email || t('account.notSet'))
const initials = computed(() => displayName.value.charAt(0).toUpperCase())

const planLabel = computed(() => {
  const role = userStore.user?.role || 'free'
  return t(`account.plans.${role}`)
})

const planBadgeClass = computed(() => {
  if (userStore.isEnterpriseTier) return 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
  if (userStore.isProTier) return 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-200'
  return 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
})

const quotaDisplay = computed(() => {
  const remaining = userStore.stats?.quota_remaining
  if (remaining === -1 || remaining === undefined) return t('account.unlimited')
  return String(remaining)
})
const usageItems = computed(() => [
  { label: t('account.totalRequests'), value: userStore.stats?.total_requests ?? 0 },
  { label: t('account.requestsToday'), value: userStore.stats?.requests_today ?? 0 },
  { label: t('account.quotaRemaining'), value: quotaDisplay.value },
])
const deleteDialogDetails = computed(() => [
  t('account.deleteDialog.detailAccess'),
  t('account.deleteDialog.detailRetention'),
  t('account.deleteDialog.detailSignIn'),
])

const refreshAccount = async () => {
  accountError.value = null
  await userStore.checkAuth()
}

const startEdit = () => {
  editForm.full_name = userStore.user?.full_name || ''
  editing.value = true
  updateMessage.value = ''
  accountError.value = null
}

const cancelEdit = () => {
  editing.value = false
  userStore.error = null
  accountError.value = null
}

const saveProfile = async () => {
  accountError.value = null
  try {
    await userStore.updateProfile({ full_name: editForm.full_name.trim() })
    updateMessage.value = t('account.updateSuccess')
    editing.value = false
  } catch (error) {
    accountError.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackTitle: t('account.updateFailedTitle'),
      fallbackMessage: t('account.updateFailedMessage'),
    })
  }
}

const confirmDelete = async () => {
  accountError.value = null
  showDeleteConfirmation.value = true
}

const deleteAccount = async () => {
  try {
    await userStore.deleteAccount()
    showDeleteConfirmation.value = false
    router.push(localePath('/'))
  } catch (error) {
    accountError.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackTitle: t('account.deleteFailedTitle'),
      fallbackMessage: t('account.deleteFailedMessage'),
    })
  }
}

onMounted(async () => {
  await refreshAccount()
})
</script>
