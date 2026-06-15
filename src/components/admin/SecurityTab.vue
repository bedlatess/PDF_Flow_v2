<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { KeyRound, LogOut, ShieldCheck } from 'lucide-vue-next'
import { authAPI } from '@/services/api'
import { formatUserFacingError } from '@/utils/error-messages'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const passwordLengthOk = computed(() => form.newPassword.length >= 8)
const passwordHasLetter = computed(() => /[A-Za-z]/.test(form.newPassword))
const passwordHasNumber = computed(() => /\d/.test(form.newPassword))
const passwordConfirmed = computed(
  () => form.newPassword.length > 0 && form.newPassword === form.confirmPassword,
)
const canSubmit = computed(
  () =>
    form.currentPassword.length > 0 &&
    passwordLengthOk.value &&
    passwordHasLetter.value &&
    passwordHasNumber.value &&
    passwordConfirmed.value &&
    !saving.value,
)

const clearLocalSession = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

const submitPasswordChange = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!passwordConfirmed.value) {
    errorMessage.value = 'New password confirmation does not match.'
    return
  }

  saving.value = true
  try {
    await authAPI.changePassword({
      current_password: form.currentPassword,
      new_password: form.newPassword,
    })

    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    successMessage.value = 'Password changed. Sign in again to continue managing PDF-Flow.'
    clearLocalSession()
    window.setTimeout(() => {
      window.location.href = '/access?reason=password_changed&redirect=/'
    }, 1200)
  } catch (error) {
    errorMessage.value = formatUserFacingError(error, {
      area: 'AUTH',
      fallbackMessage: 'Password could not be changed. Check the current password and try again.',
    }).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="System"
        title="Security"
        description="Rotate the active administrator password here. A successful change clears the current session and requires a fresh sign-in."
        :icon="ShieldCheck"
      />

      <AdminStateBlock
        class="mt-5"
        tone="warning"
        title="Session handling"
        description="The current browser session is cleared after a successful password change. The next request must authenticate again."
      />

      <AdminStateBlock
        class="mt-4"
        tone="info"
        title="Password rules"
        description="Use at least 8 characters with both letters and numbers."
      />
    </AdminPanel>

    <AdminPanel as="section" padding="lg">
      <div class="flex items-start gap-4">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-sky-600 text-white dark:bg-sky-400 dark:text-slate-950">
          <KeyRound class="h-5 w-5" />
        </div>
        <div>
          <h3 class="text-lg font-semibold">Change password</h3>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Enter the current password before setting a new one.
          </p>
        </div>
      </div>

      <form class="mt-6 space-y-4" @submit.prevent="submitPasswordChange">
        <div>
          <label for="admin-current-password" class="mb-2 block text-sm font-semibold">
            Current password
          </label>
          <input
            id="admin-current-password"
            v-model="form.currentPassword"
            type="password"
            autocomplete="current-password"
            required
            :disabled="saving"
            class="w-full rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100 disabled:opacity-60 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
          />
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <div>
            <label for="admin-new-password" class="mb-2 block text-sm font-semibold">
              New password
            </label>
            <input
              id="admin-new-password"
              v-model="form.newPassword"
              type="password"
              autocomplete="new-password"
              minlength="8"
              required
              :disabled="saving"
              class="w-full rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100 disabled:opacity-60 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </div>
          <div>
            <label for="admin-confirm-password" class="mb-2 block text-sm font-semibold">
              Confirm password
            </label>
            <input
              id="admin-confirm-password"
              v-model="form.confirmPassword"
              type="password"
              autocomplete="new-password"
              minlength="8"
              required
              :disabled="saving"
              class="w-full rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100 disabled:opacity-60 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:ring-sky-500/20"
            />
          </div>
        </div>

        <div class="grid gap-2 text-xs text-slate-500 dark:text-slate-400 sm:grid-cols-3">
          <span :class="passwordLengthOk ? 'text-emerald-600 dark:text-emerald-300' : ''">8+ characters</span>
          <span :class="passwordHasLetter ? 'text-emerald-600 dark:text-emerald-300' : ''">Letter included</span>
          <span :class="passwordHasNumber ? 'text-emerald-600 dark:text-emerald-300' : ''">Number included</span>
        </div>

        <p
          v-if="errorMessage"
          class="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
        >
          {{ errorMessage }}
        </p>
        <p
          v-if="successMessage"
          class="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200"
        >
          {{ successMessage }}
        </p>

        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-xs leading-5 text-slate-500 dark:text-slate-400">
            Existing browser tokens are cleared after success.
          </p>
          <AdminActionButton type="submit" :loading="saving" :disabled="!canSubmit">
            <template #icon>
              <LogOut class="h-4 w-4" />
            </template>
            Change and sign out
          </AdminActionButton>
        </div>
      </form>
    </AdminPanel>
  </div>
</template>
