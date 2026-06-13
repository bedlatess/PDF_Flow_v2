<script setup lang="ts">
import { ClipboardCopy, CreditCard, RefreshCw } from 'lucide-vue-next'
import type { AdminPaymentSummary } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
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
    <section class="min-w-0 rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="flex items-center gap-3">
            <CreditCard class="h-5 w-5 text-slate-700 dark:text-slate-200" />
            <h2 class="text-xl font-semibold">支付对账</h2>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            这里聚焦订单、回调事件、金额币种异常和对账证据。是否允许用户获得权益，仍以服务端已验证的支付结果为准。
          </p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <select
            :value="paymentProviderFilter"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            aria-label="筛选支付方式"
            @change="emit('update:paymentProviderFilter', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">全部支付方式</option>
            <option
              v-for="provider in paymentSummary?.providers || []"
              :key="provider.key"
              :value="provider.key"
            >
              {{ provider.display_name }}
            </option>
          </select>
          <select
            :value="paymentStatusFilter"
            class="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            aria-label="筛选支付状态"
            @change="emit('update:paymentStatusFilter', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">全部状态</option>
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
            刷新支付
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-sm text-slate-500 dark:text-slate-400">总订单</p>
          <p class="mt-2 text-3xl font-semibold">{{ paymentSummary?.total_orders ?? 0 }}</p>
        </div>
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-sm text-amber-700 dark:text-amber-200/80">待支付</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ paymentSummary?.pending_orders ?? 0 }}
          </p>
        </div>
        <div class="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-sm text-emerald-700 dark:text-emerald-200/80">已支付</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">
            {{ paymentSummary?.paid_orders ?? 0 }}
          </p>
        </div>
        <div class="rounded-md border border-rose-200 bg-rose-50 p-4 dark:border-rose-500/30 dark:bg-rose-500/10">
          <p class="text-sm text-rose-700 dark:text-rose-200/80">需核对</p>
          <p class="mt-2 text-3xl font-semibold text-rose-800 dark:text-rose-100">
            {{
              (paymentSummary?.amount_mismatch_orders ?? 0) +
              (paymentSummary?.currency_mismatch_orders ?? 0)
            }}
          </p>
        </div>
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-sm text-amber-700 dark:text-amber-200/80">过期待付</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ paymentSummary?.expired_pending_orders ?? 0 }}
          </p>
        </div>
        <div class="rounded-md border border-sky-200 bg-sky-50 p-4 dark:border-sky-500/30 dark:bg-sky-500/10">
          <p class="text-sm text-sky-700 dark:text-sky-200/80">已入账</p>
          <div class="mt-2 space-y-1">
            <p
              v-for="[currency, amount] in Object.entries(paymentSummary?.currency_breakdown || {})"
              :key="currency"
              class="text-lg font-semibold text-sky-800 dark:text-sky-100"
            >
              {{ formatMoney(Number(amount), currency) }}
            </p>
            <p
              v-if="Object.keys(paymentSummary?.currency_breakdown || {}).length === 0"
              class="text-2xl font-semibold text-sky-800 dark:text-sky-100"
            >
              0
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <AdminPanel as="article" class="min-w-0">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="font-semibold">对账摘要</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              后端生成的安全摘要，可用于工单、商户联调记录或线上复盘，不包含原始回调载荷和完整 checkout 链接。
            </p>
          </div>
          <AdminActionButton
            tone="neutral"
            class="min-h-11 shrink-0"
            :disabled="!paymentSummary?.reconciliation_summary"
            @click="emit('copyReconciliation')"
          >
            <template #icon>
              <ClipboardCopy class="h-4 w-4" />
            </template>
            {{ reconciliationCopied ? '已复制对账包' : '复制对账包' }}
          </AdminActionButton>
        </div>
        <pre
          class="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-slate-50 p-4 font-mono text-[12px] leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300"
          >{{ paymentSummary?.reconciliation_summary || '暂无对账摘要，请刷新支付数据。' }}</pre
        >
      </AdminPanel>

      <AdminPanel as="article" class="min-w-0">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="font-semibold">联调证据包</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              用于记录沙箱或小额 live smoke test 的关键字段。配置入口已经移动到“支付配置”模块。
            </p>
          </div>
          <AdminActionButton
            tone="neutral"
            class="min-h-11 shrink-0"
            :disabled="!paymentSummary?.integration_evidence_packet"
            @click="emit('copyEvidence')"
          >
            <template #icon>
              <ClipboardCopy class="h-4 w-4" />
            </template>
            {{ evidenceCopied ? '已复制证据包' : '复制证据包' }}
          </AdminActionButton>
        </div>
        <pre
          class="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-slate-50 p-4 font-mono text-[12px] leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300"
          >{{ paymentSummary?.integration_evidence_packet || '暂无联调证据，请刷新支付数据。' }}</pre
        >
      </AdminPanel>
    </section>

    <AdminPanel as="section" class="min-w-0 overflow-hidden">
      <div class="mb-4">
        <p class="font-semibold">最近支付订单</p>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          仅展示运营排查需要的订单字段。完整权益开通仍以 provider 回调和后端订单状态为准。
        </p>
      </div>

      <div class="-mx-5 min-w-0 overflow-x-auto px-5">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800 dark:text-slate-400">
            <tr>
              <th class="py-3 pr-4 font-semibold">订单</th>
              <th class="py-3 pr-4 font-semibold">用户</th>
              <th class="py-3 pr-4 font-semibold">方式</th>
              <th class="py-3 pr-4 font-semibold">金额</th>
              <th class="py-3 pr-4 font-semibold">状态</th>
              <th class="py-3 pr-4 font-semibold">凭据</th>
              <th class="py-3 pr-4 font-semibold">时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="order in paymentSummary?.recent_orders || []"
              :key="order.id"
              class="border-b border-slate-100 align-top dark:border-slate-800/70"
            >
              <td class="py-4 pr-4">
                <p class="break-all font-mono text-xs font-semibold text-slate-950 dark:text-white">
                  {{ order.merchant_order_id }}
                </p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ order.plan }}</p>
              </td>
              <td class="py-4 pr-4">
                <p class="break-all text-slate-700 dark:text-slate-200">
                  {{ order.user_email || `User #${order.user_id}` }}
                </p>
              </td>
              <td class="py-4 pr-4">
                <p class="font-semibold">{{ order.provider_display_name }}</p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {{ order.provider_order_id || '未返回 provider order' }}
                </p>
              </td>
              <td class="py-4 pr-4 font-semibold">
                {{ formatMoney(order.amount_cents, order.currency) }}
              </td>
              <td class="py-4 pr-4">
                <StatusPill :tone="statusTone(order.status)">{{ order.status }}</StatusPill>
              </td>
              <td class="py-4 pr-4">
                <div class="flex flex-wrap gap-2">
                  <StatusPill :tone="order.checkout_url_present ? 'info' : 'neutral'">
                    {{ order.checkout_url_present ? 'checkout' : 'no checkout' }}
                  </StatusPill>
                  <StatusPill :tone="order.qr_code_url_present ? 'info' : 'neutral'">
                    {{ order.qr_code_url_present ? 'code' : 'no code' }}
                  </StatusPill>
                </div>
              </td>
              <td class="py-4 pr-4 text-xs leading-5 text-slate-500 dark:text-slate-400">
                <p>创建 {{ formatDate(order.created_at) }}</p>
                <p v-if="order.paid_at">支付 {{ formatDate(order.paid_at) }}</p>
                <p v-else-if="order.expires_at">过期 {{ formatDate(order.expires_at) }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        v-if="!paymentSummary?.recent_orders?.length"
        class="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/45 dark:text-slate-400"
      >
        当前筛选条件下没有支付订单。
      </div>
    </AdminPanel>

    <AdminPanel as="section" class="min-w-0">
      <div class="mb-4">
        <p class="font-semibold">支付事件留痕</p>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          记录 provider 回调或捕获结果的处理状态，用于判断重复通知、已应用事件和需要人工核对的失败事件。
        </p>
      </div>

      <div class="grid gap-3 lg:grid-cols-2">
        <div
          v-for="event in paymentSummary?.recent_events || []"
          :key="event.id"
          class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
        >
          <div class="flex flex-wrap items-center gap-2">
            <StatusPill :tone="statusTone(event.processing_status)">
              {{ event.processing_status }}
            </StatusPill>
            <StatusPill>{{ event.provider }}</StatusPill>
            <span class="ml-auto text-xs text-slate-500 dark:text-slate-400">
              {{ formatDate(event.created_at) }}
            </span>
          </div>
          <p class="mt-3 break-all font-mono text-xs font-semibold text-slate-950 dark:text-white">
            {{ event.provider_event_id }}
          </p>
          <p class="mt-2 break-all text-xs text-slate-500 dark:text-slate-400">
            {{ event.merchant_order_id }}
          </p>
          <div class="mt-3 flex flex-wrap gap-2 text-xs">
            <StatusPill>{{ event.event_type }}</StatusPill>
            <StatusPill v-if="event.amount_cents !== null && event.currency">
              {{ formatMoney(event.amount_cents, event.currency) }}
            </StatusPill>
          </div>
          <p
            v-if="event.raw_summary"
            class="mt-3 break-words rounded-md bg-white p-2 font-mono text-[12px] leading-5 text-slate-600 dark:bg-slate-900 dark:text-slate-300"
          >
            {{ event.raw_summary }}
          </p>
          <p
            v-if="event.error_message"
            class="mt-3 text-sm leading-6 text-rose-700 dark:text-rose-200"
          >
            {{ event.error_message }}
          </p>
        </div>
      </div>

      <div
        v-if="!paymentSummary?.recent_events?.length"
        class="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/45 dark:text-slate-400"
      >
        暂无支付事件。真实回调或捕获成功后会在这里留下处理记录。
      </div>
    </AdminPanel>
  </div>
</template>
