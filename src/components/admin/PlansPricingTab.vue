<script setup lang="ts">
import { computed } from 'vue'
import { BadgeDollarSign, Save } from 'lucide-vue-next'
import type { AdminPricingPlan } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import RiskBadge from './RiskBadge.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
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

const publicCount = computed(() => props.plans.filter((plan) => plan.is_public).length)
const highlightedCount = computed(() => props.plans.filter((plan) => plan.highlighted).length)

const mappingCount = (plan: AdminPricingPlan) => {
  let count = 0
  if (plan.provider_mappings.stripe.price_id) count += 1
  if (plan.provider_mappings.paypal.plan_id || plan.provider_mappings.paypal.product_id) count += 1
  if (plan.provider_mappings.gmpay.amount_cents > 0) count += 1
  return count
}
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Revenue"
        title="Plans & Pricing"
        description="Manage the public plan catalog and provider price mappings. Pricing uses DB-first values when configured and keeps the legacy catalog fallback when mappings are missing."
        :icon="BadgeDollarSign"
      >
        <template #badges>
          <RiskBadge level="high" compact />
          <StatusPill tone="neutral">{{ plans.length }} plans</StatusPill>
          <StatusPill tone="success">{{ publicCount }} public</StatusPill>
          <StatusPill tone="warning">{{ highlightedCount }} highlighted</StatusPill>
        </template>
      </AdminSectionHeader>

      <AdminStateBlock
        class="mt-5"
        tone="warning"
        title="High-impact display and checkout mapping"
        description="Plan visibility, display prices, and provider IDs affect Pricing and checkout expectations. This page still does not perform real payment validation or webhook entitlement automation."
      />
    </AdminPanel>

    <AdminPanel v-for="plan in plans" :key="plan.plan_key" as="article" padding="lg">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <h3 class="text-xl font-semibold text-slate-950 dark:text-white">
              {{ plan.display_name || planLabel[plan.plan_key] }}
            </h3>
            <StatusPill :tone="plan.is_public ? 'success' : 'neutral'">
              {{ plan.is_public ? 'Public' : 'Hidden' }}
            </StatusPill>
            <StatusPill v-if="plan.highlighted" tone="warning">Highlighted</StatusPill>
            <StatusPill tone="info">{{ mappingCount(plan) }}/3 mappings</StatusPill>
          </div>
          <p class="mt-1 break-all text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
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
          Save plan
        </AdminActionButton>
      </div>

      <div class="mt-5 grid gap-4 xl:grid-cols-[1.05fr_1fr]">
        <section class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-sm font-semibold text-slate-900 dark:text-white">Display catalog</p>
              <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Controls Pricing page copy, visibility, ordering, and highlighted state.
              </p>
            </div>
            <StatusPill :tone="plan.is_public ? 'success' : 'neutral'">
              {{ plan.is_public ? 'Shown on Pricing' : 'Hidden from Pricing' }}
            </StatusPill>
          </div>

          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Display name</span>
              <input
                v-model="plan.display_name"
                type="text"
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Display price</span>
              <input
                v-model="plan.display_price"
                type="text"
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Amount in cents</span>
              <input
                v-model.number="plan.price_amount_cents"
                type="number"
                min="0"
                step="1"
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Currency</span>
              <input
                v-model="plan.currency"
                type="text"
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm uppercase text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Billing interval</span>
              <select
                v-model="plan.billing_interval"
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
                <option v-for="option in intervalOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>

            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Sort order</span>
              <input
                v-model.number="plan.sort_order"
                type="number"
                step="1"
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
            </label>
          </div>

          <label class="mt-3 grid gap-1 text-sm">
            <span class="font-semibold text-slate-600 dark:text-slate-300">Description</span>
            <textarea
              v-model="plan.description"
              rows="3"
              class="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm leading-6 text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            />
          </label>

          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <label class="flex min-h-11 items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              <span>
                <span class="block font-semibold">Public display</span>
                <span class="text-xs text-slate-500 dark:text-slate-400">Visible on Pricing</span>
              </span>
              <input v-model="plan.is_public" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-sky-600">
            </label>
            <label class="flex min-h-11 items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              <span>
                <span class="block font-semibold">Highlighted</span>
                <span class="text-xs text-slate-500 dark:text-slate-400">Emphasized plan card</span>
              </span>
              <input v-model="plan.highlighted" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-sky-600">
            </label>
          </div>
        </section>

        <section class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div>
            <p class="text-sm font-semibold text-slate-900 dark:text-white">Provider mapping</p>
            <p class="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Checkout resolves these values DB-first. Missing or incomplete mappings keep the legacy fallback path.
            </p>
          </div>

          <div class="mt-4 grid gap-3">
            <label class="grid gap-1 text-sm">
              <span class="font-semibold text-slate-600 dark:text-slate-300">Stripe Price ID</span>
              <input
                v-model="plan.provider_mappings.stripe.price_id"
                type="text"
                placeholder="price_..."
                class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
              >
            </label>

            <div class="grid gap-3 md:grid-cols-2">
              <label class="grid gap-1 text-sm">
                <span class="font-semibold text-slate-600 dark:text-slate-300">PayPal Plan ID</span>
                <input
                  v-model="plan.provider_mappings.paypal.plan_id"
                  type="text"
                  placeholder="P-..."
                  class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                >
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-semibold text-slate-600 dark:text-slate-300">PayPal Product ID</span>
                <input
                  v-model="plan.provider_mappings.paypal.product_id"
                  type="text"
                  placeholder="PROD-..."
                  class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                >
              </label>
            </div>

            <div class="grid gap-3 md:grid-cols-2">
              <label class="grid gap-1 text-sm">
                <span class="font-semibold text-slate-600 dark:text-slate-300">GM Pay amount cents</span>
                <input
                  v-model.number="plan.provider_mappings.gmpay.amount_cents"
                  type="number"
                  min="0"
                  step="1"
                  class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                >
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-semibold text-slate-600 dark:text-slate-300">GM Pay currency</span>
                <input
                  v-model="plan.provider_mappings.gmpay.currency"
                  type="text"
                  class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm uppercase text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                >
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-semibold text-slate-600 dark:text-slate-300">GM Pay token</span>
                <input
                  v-model="plan.provider_mappings.gmpay.token"
                  type="text"
                  class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm lowercase text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                >
              </label>
              <label class="grid gap-1 text-sm">
                <span class="font-semibold text-slate-600 dark:text-slate-300">GM Pay network</span>
                <input
                  v-model="plan.provider_mappings.gmpay.network"
                  type="text"
                  class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm lowercase text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                >
              </label>
            </div>
          </div>
        </section>
      </div>
    </AdminPanel>

    <AdminStateBlock
      v-if="plans.length === 0"
      tone="neutral"
      title="No pricing plans"
      description="The plan catalog will appear after the backend returns pricing_plans or the fallback catalog is seeded."
    />
  </div>
</template>
