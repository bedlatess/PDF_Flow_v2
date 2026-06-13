<script setup lang="ts">
import { onMounted } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  EyeOff,
  Loader2,
  SlidersHorizontal,
} from 'lucide-vue-next'
import AdminPanel from '@/components/admin/AdminPanel.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import AuditLogsTab from '@/components/admin/AuditLogsTab.vue'
import ContentBlocksTab from '@/components/admin/ContentBlocksTab.vue'
import ErrorsTab from '@/components/admin/ErrorsTab.vue'
import FeatureFlagsTab from '@/components/admin/FeatureFlagsTab.vue'
import FeedbackTab from '@/components/admin/FeedbackTab.vue'
import JobsTab from '@/components/admin/JobsTab.vue'
import MaintenanceTab from '@/components/admin/MaintenanceTab.vue'
import OverviewTab from '@/components/admin/OverviewTab.vue'
import PaymentsTab from '@/components/admin/PaymentsTab.vue'
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
  enabledFlagCount,
  lockedFlagCount,
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

onMounted(loadAdminData)
</script>
<template>
  <div class="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-white">
    <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <AdminPanel as="section" padding="lg" class="shadow-sm">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div
              class="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200"
            >
              <EyeOff class="h-4 w-4" />
              Hidden Operations
            </div>
            <h1 class="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
              PDF-Flow Control Room
            </h1>
            <p
              class="mt-4 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-base"
            >
              这是隐藏后台的第一阶段。这里不会出现在普通用户导航里，但真正的保护来自后端 ADMIN
              权限、接口鉴权和审计日志。
            </p>
          </div>

          <div class="grid grid-cols-2 gap-3 text-center sm:grid-cols-6">
            <AdminPanel as="div" padding="sm">
              <p class="text-2xl font-semibold">{{ enabledFlagCount }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">已开启</p>
            </AdminPanel>
            <AdminPanel as="div" padding="sm">
              <p class="text-2xl font-semibold">{{ lockedFlagCount }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">受限功能</p>
            </AdminPanel>
            <AdminPanel as="div" padding="sm">
              <p class="text-2xl font-semibold">{{ overview?.content_blocks_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">内容块</p>
            </AdminPanel>
            <AdminPanel as="div" padding="sm">
              <p class="text-2xl font-semibold">{{ overview?.active_users_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">活跃用户</p>
            </AdminPanel>
            <AdminPanel as="div" padding="sm">
              <p class="text-2xl font-semibold">{{ overview?.failed_jobs_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">失败任务</p>
            </AdminPanel>
            <AdminPanel as="div" padding="sm">
              <p class="text-2xl font-semibold">{{ overview?.open_feedback_count ?? 0 }}</p>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">待处理反馈</p>
            </AdminPanel>
          </div>
        </div>
      </AdminPanel>

      <AdminPanel
        v-if="error"
        as="div"
        tone="danger"
        padding="sm"
        class="mt-6 text-sm text-rose-700 dark:text-rose-200"
      >
        <div class="flex items-start gap-3">
          <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" />
          <span>{{ error }}</span>
        </div>
      </AdminPanel>

      <AdminPanel
        v-if="success"
        as="div"
        tone="success"
        padding="sm"
        class="mt-6 text-sm text-emerald-700 dark:text-emerald-200"
      >
        <div class="flex items-start gap-3">
          <CheckCircle2 class="mt-0.5 h-5 w-5 shrink-0" />
          <span>{{ success }}</span>
        </div>
      </AdminPanel>

      <div
        v-if="loading"
        class="mt-10 flex items-center justify-center rounded-lg border border-slate-200 bg-white p-16 dark:border-slate-800 dark:bg-slate-900"
      >
        <Loader2 class="h-8 w-8 animate-spin text-sky-600 dark:text-sky-300" />
      </div>

      <section v-else class="mt-8 grid gap-6 lg:grid-cols-[260px_1fr]">
        <AdminPanel as="aside" padding="sm">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="flex w-full items-center gap-3 rounded-md px-4 py-3 text-left text-sm transition"
            :class="
              activeTab === tab.id
                ? 'bg-slate-950 text-white shadow-sm dark:bg-sky-400 dark:text-slate-950'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
            "
            @click="activeTab = tab.id"
          >
            <component :is="tab.icon" class="h-4 w-4" />
            <span class="font-semibold">{{ tab.label }}</span>
          </button>
        </AdminPanel>

        <div class="min-w-0">
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

          <AuditLogsTab v-else :audit-logs="auditLogs" :format-date="formatDate" />
        </div>
      </section>

      <section
        class="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm leading-7 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100"
      >
        <div class="flex items-start gap-3">
          <SlidersHorizontal class="mt-1 h-5 w-5 shrink-0" />
          <p>
            当前阶段已经能通过后台维护配置、功能开关和内容块。下一阶段需要把公开页面和工具页统一接入这些后端开关，让“关闭功能
            / 维护提示 / 登录要求 / Pro 要求”真正影响用户界面和 API 行为。
          </p>
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
