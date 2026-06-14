<script setup lang="ts">
import { Save } from 'lucide-vue-next'
import type { AdminPricingPlan } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
  plans: AdminPricingPlan[]
  savingKey: string | null
}>()

const emit = defineEmits<{
  save: [plan: AdminPricingPlan]
}>()

const planLabel: Record<string, string> = {
  free: 'Free',
  pro_monthly: 'Pro Monthly',
  pro_yearly: 'Pro Yearly',
  enterprise: 'Enterprise',
}

const intervalOptions = [
  { value: 'none', label: 'None' },
  { value: 'month', label: 'Monthly' },
  { value: 'year', label: 'Yearly' },
  { value: 'custom', label: 'Custom' },
] as const
</script>

<template>
  <div class="grid gap-4">
    <AdminPanel as="section" tone="subtle">
      <div class="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-lg font-semibold">套餐目录</p>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            这里管理 Pricing 页面展示和下单时使用的 provider price mapping。第一版只保留固定套餐，不做真实扣费验证和 webhook 权益自动化。
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <StatusPill tone="neutral">{{ plans.length }} plans</StatusPill>
          <StatusPill tone="success">{{ plans.filter((plan) => plan.is_public).length }} public</StatusPill>
        </div>
      </div>
    </AdminPanel>

    <AdminPanel v-for="plan in plans" :key="plan.plan_key" as="article">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h3 class="text-xl font-semibold">{{ plan.display_name || planLabel[plan.plan_key] }}</h3>
            <StatusPill :tone="plan.is_public ? 'success' : 'neutral'">
              {{ plan.is_public ? 'public' : 'hidden' }}
            </StatusPill>
            <StatusPill v-if="plan.highlighted" tone="warning">highlighted</StatusPill>
          </div>
          <p class="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {{ plan.plan_key }}
          </p>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ plan.description || 'No public description configured.' }}
          </p>
        </div>

        <AdminActionButton
          :disabled="savingKey === `pricing:${plan.plan_key}`"
          :loading="savingKey === `pricing:${plan.plan_key}`"
          @click="emit('save', plan)"
        >
          <template #icon>
            <Save class="h-4 w-4" />
          </template>
          保存套餐
        </AdminActionButton>
      </div>

      <div class="mt-5 grid gap-4 xl:grid-cols-[1.05fr_1fr]">
        <section class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-sm font-semibold text-slate-900 dark:text-white">展示配置</p>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">展示名称</span>
              <input
                v-model="plan.display_name"
                type="text"
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              />
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">展示价格</span>
              <input
                v-model="plan.display_price"
                type="text"
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              />
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">金额 cents</span>
              <input
                v-model.number="plan.price_amount_cents"
                type="number"
                min="0"
                step="1"
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              />
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">币种</span>
              <input
                v-model="plan.currency"
                type="text"
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm uppercase text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              />
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">周期</span>
              <select
                v-model="plan.billing_interval"
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
                <option v-for="option in intervalOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">排序</span>
              <input
                v-model.number="plan.sort_order"
                type="number"
                step="1"
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              />
            </label>
          </div>

          <label class="mt-3 grid gap-1 text-sm">
            <span class="font-medium text-slate-600 dark:text-slate-300">描述</span>
            <textarea
              v-model="plan.description"
              rows="3"
              class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            />
          </label>

          <div class="mt-4 flex flex-wrap gap-4">
            <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <input v-model="plan.is_public" type="checkbox" class="rounded border-slate-300 text-sky-600" />
              公开显示
            </label>
            <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <input v-model="plan.highlighted" type="checkbox" class="rounded border-slate-300 text-sky-600" />
              推荐展示
            </label>
          </div>
        </section>

        <section class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-sm font-semibold text-slate-900 dark:text-white">Provider mapping</p>
          <div class="mt-4 grid gap-3">
            <label class="grid gap-1 text-sm">
              <span class="font-medium text-slate-600 dark:text-slate-300">Stripe Price ID</span>
              <input
                v-model="plan.provider_mappings.stripe.price_id"
                type="text"
                placeholder="price_..."
                class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              />
            </label>

            <div class="grid gap-3 md:grid-cols-2">
              <label class="grid gap-1 text-sm">
                <span class="font-medium text-slate-600 dark:text-slate-300">PayPal Plan ID</span>
                <input
                  v-model="plan.provider_mappings.paypal.plan_id"
                  type="text"
                  placeholder="P-..."
                  class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                />
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-medium text-slate-600 dark:text-slate-300">PayPal Product ID</span>
                <input
                  v-model="plan.provider_mappings.paypal.product_id"
                  type="text"
                  placeholder="PROD-..."
                  class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                />
              </label>
            </div>

            <div class="grid gap-3 md:grid-cols-2">
              <label class="grid gap-1 text-sm">
                <span class="font-medium text-slate-600 dark:text-slate-300">GM Pay amount cents</span>
                <input
                  v-model.number="plan.provider_mappings.gmpay.amount_cents"
                  type="number"
                  min="0"
                  step="1"
                  class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                />
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-medium text-slate-600 dark:text-slate-300">GM Pay currency</span>
                <input
                  v-model="plan.provider_mappings.gmpay.currency"
                  type="text"
                  class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm uppercase text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                />
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-medium text-slate-600 dark:text-slate-300">GM Pay token</span>
                <input
                  v-model="plan.provider_mappings.gmpay.token"
                  type="text"
                  class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm lowercase text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                />
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-medium text-slate-600 dark:text-slate-300">GM Pay network</span>
                <input
                  v-model="plan.provider_mappings.gmpay.network"
                  type="text"
                  class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm lowercase text-slate-950 outline-none focus:border-sky-500 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                />
              </label>
            </div>
          </div>
        </section>
      </div>
    </AdminPanel>
  </div>
</template>
