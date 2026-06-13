<script setup lang="ts">
import { ClipboardCopy, CreditCard, RefreshCw, ShieldCheck } from 'lucide-vue-next'
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
  if (status === 'paid') return 'success'
  if (status === 'applied') return 'success'
  if (status === 'pending') return 'warning'
  if (status === 'received' || status === 'ignored') return 'warning'
  if (status === 'amount_mismatch' || status === 'currency_mismatch') return 'danger'
  if (status === 'failed' || status === 'canceled' || status === 'cancelled') return 'danger'
  return 'neutral'
}

const acceptanceTone = (status: string) => {
  if (status === 'accepted') return 'success'
  if (status === 'needs_review') return 'danger'
  if (status === 'missing_config' || status === 'waiting_callback') return 'warning'
  if (status === 'ready_to_test') return 'info'
  return 'neutral'
}
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="flex items-center gap-3">
            <CreditCard class="h-5 w-5 text-sky-600 dark:text-sky-300" />
            <p class="text-xl font-semibold">支付对账</p>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            这里是只读支付运营视图，用来确认订单状态、支付方式配置和需要人工核对的异常。权益仍然只由后端已验证的回调或捕获结果激活。
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

      <div class="mt-5 grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <AdminPanel as="div" padding="sm" tone="subtle">
          <p class="text-sm text-slate-500 dark:text-slate-400">总订单</p>
          <p class="mt-2 text-3xl font-semibold">{{ paymentSummary?.total_orders ?? 0 }}</p>
        </AdminPanel>
        <AdminPanel as="div" padding="sm" tone="warning">
          <p class="text-sm text-amber-700 dark:text-amber-200/80">待支付</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ paymentSummary?.pending_orders ?? 0 }}
          </p>
        </AdminPanel>
        <AdminPanel as="div" padding="sm" tone="success">
          <p class="text-sm text-emerald-700 dark:text-emerald-200/80">已支付</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">
            {{ paymentSummary?.paid_orders ?? 0 }}
          </p>
        </AdminPanel>
        <AdminPanel as="div" padding="sm" tone="danger">
          <p class="text-sm text-rose-700 dark:text-rose-200/80">需核对</p>
          <p class="mt-2 text-3xl font-semibold text-rose-800 dark:text-rose-100">
            {{
              (paymentSummary?.amount_mismatch_orders ?? 0) +
              (paymentSummary?.currency_mismatch_orders ?? 0)
            }}
          </p>
        </AdminPanel>
        <AdminPanel as="div" padding="sm" tone="warning">
          <p class="text-sm text-amber-700 dark:text-amber-200/80">过期待付</p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ paymentSummary?.expired_pending_orders ?? 0 }}
          </p>
        </AdminPanel>
        <AdminPanel as="div" padding="sm" tone="info">
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
        </AdminPanel>
      </div>
    </AdminPanel>

    <section class="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <AdminPanel as="article">
        <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="font-semibold">支付方式健康</p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              enabled 表示前台可选择，configured 表示商户关键配置已存在。
            </p>
          </div>
          <ShieldCheck class="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
        </div>

        <div class="grid gap-3">
          <div
            v-for="provider in paymentSummary?.providers || []"
            :key="provider.key"
            class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
          >
            <div class="flex flex-wrap items-center gap-2">
              <p class="mr-auto font-semibold text-slate-950 dark:text-white">
                {{ provider.display_name }}
              </p>
              <StatusPill :tone="provider.enabled ? 'success' : 'neutral'">
                {{ provider.enabled ? 'enabled' : 'disabled' }}
              </StatusPill>
              <StatusPill :tone="provider.configured ? 'success' : 'warning'">
                {{ provider.configured ? 'configured' : 'missing config' }}
              </StatusPill>
              <StatusPill :tone="acceptanceTone(provider.acceptance_status)">
                {{ provider.acceptance_label }}
              </StatusPill>
            </div>
            <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {{ provider.detail }}
            </p>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {{ provider.acceptance_detail }}
            </p>
            <div class="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
              <div class="rounded-md bg-white p-2 dark:bg-slate-900">
                <p class="font-semibold">{{ provider.open_orders }}</p>
                <p class="mt-1 text-slate-500 dark:text-slate-400">open</p>
              </div>
              <div class="rounded-md bg-white p-2 dark:bg-slate-900">
                <p class="font-semibold">{{ provider.paid_orders }}</p>
                <p class="mt-1 text-slate-500 dark:text-slate-400">paid</p>
              </div>
              <div class="rounded-md bg-white p-2 dark:bg-slate-900">
                <p class="font-semibold">{{ provider.failed_orders }}</p>
                <p class="mt-1 text-slate-500 dark:text-slate-400">review</p>
              </div>
            </div>
            <div
              v-if="provider.acceptance_blockers.length || provider.latest_paid_event_at"
              class="mt-3 rounded-md bg-white p-3 text-xs leading-5 text-slate-500 dark:bg-slate-900 dark:text-slate-400"
            >
              <p v-if="provider.latest_paid_event_at">
                最近通过事件：{{ formatDate(provider.latest_paid_event_at) }}
              </p>
              <ul v-if="provider.acceptance_blockers.length" class="space-y-1">
                <li
                  v-for="blocker in provider.acceptance_blockers"
                  :key="`${provider.key}-blocker-${blocker}`"
                >
                  {{ blocker }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </AdminPanel>

      <AdminPanel as="article">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="font-semibold">对账排障包</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              后端生成的安全摘要，可粘贴到工单或商户联调记录；不包含原始回调、文档内容或完整 checkout 链接。
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
    </section>

    <AdminPanel as="section">
      <div class="mb-4">
        <p class="font-semibold">商户回调配置清单</p>
        <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
          以后配置 PayPal、支付宝、微信支付、易支付或 USDT 网关时，以这里的 webhook/notify URL 为准。成功/取消地址只是用户返回页面，不能作为开通会员的依据。
        </p>
      </div>

      <div class="grid gap-3 lg:grid-cols-2">
        <div
          v-for="provider in paymentSummary?.providers || []"
          :key="`${provider.key}-setup`"
          class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
        >
          <div class="flex flex-wrap items-center gap-2">
            <p class="mr-auto font-semibold text-slate-950 dark:text-white">
              {{ provider.display_name }}
            </p>
            <StatusPill :tone="provider.missing_config_keys.length ? 'warning' : 'success'">
              {{ provider.missing_config_keys.length ? 'needs config' : 'ready' }}
            </StatusPill>
            <StatusPill :tone="acceptanceTone(provider.acceptance_status)">
              {{ provider.acceptance_label }}
            </StatusPill>
          </div>

          <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ provider.acceptance_detail }}
          </p>

          <p class="mt-3 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
            Merchant console
          </p>
          <p class="mt-1 text-sm text-slate-700 dark:text-slate-200">
            {{ provider.merchant_console_hint }}
          </p>

          <dl class="mt-3 space-y-3 text-sm">
            <div>
              <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Webhook / notify URL
              </dt>
              <dd class="mt-1 break-all rounded-md bg-white p-2 font-mono text-[12px] leading-5 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                {{ provider.webhook_url }}
              </dd>
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <div>
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                  Success return
                </dt>
                <dd class="mt-1 break-all rounded-md bg-white p-2 font-mono text-[12px] leading-5 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                  {{ provider.success_return_url }}
                </dd>
              </div>
              <div>
                <dt class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                  Cancel return
                </dt>
                <dd class="mt-1 break-all rounded-md bg-white p-2 font-mono text-[12px] leading-5 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                  {{ provider.cancel_return_url }}
                </dd>
              </div>
            </div>
          </dl>

          <div class="mt-3">
            <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              Required backend config
            </p>
            <div class="mt-2 flex flex-wrap gap-2">
              <StatusPill
                v-for="key in provider.required_config_keys"
                :key="key"
                :tone="provider.missing_config_keys.includes(key) ? 'warning' : 'success'"
              >
                {{ key }}
              </StatusPill>
            </div>
          </div>

          <ul class="mt-3 space-y-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
            <li v-for="note in provider.setup_notes" :key="note">
              {{ note }}
            </li>
          </ul>
        </div>
      </div>
    </AdminPanel>

    <AdminPanel as="section">
      <div class="mb-4">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="font-semibold">支付联调运维包</p>
            <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
              用于你后面自己跑 sandbox 或低金额 live smoke test。每个渠道都按“沙箱步骤、上线检查、预期事件链、失败排查、证据字段”整理，方便逐项核对和复盘。
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
      </div>

      <div class="grid gap-4 xl:grid-cols-2">
        <div
          v-for="provider in paymentSummary?.providers || []"
          :key="`${provider.key}-runbook`"
          class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45"
        >
          <div class="flex flex-wrap items-center gap-2">
            <p class="mr-auto font-semibold text-slate-950 dark:text-white">
              {{ provider.display_name }}
            </p>
            <StatusPill :tone="provider.enabled ? 'success' : 'neutral'">
              {{ provider.enabled ? 'enabled' : 'disabled' }}
            </StatusPill>
            <StatusPill :tone="provider.configured ? 'success' : 'warning'">
              {{ provider.configured ? 'configured' : 'missing config' }}
            </StatusPill>
          </div>

          <div class="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Sandbox smoke test
              </p>
              <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li v-for="(step, index) in provider.sandbox_runbook" :key="`${provider.key}-sandbox-${step}`">
                  {{ index + 1 }}. {{ step }}
                </li>
              </ol>
            </div>

            <div>
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Go-live checklist
              </p>
              <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li v-for="(step, index) in provider.go_live_checklist" :key="`${provider.key}-live-${step}`">
                  {{ index + 1 }}. {{ step }}
                </li>
              </ol>
            </div>
          </div>

          <div class="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Expected event flow
              </p>
              <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li v-for="(step, index) in provider.expected_event_flow" :key="`${provider.key}-flow-${step}`">
                  {{ index + 1 }}. {{ step }}
                </li>
              </ol>
            </div>

            <div>
              <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Troubleshooting
              </p>
              <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                <li v-for="(step, index) in provider.troubleshooting_steps" :key="`${provider.key}-trouble-${step}`">
                  {{ index + 1 }}. {{ step }}
                </li>
              </ol>
            </div>
          </div>

          <div class="mt-4">
            <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              Evidence fields to record
            </p>
            <div class="mt-2 flex flex-wrap gap-2">
              <StatusPill v-for="field in provider.evidence_fields" :key="`${provider.key}-${field}`">
                {{ field }}
              </StatusPill>
            </div>
          </div>
        </div>
      </div>
    </AdminPanel>

    <AdminPanel as="section">
      <div class="mb-4">
        <p class="font-semibold">最近支付订单</p>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          只展示运营排查需要的订单字段。完整支付确认仍以 provider 回调和后端订单状态为准。
        </p>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-[980px] w-full text-left text-sm">
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
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {{ order.plan }}
                </p>
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
                <StatusPill :tone="statusTone(order.status)">
                  {{ order.status }}
                </StatusPill>
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

    <AdminPanel as="section">
      <div class="mb-4">
        <p class="font-semibold">支付事件留痕</p>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          记录 provider 回调或捕获结果的处理状态，用来判断重复通知、已应用事件和需要人工核对的失败事件。
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
