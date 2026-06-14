<script setup lang="ts">
import { computed, onMounted } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Loader2,
  ShieldCheck,
} from 'lucide-vue-next'
import type { ControlRoomTabGroup } from '@/admin/control-room/types'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import AuditLogsTab from '@/components/admin/AuditLogsTab.vue'
import ContentBlocksTab from '@/components/admin/ContentBlocksTab.vue'
import ErrorsTab from '@/components/admin/ErrorsTab.vue'
import FeatureFlagsTab from '@/components/admin/FeatureFlagsTab.vue'
import FeedbackTab from '@/components/admin/FeedbackTab.vue'
import JobsTab from '@/components/admin/JobsTab.vue'
import MaintenanceTab from '@/components/admin/MaintenanceTab.vue'
import OverviewTab from '@/components/admin/OverviewTab.vue'
import PaymentSetupTab from '@/components/admin/PaymentSetupTab.vue'
import PaymentsTab from '@/components/admin/PaymentsTab.vue'
import SecurityTab from '@/components/admin/SecurityTab.vue'
import SiteSettingsTab from '@/components/admin/SiteSettingsTab.vue'
import UsersTab from '@/components/admin/UsersTab.vue'
import { useControlRoom } from '@/admin/control-room/useControlRoom'

const {
  tabs,
  loading,
  savingKey,
  activeTab,
  error,
  success,
  overview,
  operations,
  settings,
  flags,
  contentBlocks,
  auditLogs,
  users,
  userPasswordResetLinks,
  jobs,
  feedbackReports,
  apiErrors,
  diagnostics,
  healthReport,
  maintenance,
  paymentSummary,
  userSearch,
  jobStatusFilter,
  jobSearch,
  paymentProviderFilter,
  paymentStatusFilter,
  feedbackStatusFilter,
  highlightedFeedbackId,
  copiedFeedbackId,
  healthReportCopied,
  diagnosticSummaryCopied,
  reconciliationCopied,
  evidenceCopied,
  selectedContent,
  pendingConfirmation,
  filteredJobs,
  formatDate,
  formatMoney,
  parseDiagnostics,
  buildHealthReportSummary,
  copyFeedbackSummary,
  copyHealthReport,
  copyDiagnosticSummary,
  copyReconciliationSummary,
  copyPaymentEvidencePacket,
  closeAdminConfirmation,
  confirmAdminAction,
  loadHealthReport,
  loadAdminData,
  saveFlag,
  saveSetting,
  saveContentBlock,
  searchUsers,
  saveUser,
  toggleUserBan,
  createPasswordResetLink,
  deleteUser,
  loadJobs,
  loadPayments,
  loadFeedback,
  saveFeedback,
  cleanupLiveAcceptanceFeedback,
  refreshMaintenance,
  cleanupTestUsers,
  cleanupExpiredFiles,
  openFeedbackFromDiagnostics,
  loadDiagnostics,
} = useControlRoom()

const tabGroups = computed(() => {
  const groups = new Map<ControlRoomTabGroup, typeof tabs>()
  for (const tab of tabs) {
    const groupTabs = groups.get(tab.group) ?? []
    groupTabs.push(tab)
    groups.set(tab.group, groupTabs)
  }
  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }))
})

const currentTab = computed(() => tabs.find((tab) => tab.id === activeTab.value) ?? tabs[0])
const paymentProviders = computed(() => paymentSummary.value?.providers ?? [])
const paymentConfiguredCount = computed(
  () => paymentProviders.value.filter((provider) => provider.configured).length,
)
const paymentEnabledCount = computed(
  () => paymentProviders.value.filter((provider) => provider.enabled).length,
)
const paymentRiskCount = computed(
  () =>
    paymentProviders.value.filter(
      (provider) =>
        provider.missing_config_keys.length > 0 ||
        provider.acceptance_status === 'needs_review' ||
        provider.acceptance_status === 'missing_config',
    ).length,
)
const serviceRiskCount = computed(
  () =>
    Object.values(operations.value?.services ?? {}).filter(
      (service) => service.status !== 'healthy',
    ).length,
)

onMounted(loadAdminData)
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-slate-950 dark:bg-slate-950 dark:text-white">
    <header class="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div class="mx-auto max-w-[1500px] px-4 py-6 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              <ShieldCheck class="h-4 w-4" />
              Admin Console
              <span class="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                admin.pawn.eu.org
              </span>
            </div>
            <h1 class="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              PDF-Flow Admin
            </h1>
            <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              面向日常运营的后台控制台：先看健康度和收入配置，再进入用户、产品、任务、支持和审计模块处理具体问题。
            </p>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Active Users
              </p>
              <p class="mt-2 text-2xl font-semibold">
                {{ overview?.active_users_count ?? operations?.active_users ?? 0 }}
              </p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                总用户 {{ overview?.users_count ?? operations?.total_users ?? 0 }}
              </p>
            </div>
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Payment Ready
              </p>
              <p class="mt-2 text-2xl font-semibold">
                {{ paymentConfiguredCount }}/{{ paymentProviders.length }}
              </p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                启用 {{ paymentEnabledCount }}，待处理 {{ paymentRiskCount }}
              </p>
            </div>
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Work Queue
              </p>
              <p class="mt-2 text-2xl font-semibold">
                {{ operations?.running_jobs ?? 0 }}
              </p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                失败 {{ overview?.failed_jobs_count ?? operations?.failed_jobs ?? 0 }}
              </p>
            </div>
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Support Risk
              </p>
              <p class="mt-2 text-2xl font-semibold">
                {{ overview?.open_feedback_count ?? diagnostics?.open_feedback_count ?? 0 }}
              </p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                服务异常 {{ serviceRiskCount }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="mx-auto grid max-w-[1500px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[284px_minmax(0,1fr)] lg:px-8">
      <aside class="h-fit rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:sticky lg:top-6">
        <nav class="space-y-5" aria-label="Admin modules">
          <section v-for="group in tabGroups" :key="group.label">
            <p class="px-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
              {{ group.label }}
            </p>
            <div class="mt-2 space-y-1">
              <button
                v-for="tab in group.items"
                :key="tab.id"
                type="button"
                class="group flex w-full items-start gap-3 rounded-md px-3 py-3 text-left transition"
                :class="
                  activeTab === tab.id
                    ? 'bg-slate-950 text-white shadow-sm dark:bg-sky-400 dark:text-slate-950'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                "
                @click="activeTab = tab.id"
              >
                <component :is="tab.icon" class="mt-0.5 h-4 w-4 shrink-0" />
                <span class="min-w-0 flex-1">
                  <span class="block text-sm font-semibold">{{ tab.label }}</span>
                  <span
                    class="mt-1 block text-xs leading-5"
                    :class="
                      activeTab === tab.id
                        ? 'text-white/75 dark:text-slate-950/70'
                        : 'text-slate-500 dark:text-slate-400'
                    "
                  >
                    {{ tab.description }}
                  </span>
                </span>
                <ChevronRight
                  class="mt-0.5 h-4 w-4 shrink-0 opacity-0 transition group-hover:opacity-100"
                  :class="activeTab === tab.id ? 'opacity-100' : ''"
                />
              </button>
            </div>
          </section>
        </nav>
      </aside>

      <section class="min-w-0">
        <div class="mb-5 rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {{ currentTab.group }}
          </p>
          <h2 class="mt-1 text-2xl font-semibold">{{ currentTab.label }}</h2>
          <p class="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {{ currentTab.description }}
          </p>
        </div>

        <div
          v-if="error"
          class="mb-5 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
        >
          <div class="flex items-start gap-3">
            <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" />
            <span>{{ error }}</span>
          </div>
        </div>

        <div
          v-if="success"
          class="mb-5 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200"
        >
          <div class="flex items-start gap-3">
            <CheckCircle2 class="mt-0.5 h-5 w-5 shrink-0" />
            <span>{{ success }}</span>
          </div>
        </div>

        <div
          v-if="loading"
          class="flex min-h-[420px] items-center justify-center rounded-lg border border-slate-200 bg-white p-16 dark:border-slate-800 dark:bg-slate-900"
        >
          <Loader2 class="h-8 w-8 animate-spin text-sky-600 dark:text-sky-300" />
        </div>

        <div v-else>
          <OverviewTab
            v-if="activeTab === 'overview'"
            :overview="overview"
            :operations="operations"
            :jobs="jobs"
            :health-report="healthReport"
            :health-report-summary="buildHealthReportSummary()"
            :health-report-copied="healthReportCopied"
            :saving-key="savingKey"
            :format-date="formatDate"
            @refresh-all="loadAdminData"
            @refresh-health-report="loadHealthReport"
            @copy-health-report="copyHealthReport"
          />

          <UsersTab
            v-else-if="activeTab === 'users'"
            :users="users"
            :password-reset-links="userPasswordResetLinks"
            :user-search="userSearch"
            :saving-key="savingKey"
            :format-date="formatDate"
            @update:user-search="userSearch = $event"
            @search="searchUsers"
            @save="saveUser"
            @toggle-ban="toggleUserBan"
            @create-password-reset-link="createPasswordResetLink"
            @delete="deleteUser"
          />

          <PaymentSetupTab
            v-else-if="activeTab === 'paymentSetup'"
            :payment-summary="paymentSummary"
            :evidence-copied="evidenceCopied"
            :saving-key="savingKey"
            @refresh="loadPayments"
            @copy-evidence="copyPaymentEvidencePacket"
          />

          <PaymentsTab
            v-else-if="activeTab === 'payments'"
            :payment-summary="paymentSummary"
            :payment-provider-filter="paymentProviderFilter"
            :payment-status-filter="paymentStatusFilter"
            :reconciliation-copied="reconciliationCopied"
            :evidence-copied="evidenceCopied"
            :saving-key="savingKey"
            :format-date="formatDate"
            :format-money="formatMoney"
            @update:payment-provider-filter="
              paymentProviderFilter = $event;
              loadPayments()
            "
            @update:payment-status-filter="
              paymentStatusFilter = $event;
              loadPayments()
            "
            @refresh="loadPayments"
            @copy-reconciliation="copyReconciliationSummary"
            @copy-evidence="copyPaymentEvidencePacket"
          />

          <FeatureFlagsTab
            v-else-if="activeTab === 'flags'"
            :flags="flags"
            :saving-key="savingKey"
            @save="saveFlag"
          />

          <SiteSettingsTab
            v-else-if="activeTab === 'settings'"
            :settings="settings"
            :saving-key="savingKey"
            @save="saveSetting"
          />

          <ContentBlocksTab
            v-else-if="activeTab === 'content'"
            :blocks="contentBlocks"
            :selected-content="selectedContent"
            :saving-key="savingKey"
            @select="selectedContent = $event"
            @save="saveContentBlock"
          />

          <JobsTab
            v-else-if="activeTab === 'jobs'"
            :filtered-jobs="filteredJobs"
            :job-search="jobSearch"
            :job-status-filter="jobStatusFilter"
            :saving-key="savingKey"
            :format-date="formatDate"
            @update:job-search="jobSearch = $event"
            @update:job-status-filter="jobStatusFilter = $event"
            @refresh="loadJobs"
          />

          <FeedbackTab
            v-else-if="activeTab === 'feedback'"
            :feedback-reports="feedbackReports"
            :feedback-status-filter="feedbackStatusFilter"
            :highlighted-feedback-id="highlightedFeedbackId"
            :copied-feedback-id="copiedFeedbackId"
            :saving-key="savingKey"
            :format-date="formatDate"
            :parse-diagnostics="parseDiagnostics"
            @update:feedback-status-filter="feedbackStatusFilter = $event"
            @refresh="loadFeedback"
            @cleanup-live="cleanupLiveAcceptanceFeedback"
            @copy-summary="copyFeedbackSummary"
            @save="saveFeedback"
          />

          <ErrorsTab
            v-else-if="activeTab === 'errors'"
            :api-errors="apiErrors"
            :diagnostics="diagnostics"
            :operations="operations"
            :overview="overview"
            :diagnostic-summary-copied="diagnosticSummaryCopied"
            :saving-key="savingKey"
            :format-date="formatDate"
            @refresh="loadDiagnostics"
            @copy-diagnostic-summary="copyDiagnosticSummary"
            @open-feedback="openFeedbackFromDiagnostics"
          />

          <MaintenanceTab
            v-else-if="activeTab === 'maintenance'"
            :maintenance="maintenance"
            :operations="operations"
            :diagnostics="diagnostics"
            :saving-key="savingKey"
            @refresh="refreshMaintenance"
            @cleanup-live="cleanupLiveAcceptanceFeedback"
            @cleanup-test-users="cleanupTestUsers"
            @cleanup-expired-files="cleanupExpiredFiles"
          />

          <SecurityTab v-else-if="activeTab === 'security'" />

          <AuditLogsTab v-else :audit-logs="auditLogs" :format-date="formatDate" />
        </div>
      </section>

      <ConfirmationDialog
        :model-value="!!pendingConfirmation"
        :title="pendingConfirmation?.title || ''"
        :summary="pendingConfirmation?.summary || ''"
        :details="pendingConfirmation?.details || []"
        :confirm-label="pendingConfirmation?.confirmLabel || ''"
        cancel-label="取消"
        :tone="pendingConfirmation?.tone || 'danger'"
        :loading="!!pendingConfirmation && savingKey === pendingConfirmation.savingKey"
        @update:model-value="(value) => { if (!value) closeAdminConfirmation() }"
        @confirm="confirmAdminAction"
      />
    </main>
  </div>
</template>
