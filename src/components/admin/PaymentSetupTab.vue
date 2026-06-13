<script setup lang="ts">
import { computed, ref } from 'vue'
import { ClipboardCopy, Copy, FileCog, RefreshCw, ShieldCheck } from 'lucide-vue-next'
import type { AdminPaymentProviderHealth, AdminPaymentSummary } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import StatusPill from './StatusPill.vue'

const props = defineProps<{
  paymentSummary: AdminPaymentSummary | null
  evidenceCopied: boolean
  savingKey: string | null
}>()

const emit = defineEmits<{
  refresh: []
  copyEvidence: []
}>()

const copiedEndpointKey = ref<string | null>(null)

const providers = computed(() => props.paymentSummary?.providers ?? [])
const enabledCount = computed(() => providers.value.filter((provider) => provider.enabled).length)
const configuredCount = computed(
  () => providers.value.filter((provider) => provider.configured).length,
)
const acceptedCount = computed(
  () => providers.value.filter((provider) => provider.acceptance_status === 'accepted').length,
)
const blockerCount = computed(() =>
  providers.value.reduce((total, provider) => total + provider.acceptance_blockers.length, 0),
)

const acceptanceTone = (status: string) => {
  if (status === 'accepted') return 'success'
  if (status === 'needs_review') return 'danger'
  if (status === 'missing_config' || status === 'waiting_callback') return 'warning'
  if (status === 'ready_to_test') return 'info'
  return 'neutral'
}

const configTone = (provider: AdminPaymentProviderHealth) =>
  provider.missing_config_keys.length ? 'warning' : 'success'

const copyEndpoint = async (key: string, value: string) => {
  if (!value) return
  await navigator.clipboard.writeText(value)
  copiedEndpointKey.value = key
  window.setTimeout(() => {
    if (copiedEndpointKey.value === key) {
      copiedEndpointKey.value = null
    }
  }, 1800)
}
</script>

<template>
  <div class="space-y-6">
    <section class="min-w-0 rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="flex items-center gap-3">
            <FileCog class="h-5 w-5 text-slate-700 dark:text-slate-200" />
            <h2 class="text-xl font-semibold">支付配置</h2>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            这里只展示支付接入是否具备上线条件，不在浏览器里录入或显示商户密钥。真正的密钥仍由服务器环境变量和商户后台管理，前端只负责给管理员明确的配置清单和回调地址。
          </p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row">
          <AdminActionButton
            tone="neutral"
            class="min-h-11"
            :loading="savingKey === 'payments:refresh'"
            :disabled="savingKey === 'payments:refresh'"
            @click="emit('refresh')"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            刷新配置状态
          </AdminActionButton>
          <AdminActionButton
            tone="neutral"
            class="min-h-11"
            :disabled="!paymentSummary?.integration_evidence_packet"
            @click="emit('copyEvidence')"
          >
            <template #icon>
              <ClipboardCopy class="h-4 w-4" />
            </template>
            {{ evidenceCopied ? '已复制证据包' : '复制联调证据包' }}
          </AdminActionButton>
        </div>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Providers
          </p>
          <p class="mt-2 text-3xl font-semibold">{{ providers.length }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">后端注册的支付渠道</p>
        </div>
        <div class="min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Enabled
          </p>
          <p class="mt-2 text-3xl font-semibold">{{ enabledCount }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">前台可选择渠道</p>
        </div>
        <div class="min-w-0 rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-200/75">
            Accepted
          </p>
          <p class="mt-2 text-3xl font-semibold text-emerald-800 dark:text-emerald-100">
            {{ acceptedCount }}
          </p>
          <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-200/75">
            已通过验收，配置齐全 {{ configuredCount }}
          </p>
        </div>
        <div class="min-w-0 rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p class="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-200/75">
            Review
          </p>
          <p class="mt-2 text-3xl font-semibold text-amber-800 dark:text-amber-100">
            {{ blockerCount }}
          </p>
          <p class="mt-1 text-xs text-amber-700 dark:text-amber-200/75">待处理阻塞项</p>
        </div>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-2">
      <article
        v-for="provider in providers"
        :key="provider.key"
        class="min-w-0 rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
      >
        <div class="flex flex-wrap items-center gap-2">
          <h3 class="mr-auto text-lg font-semibold text-slate-950 dark:text-white">
            {{ provider.display_name }}
          </h3>
          <StatusPill :tone="provider.enabled ? 'success' : 'neutral'">
            {{ provider.enabled ? 'enabled' : 'disabled' }}
          </StatusPill>
          <StatusPill :tone="configTone(provider)">
            {{ provider.missing_config_keys.length ? 'needs config' : 'configured' }}
          </StatusPill>
          <StatusPill :tone="acceptanceTone(provider.acceptance_status)">
            {{ provider.acceptance_label }}
          </StatusPill>
        </div>

        <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ provider.acceptance_detail }}
        </p>

        <div class="mt-4 min-w-0 rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
          <div class="flex items-center gap-2">
            <ShieldCheck class="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
            <p class="font-semibold">商户后台配置</p>
          </div>
          <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {{ provider.merchant_console_hint }}
          </p>

          <dl class="mt-4 space-y-3">
            <div>
              <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Webhook / Notify URL
              </dt>
              <dd class="mt-1 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
                <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
                  {{ provider.webhook_url }}
                </code>
                <button
                  type="button"
                  class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                  :aria-label="`复制 ${provider.display_name} webhook`"
                  @click="copyEndpoint(`${provider.key}:webhook`, provider.webhook_url)"
                >
                  <Copy class="h-4 w-4" />
                </button>
              </dd>
            </div>
            <div class="grid gap-3 md:grid-cols-2">
              <div>
                <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Success Return
                </dt>
                <dd class="mt-1 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
                  <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
                    {{ provider.success_return_url }}
                  </code>
                  <button
                    type="button"
                    class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    :aria-label="`复制 ${provider.display_name} success return`"
                    @click="copyEndpoint(`${provider.key}:success`, provider.success_return_url)"
                  >
                    <Copy class="h-4 w-4" />
                  </button>
                </dd>
              </div>
              <div>
                <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Cancel Return
                </dt>
                <dd class="mt-1 flex min-w-0 gap-2 rounded-md bg-white p-2 dark:bg-slate-900">
                  <code class="min-w-0 flex-1 break-all text-xs leading-5 text-slate-700 dark:text-slate-200">
                    {{ provider.cancel_return_url }}
                  </code>
                  <button
                    type="button"
                    class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    :aria-label="`复制 ${provider.display_name} cancel return`"
                    @click="copyEndpoint(`${provider.key}:cancel`, provider.cancel_return_url)"
                  >
                    <Copy class="h-4 w-4" />
                  </button>
                </dd>
              </div>
            </div>
          </dl>

          <p
            v-if="copiedEndpointKey?.startsWith(provider.key)"
            class="mt-3 text-xs font-semibold text-emerald-700 dark:text-emerald-200"
          >
            地址已复制。
          </p>
        </div>

        <div class="mt-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Required backend config
          </p>
            <div class="mt-2 flex min-w-0 flex-wrap gap-2">
            <StatusPill
              v-for="key in provider.required_config_keys"
              :key="key"
              :tone="provider.missing_config_keys.includes(key) ? 'warning' : 'success'"
            >
              {{ key }}
            </StatusPill>
          </div>
        </div>

        <div v-if="provider.acceptance_blockers.length" class="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
          <p class="font-semibold">上线阻塞项</p>
          <ul class="mt-2 space-y-1">
            <li v-for="blocker in provider.acceptance_blockers" :key="`${provider.key}-${blocker}`">
              {{ blocker }}
            </li>
          </ul>
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-2">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Sandbox smoke test
            </p>
            <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
              <li v-for="(step, index) in provider.sandbox_runbook" :key="`${provider.key}-sandbox-${step}`">
                {{ index + 1 }}. {{ step }}
              </li>
            </ol>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Go-live checklist
            </p>
            <ol class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
              <li v-for="(step, index) in provider.go_live_checklist" :key="`${provider.key}-live-${step}`">
                {{ index + 1 }}. {{ step }}
              </li>
            </ol>
          </div>
        </div>

        <div v-if="provider.setup_notes.length" class="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400">
          <p v-for="note in provider.setup_notes" :key="`${provider.key}-${note}`">
            {{ note }}
          </p>
        </div>
      </article>
    </section>

    <AdminPanel v-if="!providers.length" as="section" tone="subtle">
      <p class="text-center text-sm text-slate-500 dark:text-slate-400">
        暂无支付渠道配置数据。请刷新支付状态或检查后端支付 provider 注册表。
      </p>
    </AdminPanel>
  </div>
</template>
