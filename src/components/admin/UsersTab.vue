<script setup lang="ts">
import { KeyRound, Save, Search, Trash2 } from 'lucide-vue-next'
import type { AdminPasswordResetLink, AdminUser } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'
import { getEntitlementSummary } from '@/utils/entitlements'

defineProps<{
  users: AdminUser[]
  passwordResetLinks: Record<number, AdminPasswordResetLink>
  userSearch: string
  savingKey: string | null
  formatDate: (value: string) => string
}>()

const emit = defineEmits<{
  'update:userSearch': [value: string]
  search: []
  save: [user: AdminUser]
  toggleBan: [user: AdminUser]
  createPasswordResetLink: [user: AdminUser]
  delete: [user: AdminUser]
}>()

const updateUserSearch = (event: Event) => {
  emit('update:userSearch', (event.target as HTMLInputElement).value)
}

const subscriptionStatuses = [
  { value: '', label: 'No subscription' },
  { value: 'manual', label: 'Manual' },
  { value: 'active', label: 'Active' },
  { value: 'trialing', label: 'Trialing' },
  { value: 'cancel_at_period_end', label: 'Cancel at period end' },
  { value: 'expired', label: 'Expired' },
  { value: 'canceled', label: 'Canceled' },
]

const toDateTimeLocal = (value: string | null) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

const setSubscriptionEndDate = (user: AdminUser, value: string) => {
  user.subscription_end_date = value ? new Date(value).toISOString() : null
}

const updateSubscriptionEndDate = (user: AdminUser, event: Event) => {
  setSubscriptionEndDate(user, (event.target as HTMLInputElement).value)
}

const grantManualPro = (user: AdminUser, days: number) => {
  const currentEnd = user.subscription_end_date ? new Date(user.subscription_end_date) : null
  const base =
    currentEnd && currentEnd.getTime() > Date.now() && !Number.isNaN(currentEnd.getTime())
      ? currentEnd
      : new Date()
  base.setDate(base.getDate() + days)
  user.role = 'pro'
  user.subscription_status = 'manual'
  user.subscription_end_date = base.toISOString()
}

const expireSubscription = (user: AdminUser) => {
  user.subscription_status = 'expired'
  user.subscription_end_date = new Date().toISOString()
}

const entitlementSummary = (user: AdminUser) => getEntitlementSummary(user)
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Operate"
        title="Users & Access"
        description="Manage roles, account status, verification, manual entitlements, bans, and one-time reset links. Changes can affect real customer access."
      >
        <template #actions>
          <label class="relative block min-w-0 sm:min-w-[280px]">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              :value="userSearch"
              type="search"
              placeholder="Search by email or name"
              class="min-h-11 w-full rounded-md border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-white dark:focus:border-sky-400"
              @input="updateUserSearch"
              @keyup.enter="emit('search')"
            />
          </label>
          <AdminActionButton
            class="min-h-11 py-3"
            :disabled="savingKey === 'users:search'"
            :loading="savingKey === 'users:search'"
            @click="emit('search')"
          >
            Search
          </AdminActionButton>
        </template>
      </AdminSectionHeader>

      <div class="mt-5 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
        <div
          class="hidden grid-cols-[1.35fr_0.7fr_0.85fr_1.45fr] gap-3 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400 lg:grid"
        >
          <span>User</span>
          <span>Role</span>
          <span>Status</span>
          <span>Actions</span>
        </div>

        <div
          v-for="user in users"
          :key="user.id"
          class="grid gap-4 border-t border-slate-200 px-4 py-4 dark:border-slate-800 lg:grid-cols-[1.35fr_0.7fr_0.85fr_1.45fr] lg:items-center"
        >
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <p class="break-all font-semibold text-slate-950 dark:text-white">{{ user.email }}</p>
              <StatusPill v-if="user.is_test_account" tone="warning">Test account</StatusPill>
            </div>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {{ user.full_name || 'No profile name' }}
            </p>
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Joined {{ formatDate(user.created_at) }} · Email {{ user.is_verified ? 'verified' : 'unverified' }}
            </p>
          </div>

          <select
            v-model="user.role"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
          >
            <option value="free">Free</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
            <option value="admin">Admin</option>
          </select>

          <div>
            <StatusPill :tone="user.is_active ? 'success' : 'danger'">
              {{ user.is_active ? 'Active' : 'Blocked' }}
            </StatusPill>
            <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
              {{ user.last_login_at ? `Last login ${formatDate(user.last_login_at)}` : 'No login recorded' }}
            </p>
          </div>

          <div class="flex flex-wrap gap-2">
            <AdminActionButton
              tone="neutral"
              :disabled="savingKey === `user:${user.id}`"
              :loading="savingKey === `user:${user.id}`"
              @click="emit('save', user)"
            >
              <template #icon>
                <Save class="h-4 w-4" />
              </template>
              Save user
            </AdminActionButton>
            <AdminActionButton
              :tone="user.is_active ? 'warning' : 'success'"
              :disabled="savingKey === `ban:${user.id}`"
              :loading="savingKey === `ban:${user.id}`"
              @click="emit('toggleBan', user)"
            >
              {{ user.is_active ? 'Block' : 'Unblock' }}
            </AdminActionButton>
            <AdminActionButton
              tone="success"
              :disabled="!user.is_active || savingKey === `reset-link:${user.id}`"
              :loading="savingKey === `reset-link:${user.id}`"
              @click="emit('createPasswordResetLink', user)"
            >
              <template #icon>
                <KeyRound class="h-4 w-4" />
              </template>
              Reset link
            </AdminActionButton>
            <AdminActionButton
              tone="danger"
              :disabled="savingKey === `delete:${user.id}`"
              :loading="savingKey === `delete:${user.id}`"
              @click="emit('delete', user)"
            >
              <template #icon>
                <Trash2 class="h-4 w-4" />
              </template>
              Delete
            </AdminActionButton>
          </div>

          <div
            class="grid gap-3 rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/35 sm:grid-cols-[0.9fr_1fr_auto] lg:col-span-4"
          >
            <div class="flex flex-wrap items-center gap-2 sm:col-span-3">
              <StatusPill :tone="entitlementSummary(user).tone">
                {{ entitlementSummary(user).label }} · {{ entitlementSummary(user).statusLabel }}
              </StatusPill>
              <span class="text-xs font-medium text-slate-500 dark:text-slate-400">
                {{ entitlementSummary(user).detail }}
              </span>
            </div>
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Entitlement
              <select
                v-model="user.subscription_status"
                class="mt-2 min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm normal-case tracking-normal text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
              >
                <option
                  v-for="status in subscriptionStatuses"
                  :key="status.value || 'none'"
                  :value="status.value || null"
                >
                  {{ status.label }}
                </option>
              </select>
            </label>
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Ends at
              <input
                :value="toDateTimeLocal(user.subscription_end_date)"
                type="datetime-local"
                class="mt-2 min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm normal-case tracking-normal text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
                @input="updateSubscriptionEndDate(user, $event)"
              />
            </label>
            <div class="flex flex-wrap items-end gap-2">
              <button
                type="button"
                class="min-h-10 rounded-md border border-sky-200 bg-white px-3 py-2 text-xs font-semibold text-sky-700 hover:border-sky-300 hover:bg-sky-50 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100"
                @click="grantManualPro(user, 30)"
              >
                Pro +30d
              </button>
              <button
                type="button"
                class="min-h-10 rounded-md border border-sky-200 bg-white px-3 py-2 text-xs font-semibold text-sky-700 hover:border-sky-300 hover:bg-sky-50 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100"
                @click="grantManualPro(user, 365)"
              >
                Pro +365d
              </button>
              <button
                type="button"
                class="min-h-10 rounded-md border border-amber-200 bg-white px-3 py-2 text-xs font-semibold text-amber-700 hover:border-amber-300 hover:bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
                @click="expireSubscription(user)"
              >
                Expire
              </button>
            </div>
          </div>

          <AdminStateBlock
            v-if="passwordResetLinks[user.id]"
            class="lg:col-span-4"
            tone="success"
            title="One-time reset link generated"
            :description="`Expires ${formatDate(passwordResetLinks[user.id].expires_at)}`"
          >
            <p class="break-all font-mono text-[11px]">{{ passwordResetLinks[user.id].reset_url }}</p>
          </AdminStateBlock>
        </div>

        <AdminStateBlock
          v-if="users.length === 0"
          class="border-t border-slate-200 dark:border-slate-800"
          tone="neutral"
          title="No matching users"
          description="Try a different email/name search or refresh the user list."
        />
      </div>
    </AdminPanel>
  </div>
</template>
