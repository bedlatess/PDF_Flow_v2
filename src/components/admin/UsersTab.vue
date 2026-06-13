<script setup lang="ts">
import { KeyRound, Save, Trash2 } from 'lucide-vue-next'
import type { AdminPasswordResetLink, AdminUser } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
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
  <div class="contents">
    <AdminPanel as="section">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xl font-semibold">用户管理</p>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Smoke 测试会自动创建 `smoke-*`、`ocr-*`、`office-*`
            账号，这些会标记为测试账号。封禁会阻止登录，删除会移除账号数据；当前管理员不能封禁、降级或删除自己。
          </p>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row">
          <input
            :value="userSearch"
            type="search"
            placeholder="搜索邮箱或姓名"
            class="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-500 focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-400 dark:text-white dark:focus:border-sky-400"
            @input="updateUserSearch"
            @keyup.enter="emit('search')"
          />
          <AdminActionButton
            class="min-h-11 py-3"
            :disabled="savingKey === 'users:search'"
            :loading="savingKey === 'users:search'"
            @click="emit('search')"
          >
            搜索
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-5 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
        <div
          class="hidden grid-cols-[1.35fr_0.7fr_0.85fr_1.45fr] gap-3 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:bg-slate-800 dark:text-slate-400 lg:grid"
        >
          <span>用户</span>
          <span>角色</span>
          <span>状态</span>
          <span>操作</span>
        </div>

        <div
          v-for="user in users"
          :key="user.id"
          class="grid gap-4 border-t border-slate-200 px-4 py-4 dark:border-slate-800 lg:grid-cols-[1.35fr_0.7fr_0.85fr_1.45fr] lg:items-center"
        >
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <p class="font-semibold text-slate-950 dark:text-white">{{ user.email }}</p>
              <StatusPill v-if="user.is_test_account" tone="warning">测试账号</StatusPill>
            </div>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {{ user.full_name || '未填写姓名' }}
            </p>
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
              注册：{{ formatDate(user.created_at) }} · 邮箱状态：{{
                user.is_verified ? '已验证' : '未验证'
              }}
            </p>
          </div>

          <select
            v-model="user.role"
            class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:text-white dark:focus:border-sky-400"
          >
            <option value="free">Free</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
            <option value="admin">Admin</option>
          </select>

          <div>
            <StatusPill :tone="user.is_active ? 'success' : 'danger'">
              {{ user.is_active ? '正常' : '已封禁' }}
            </StatusPill>
            <p class="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
              {{
                user.last_login_at ? `最后登录：${formatDate(user.last_login_at)}` : '尚无登录记录'
              }}
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
              保存角色
            </AdminActionButton>
            <AdminActionButton
              :tone="user.is_active ? 'warning' : 'success'"
              :disabled="savingKey === `ban:${user.id}`"
              :loading="savingKey === `ban:${user.id}`"
              @click="emit('toggleBan', user)"
            >
              {{ user.is_active ? '封禁' : '解封' }}
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
              生成一次性重置链接
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
              删除
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
            <label class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
              Entitlement
              <select
                v-model="user.subscription_status"
                class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm normal-case tracking-normal text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
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
            <label class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
              Ends At
              <input
                :value="toDateTimeLocal(user.subscription_end_date)"
                type="datetime-local"
                class="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm normal-case tracking-normal text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-sky-400"
                @input="updateSubscriptionEndDate(user, $event)"
              />
            </label>
            <div class="flex flex-wrap items-end gap-2">
              <button
                type="button"
                class="rounded-md border border-sky-200 bg-white px-3 py-2 text-xs font-semibold text-sky-700 hover:border-sky-300 hover:bg-sky-50 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100"
                @click="grantManualPro(user, 30)"
              >
                Pro +30d
              </button>
              <button
                type="button"
                class="rounded-md border border-sky-200 bg-white px-3 py-2 text-xs font-semibold text-sky-700 hover:border-sky-300 hover:bg-sky-50 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100"
                @click="grantManualPro(user, 365)"
              >
                Pro +365d
              </button>
              <button
                type="button"
                class="rounded-md border border-amber-200 bg-white px-3 py-2 text-xs font-semibold text-amber-700 hover:border-amber-300 hover:bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
                @click="expireSubscription(user)"
              >
                Expire
              </button>
            </div>
          </div>

          <div
            v-if="passwordResetLinks[user.id]"
            class="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-xs leading-5 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100 lg:col-span-4"
          >
            <p class="font-semibold">
              已生成一次性重置链接，过期时间：{{ formatDate(passwordResetLinks[user.id].expires_at) }}
            </p>
            <p class="mt-2 break-all font-mono text-[11px]">
              {{ passwordResetLinks[user.id].reset_url }}
            </p>
          </div>
        </div>

        <div
          v-if="users.length === 0"
          class="border-t border-slate-200 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400"
        >
          没有找到匹配用户。
        </div>
      </div>
    </AdminPanel>
  </div>
</template>
