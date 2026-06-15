<script setup lang="ts">
import { ClipboardCopy, CreditCard, RefreshCw } from 'lucide-vue-next'
import type { AdminPaymentSummary } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'
import StatusPill from './StatusPill.vue'

defineProps<{
  paymentSummary: AdminPaymentSummary | null
  paymentProviderFilter: string
  paymentStatusFilter: string
  reconciliationCopied: boolean
  evidenceCopied: boolean
  savingKey: string | null
  formatDate: (value: string) => string
  formatMoney: (amountCents: number, currency: string) => string
}>()

const emit = defineEmits<{
  refresh: []
  copyReconciliation: []
  copyEvidence: []
  'update:paymentProviderFilter': [value: string]
  'update:paymentStatusFilter': [value: string]
}>()

const statusTone = (status: string) => {
  if (status === 'paid' || status === 'applied') return 'success'
  if (status === 'pending' || status === 'received' || status === 'ignored') return 'warning'
  if (
    status === 'amount_mismatch' ||
    status === 'currency_mismatch' ||
    status === 'failed' ||
    status === 'canceled' ||
    status === 'cancelled'
  )
    return 'danger'
  return 'neutral'
}
</script>

<template>
  <div class="min-w-0 space-y-6">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="Revenue"
        title="Payments & Evidence"
        description="Inspect orders, provider events, mismatch risks, pending expirations, and integration evidence. This view is diagnostic; entitlement automation remains backend-controlled."
        :icon="CreditCard"
      >
        <template #actions>
          <select
            :value="paymentProviderFilter"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            aria-label="Filter payment provider"
            @change="emit('update:paymentProviderFilter', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">All providers</option>
            <option v-for="provider in paymentSummary?.providers || []" :key="provider.key" :value="provider.key">
              {{ provider.display_name }}
            </option>
          </select>
          <select
            :value="paymentStatusFilter"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            aria-label="Filter payment status"
            @change="emit('update:paymentStatusFilter', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">All statuses</option>
            <option value="pending">pending</option>
            <option value="paid">paid</option>
            <option value="amount_mismatch">amount_mismatch</option>
            <option value="currency_mismatch">currency_mismatch</option>
            <option value="failed">failed</option>
          </select>
          <AdminActionButton
            class="min-h-11 shrink-0"
            :loading="savingKey === 'payments:refresh'"
            :disabled="savingKey === 'payments:refresh'"
            @click="emit('refresh')"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            Refresh payments
          </AdminActionButton>
        </template>
      </AdminSectionHeader>

      <div class="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <AdminStateBlock tone="neutral" compact title="Total orders" :description="String(paymentSummary?.total_orders ?? 0)" />
        <AdminStateBlock tone="warning" compact title="Pending" :description="String(paymentSummary?.pending_orders ?? 0)" />
        <AdminStateBlock tone="success" compact title="Paid" :description="String(paymentSummary?.paid_orders ?? 0)" />
        <AdminStateBlock tone="danger" compact title="Needs review" :description="String((paymentSummary?.amount_mismatch_orders ?? 0) + (paymentSummary?.currency_mismatch_orders ?? 0))" />
        <AdminStateBlock tone="warning" compact title="Expired pending" :description="String(paymentSummary?.expired_pending_orders ?? 0)" />
        <AdminStateBlock tone="info" compact title="Booked revenue">
          <p
            v-for="[currency, amount] in Object.entries(paymentSummary?.currency_breakdown || {})"
            :key="currency"
            class="font-semibold"
          >
            {{ formatMoney(Number(amount), currency) }}
          </p>
          <p v-if="Object.keys(paymentSummary?.currency_breakdown || {}).length === 0" class="font-semibold">0</p>
        </AdminStateBlock>
      </div>
    </AdminPanel>

    <section class="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <AdminPanel as="article" class="min-w-0">
        <AdminSectionHeader
          eyebrow="Summary"
          title="Reconciliation packet"
          description="A safe backend summary for support tickets, provider handoff, or live smoke notes. It avoids raw callback payloads and full checkout links."
        >
          <template #actions>
            <AdminActionButton
              tone="neutral"
              class="min-h-11 shrink-0"
              :disabled="!paymentSummary?.reconciliation_summary"
              @click="emit('copyReconciliation')"
            >
              <template #icon>
                <ClipboardCopy class="h-4 w-4" />
              </template>
              {{ reconciliationCopied ? 'Copied' : 'Copy packet' }}
            </AdminActionButton>
          </template>
        </AdminSectionHeader>
        <pre class="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-slate-50 p-4 font-mono text-[12px] leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">{{ paymentSummary?.reconciliation_summary || 'No reconciliation packet yet. Refresh payment data first.' }}</pre>
      </AdminPanel>

      <AdminPanel as="article" class="min-w-0">
        <AdminSectionHeader
          eyebrow="Evidence"
          title="Integration evidence packet"
          description="Key fields for sandbox or small live smoke records. Provider configuration stays in Payment Providers."
        >
          <template #actions>
            <AdminActionButton
              tone="neutral"
              class="min-h-11 shrink-0"
              :disabled="!paymentSummary?.integration_evidence_packet"
              @click="emit('copyEvidence')"
            >
              <template #icon>
                <ClipboardCopy class="h-4 w-4" />
              </template>
              {{ evidenceCopied ? 'Copied' : 'Copy evidence' }}
            </AdminActionButton>
          </template>
        </AdminSectionHeader>
        <pre class="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-slate-50 p-4 font-mono text-[12px] leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">{{ paymentSummary?.integration_evidence_packet || 'No integration evidence yet. Refresh payment data first.' }}</pre>
      </AdminPanel>
    </section>

    <AdminPanel as="section" class="min-w-0 overflow-hidden">
      <AdminSectionHeader
        eyebrow="Orders"
        title="Recent payment orders"
        description="Only operational fields are shown here. Entitlement decisions still depend on verified backend payment state."
      />

      <div class="-mx-5 mt-4 min-w-0 overflow-x-auto px-5">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800 dark:text-slate-400">
            <tr>
              <th class="py-3 pr-4 font-semibold">Order</th>
              <th class="py-3 pr-4 font-semibold">User</th>
              <th class="py-3 pr-4 font-semibold">Provider</th>
              <th class="py-3 pr-4 font-semibold">Amount</th>
              <th class="py-3 pr-4 font-semibold">Status</th>
              <th class="py-3 pr-4 font-semibold">Evidence</th>
              <th class="py-3 pr-4 font-semibold">Time</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in paymentSummary?.recent_orders || []" :key="order.id" class="border-b border-slate-100 align-top dark:border-slate-800/70">
              <td class="py-4 pr-4">
                <p class="break-all font-mono text-xs font-semibold text-slate-950 dark:text-white">{{ order.merchant_order_id }}</p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ order.plan }}</p>
              </td>
              <td class="py-4 pr-4">
                <p class="break-all text-slate-700 dark:text-slate-200">{{ order.user_email || `User #${order.user_id}` }}</p>
              </td>
              <td class="py-4 pr-4">
                <p class="font-semibold">{{ order.provider_display_name }}</p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ order.provider_order_id || 'No provider order id' }}</p>
              </td>
              <td class="py-4 pr-4 font-semibold">{{ formatMoney(order.amount_cents, order.currency) }}</td>
              <td class="py-4 pr-4">
                <StatusPill :tone="statusTone(order.status)">{{ order.status }}</StatusPill>
              </td>
              <td class="py-4 pr-4">
                <div class="flex flex-wrap gap-2">
                  <StatusPill :tone="order.checkout_url_present ? 'info' : 'neutral'">{{ order.checkout_url_present ? 'checkout' : 'no checkout' }}</StatusPill>
                  <StatusPill :tone="order.qr_code_url_present ? 'info' : 'neutral'">{{ order.qr_code_url_present ? 'code' : 'no code' }}</StatusPill>
                </div>
              </td>
              <td class="py-4 pr-4 text-xs leading-5 text-slate-500 dark:text-slate-400">
                <p>Created {{ formatDate(order.created_at) }}</p>
                <p v-if="order.paid_at">Paid {{ formatDate(order.paid_at) }}</p>
                <p v-else-if="order.expires_at">Expires {{ formatDate(order.expires_at) }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <AdminStateBlock
        v-if="!paymentSummary?.recent_orders?.length"
        tone="neutral"
        title="No payment orders match"
        description="Try clearing the provider or status filter, then refresh payment data."
      />
    </AdminPanel>

    <AdminPanel as="section" class="min-w-0">
      <AdminSectionHeader
        eyebrow="Events"
        title="Payment event trail"
        description="Provider callbacks or capture results appear here with their processing state for duplicate detection and manual review."
      />

      <div class="mt-4 grid gap-3 lg:grid-cols-2">
        <div v-for="event in paymentSummary?.recent_events || []" :key="event.id" class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex flex-wrap items-center gap-2">
            <StatusPill :tone="statusTone(event.processing_status)">{{ event.processing_status }}</StatusPill>
            <StatusPill>{{ event.provider }}</StatusPill>
            <span class="ml-auto text-xs text-slate-500 dark:text-slate-400">{{ formatDate(event.created_at) }}</span>
          </div>
          <p class="mt-3 break-all font-mono text-xs font-semibold text-slate-950 dark:text-white">{{ event.provider_event_id }}</p>
          <p class="mt-2 break-all text-xs text-slate-500 dark:text-slate-400">{{ event.merchant_order_id }}</p>
          <div class="mt-3 flex flex-wrap gap-2 text-xs">
            <StatusPill>{{ event.event_type }}</StatusPill>
            <StatusPill v-if="event.amount_cents !== null && event.currency">{{ formatMoney(event.amount_cents, event.currency) }}</StatusPill>
          </div>
          <p v-if="event.raw_summary" class="mt-3 break-words rounded-md bg-white p-2 font-mono text-[12px] leading-5 text-slate-600 dark:bg-slate-900 dark:text-slate-300">{{ event.raw_summary }}</p>
          <p v-if="event.error_message" class="mt-3 text-sm leading-6 text-rose-700 dark:text-rose-200">{{ event.error_message }}</p>
        </div>
      </div>

      <AdminStateBlock
        v-if="!paymentSummary?.recent_events?.length"
        tone="neutral"
        title="No payment events yet"
        description="Provider callbacks or captured payment results will appear here after they are received."
      />
    </AdminPanel>
  </div>
</template>
