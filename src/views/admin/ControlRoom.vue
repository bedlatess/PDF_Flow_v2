<script setup lang="ts">
import { computed, onMounted } from 'vue'
import {
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  ShieldCheck,
} from 'lucide-vue-next'
import {
  riskLevelLabels,
  type AdminModuleDescriptor,
} from '@/admin/control-room/modules'
import type { ControlRoomTabGroup, ControlRoomTabId } from '@/admin/control-room/types'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import AuditLogsTab from '@/components/admin/AuditLogsTab.vue'
import ContentBlocksTab from '@/components/admin/ContentBlocksTab.vue'
import ErrorsTab from '@/components/admin/ErrorsTab.vue'
import FeatureFlagsTab from '@/components/admin/FeatureFlagsTab.vue'
import FeedbackTab from '@/components/admin/FeedbackTab.vue'
import JobsTab from '@/components/admin/JobsTab.vue'
import MaintenanceTab from '@/components/admin/MaintenanceTab.vue'
import OverviewTab from '@/components/admin/OverviewTab.vue'
import PlansPricingTab from '@/components/admin/PlansPricingTab.vue'
import PaymentSetupTab from '@/components/admin/PaymentSetupTab.vue'
import PaymentsTab from '@/components/admin/PaymentsTab.vue'
import SecurityTab from '@/components/admin/SecurityTab.vue'
import ServiceProvidersTab from '@/components/admin/ServiceProvidersTab.vue'
import SiteSettingsTab from '@/components/admin/SiteSettingsTab.vue'
import UsersTab from '@/components/admin/UsersTab.vue'
import AdminStateBlock from '@/components/admin/AdminStateBlock.vue'
import RiskBadge from '@/components/admin/RiskBadge.vue'
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
  pricingPlans,
  serviceProviderConfigs,
  userSearch,
  jobStatusFilter,
  jobSearch,
  paymentProviderFilter,
  paymentStatusFilter,
  serviceProviderServiceFilter,
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
  savePricingPlan,
  loadServiceProviders,
  saveServiceProvider,
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
  const order: ControlRoomTabGroup[] = ['Command', 'Operate', 'Product', 'Revenue', 'System']
  const groups = new Map<ControlRoomTabGroup, typeof tabs>()
  for (const tab of tabs) {
    const groupTabs = groups.get(tab.group) ?? []
    groupTabs.push(tab)
    groups.set(tab.group, groupTabs)
  }
  return order
    .filter((group) => groups.has(group))
    .map((label) => ({ label, items: groups.get(label) ?? [] }))
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
const lockedFlagCount = computed(
  () => flags.value.filter((flag) => flag.requires_login || flag.requires_pro).length,
)
const failedJobCount = computed(
  () => overview.value?.failed_jobs_count ?? operations.value?.failed_jobs ?? 0,
)
const openFeedbackCount = computed(
  () => overview.value?.open_feedback_count ?? diagnostics.value?.open_feedback_count ?? 0,
)
const apiErrorCount = computed(
  () => overview.value?.api_error_count ?? diagnostics.value?.api_error_count ?? 0,
)
const maintenanceRiskCount = computed(
  () =>
    (maintenance.value?.test_users_count ?? 0) +
    (maintenance.value?.live_acceptance_feedback_count ?? 0) +
    (maintenance.value?.file_retention?.removable_count ?? 0),
)
const recentAuditCount = computed(() => auditLogs.value.length)
const serviceProviderReadyCount = computed(
  () =>
    serviceProviderConfigs.value.filter(
      (provider) => provider.enabled && provider.readiness.status === 'ready',
    ).length,
)
const serviceProviderRiskCount = computed(
  () =>
    serviceProviderConfigs.value.filter(
      (provider) => provider.enabled && provider.readiness.status !== 'ready',
    ).length,
)

const systemStatus = computed(() => {
  const hardRisk = serviceRiskCount.value + apiErrorCount.value
  const attention =
    hardRisk +
    paymentRiskCount.value +
    serviceProviderRiskCount.value +
    failedJobCount.value +
    openFeedbackCount.value
  if (hardRisk > 0) return { label: 'Needs attention', tone: 'danger' }
  if (attention > 0) return { label: 'Review recommended', tone: 'warning' }
  return { label: 'Healthy', tone: 'success' }
})

const moduleStatusBadge = (module: AdminModuleDescriptor) => {
  switch (module.statusBadgeSource) {
    case 'systemHealth':
      return systemStatus.value
    case 'serviceRisk':
      return serviceRiskCount.value > 0
        ? { label: `${serviceRiskCount.value} service issue`, tone: 'warning' }
        : { label: 'Healthy', tone: 'success' }
    case 'paymentReadiness':
      return {
        label: `${paymentConfiguredCount.value}/${paymentProviders.value.length}`,
        tone:
          paymentProviders.value.length > 0 &&
          paymentConfiguredCount.value === paymentProviders.value.length
            ? 'success'
            : 'neutral',
      }
    case 'paymentRisk':
      return paymentRiskCount.value > 0
        ? { label: `${paymentRiskCount.value} review`, tone: 'warning' }
        : { label: 'Normal', tone: 'success' }
    case 'lockedFlags':
      return lockedFlagCount.value > 0
        ? { label: `${lockedFlagCount.value} gated`, tone: 'neutral' }
        : null
    case 'serviceProviderReadiness':
      return {
        label: `${serviceProviderReadyCount.value}/${serviceProviderConfigs.value.length}`,
        tone:
          serviceProviderConfigs.value.length > 0 &&
          serviceProviderReadyCount.value === serviceProviderConfigs.value.length
            ? 'success'
            : 'neutral',
      }
    case 'failedJobs':
      return failedJobCount.value > 0
        ? { label: `${failedJobCount.value} failed`, tone: 'warning' }
        : null
    case 'openFeedback':
      return openFeedbackCount.value > 0
        ? { label: `${openFeedbackCount.value} open`, tone: 'warning' }
        : null
    case 'apiErrors':
      return apiErrorCount.value > 0
        ? { label: `${apiErrorCount.value} errors`, tone: 'danger' }
        : null
    case 'maintenanceRisk':
      return maintenanceRiskCount.value > 0
        ? { label: `${maintenanceRiskCount.value} cleanup`, tone: 'warning' }
        : null
    case 'auditRecent':
      return recentAuditCount.value > 0
        ? { label: `${recentAuditCount.value} recent`, tone: 'neutral' }
        : null
    default:
      return null
  }
}

const moduleStatusClass = (tone: string, isActive: boolean) => {
  if (isActive) return 'bg-white/15 text-white dark:bg-slate-950/15 dark:text-slate-950'
  if (tone === 'success') {
    return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200'
  }
  if (tone === 'warning') {
    return 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-200'
  }
  if (tone === 'danger') {
    return 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200'
  }
  return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
}

const riskPanelClass = (module: AdminModuleDescriptor) => {
  if (module.riskLevel === 'critical') return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200'
  if (module.riskLevel === 'high') return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200'
  if (module.riskLevel === 'medium') return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200'
  return 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300'
}

const navigateTo = (tabId: ControlRoomTabId) => {
  activeTab.value = tabId
}

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
              <span
                class="rounded-full px-2.5 py-1"
                :class="moduleStatusClass(systemStatus.tone, false)"
              >
                {{ systemStatus.label }}
              </span>
            </div>
            <h1 class="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              PDF-Flow Admin
            </h1>
            <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              Start with health and attention signals, then move into users, product configuration, revenue, diagnostics, or system controls.
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
                Total users {{ overview?.users_count ?? operations?.total_users ?? 0 }}
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
                Enabled {{ paymentEnabledCount }}, review {{ paymentRiskCount }}
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
                Failed {{ failedJobCount }}
              </p>
            </div>
            <div class="rounded-md border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Support Risk
              </p>
              <p class="mt-2 text-2xl font-semibold">
                {{ openFeedbackCount }}
              </p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Service issues {{ serviceRiskCount }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="mx-auto grid max-w-[1500px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-8">
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
                  <span class="flex flex-wrap items-center gap-2">
                    <span class="block text-sm font-semibold">{{ tab.label }}</span>
                    <RiskBadge :level="tab.riskLevel" compact />
                    <span
                      v-if="moduleStatusBadge(tab)"
                      class="rounded-full px-2 py-0.5 text-[11px] font-semibold leading-4"
                      :class="moduleStatusClass(moduleStatusBadge(tab)!.tone, activeTab === tab.id)"
                    >
                      {{ moduleStatusBadge(tab)!.label }}
                    </span>
                  </span>
                  <span
                    class="mt-1 block text-xs leading-5"
                    :class="
                      activeTab === tab.id
                        ? 'text-white/75 dark:text-slate-950/70'
                        : 'text-slate-500 dark:text-slate-400'
                    "
                  >
                    {{ tab.whenToUse }}
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
          <div class="mt-4 grid gap-3 xl:grid-cols-2">
            <div class="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <p class="font-semibold text-slate-950 dark:text-white">When to use</p>
              <p class="mt-1 leading-6">{{ currentTab.whenToUse }}</p>
            </div>
            <div
              class="rounded-md border p-3 text-sm"
              :class="riskPanelClass(currentTab)"
            >
              <div class="flex items-start gap-2">
                <AlertTriangle v-if="currentTab.riskLevel === 'high' || currentTab.riskLevel === 'critical'" class="mt-0.5 h-4 w-4 shrink-0" />
                <CheckCircle v-else class="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <p class="font-semibold">{{ riskLevelLabels[currentTab.riskLevel] }}</p>
                  <p class="mt-1 leading-6">{{ currentTab.riskNote }}</p>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="currentTab.riskLevel === 'high' || currentTab.riskLevel === 'critical'"
            class="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
          >
            High-impact area: review current state, validation messages, and changed fields before saving.
          </div>
        </div>

        <div
          v-if="error"
          class="mb-5"
        >
          <AdminStateBlock tone="danger" title="Action failed" :description="error" />
        </div>

        <div
          v-if="success"
          class="mb-5"
        >
          <AdminStateBlock tone="success" title="Saved" :description="success" />
        </div>

        <div
          v-if="loading"
          class="min-h-[420px]"
        >
          <AdminStateBlock tone="loading" title="Loading admin console" description="Fetching the latest health, configuration, jobs, users, and diagnostics." />
        </div>

        <div v-else>
          <OverviewTab
            v-if="activeTab === 'overview'"
            :overview="overview"
            :operations="operations"
            :jobs="jobs"
            :flags="flags"
            :health-report="healthReport"
            :health-report-summary="buildHealthReportSummary()"
            :health-report-copied="healthReportCopied"
            :saving-key="savingKey"
            :payment-summary="paymentSummary"
            :service-provider-configs="serviceProviderConfigs"
            :diagnostics="diagnostics"
            :maintenance="maintenance"
            :format-date="formatDate"
            @refresh-all="loadAdminData"
            @refresh-health-report="loadHealthReport"
            @copy-health-report="copyHealthReport"
            @navigate="navigateTo"
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

          <PlansPricingTab
            v-else-if="activeTab === 'plans'"
            :plans="pricingPlans"
            :saving-key="savingKey"
            @save="savePricingPlan"
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

          <ServiceProvidersTab
            v-else-if="activeTab === 'serviceProviders'"
            :service-provider-configs="serviceProviderConfigs"
            :service-filter="serviceProviderServiceFilter"
            :saving-key="savingKey"
            @update:service-filter="serviceProviderServiceFilter = $event"
            @refresh="loadServiceProviders"
            @save="saveServiceProvider"
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
        cancel-label="Cancel"
        :tone="pendingConfirmation?.tone || 'danger'"
        :loading="!!pendingConfirmation && savingKey === pendingConfirmation.savingKey"
        @update:model-value="(value) => { if (!value) closeAdminConfirmation() }"
        @confirm="confirmAdminAction"
      />
    </main>
  </div>
</template>
