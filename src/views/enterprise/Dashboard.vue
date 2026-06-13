<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-7xl">
      <!-- Header -->
      <div class="mb-8">
        <p class="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
          Enterprise
        </p>
        <h1 class="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
          {{ t('enterprise.dashboard.title') }}
        </h1>
        <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          {{ t('enterprise.dashboard.subtitle') }}
        </p>
        <div class="mt-5 flex flex-wrap gap-2 text-xs text-slate-600 dark:text-slate-300">
          <span
            v-for="item in overviewLabels"
            :key="item"
            class="rounded border border-slate-200 bg-white px-3 py-1.5 dark:border-slate-800 dark:bg-slate-900"
          >
            {{ item }}
          </span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="space-y-6">
        <Skeleton class="h-32 w-full" />
        <Skeleton class="h-64 w-full" />
        <Skeleton class="h-96 w-full" />
      </div>

      <!-- Dashboard Content -->
      <div v-else class="space-y-6">
        <div
          v-if="dashboardError"
          class="space-y-3"
        >
          <DiagnosticAlert
            :title="dashboardError.title"
            :message="dashboardError.message"
            :diagnostic-code="dashboardError.diagnosticCode"
            :support-hint="t('enterprise.dashboard.failureHint')"
            tone="warning"
          />
          <Button
            variant="outline"
            size="sm"
            :loading="loading"
            @click="loadDashboardStats"
          >
            {{ t('enterprise.dashboard.retry') }}
          </Button>
        </div>

        <!-- Overview Stats -->
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            :title="t('enterprise.stats.apiKeys')"
            :value="dashboardStats?.active_api_keys || 0"
            :subtitle="`${dashboardStats?.total_api_keys || 0} ${t('enterprise.stats.total')}`"
            icon="key"
            color="blue"
          />
          <StatCard
            :title="t('enterprise.stats.requests30d')"
            :value="formatNumber(dashboardStats?.total_requests_30d || 0)"
            :subtitle="t('enterprise.stats.last30Days')"
            icon="activity"
            color="green"
          />
          <StatCard
            :title="t('enterprise.stats.tokens')"
            :value="formatNumber(dashboardStats?.current_month_tokens || 0)"
            :subtitle="t('enterprise.stats.thisMonth')"
            icon="zap"
            color="violet"
          />
          <StatCard
            :title="t('enterprise.stats.cost')"
            :value="`$${((dashboardStats?.current_month_cost_cents || 0) / 100).toFixed(2)}`"
            :subtitle="t('enterprise.stats.thisMonth')"
            icon="dollar-sign"
            color="orange"
          />
        </div>

        <!-- Tabs -->
        <div class="overflow-hidden rounded-md border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div class="border-b border-slate-200 dark:border-slate-700">
            <nav class="flex gap-1 overflow-x-auto px-4 sm:px-6" aria-label="Tabs">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                  'whitespace-nowrap border-b-2 px-4 py-4 text-sm font-medium transition-colors',
                  activeTab === tab.id
                    ? 'border-sky-500 text-sky-700 dark:text-sky-300'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                ]"
              >
                {{ tab.label }}
              </button>
            </nav>
          </div>

          <div class="p-4 sm:p-6">
            <!-- API Keys Tab -->
            <div v-if="activeTab === 'api-keys'">
              <APIKeysManager />
            </div>

            <!-- Usage Tab -->
            <div v-else-if="activeTab === 'usage'">
              <UsageStats />
            </div>

            <!-- Webhooks Tab -->
            <div v-else-if="activeTab === 'webhooks'">
              <WebhookManager />
            </div>

            <!-- Billing Tab -->
            <div v-else-if="activeTab === 'billing'">
              <BillingStats />
            </div>

            <!-- Documentation Tab -->
            <div v-else-if="activeTab === 'docs'">
              <APIDocumentation />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { enterpriseAPI } from '@/services/api'
import Skeleton from '@/components/common/Skeleton.vue'
import Button from '@/components/common/Button.vue'
import DiagnosticAlert from '@/components/common/DiagnosticAlert.vue'
import StatCard from '@/components/enterprise/StatCard.vue'
import APIKeysManager from '@/components/enterprise/APIKeysManager.vue'
import UsageStats from '@/components/enterprise/UsageStats.vue'
import WebhookManager from '@/components/enterprise/WebhookManager.vue'
import BillingStats from '@/components/enterprise/BillingStats.vue'
import APIDocumentation from '@/components/enterprise/APIDocumentation.vue'
import { formatUserFacingError, type FormattedUserError } from '@/utils/error-messages'
import { useLocalePath } from '@/composables/useLocalePath'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const { localePath } = useLocalePath()

const loading = ref(true)
const activeTab = ref('api-keys')
const dashboardStats = ref<any>(null)
const dashboardError = ref<FormattedUserError | null>(null)

const tabs = computed(() => [
  { id: 'api-keys', label: t('enterprise.tabs.apiKeys') },
  { id: 'usage', label: t('enterprise.tabs.usage') },
  { id: 'webhooks', label: t('enterprise.tabs.webhooks') },
  { id: 'billing', label: t('enterprise.tabs.billing') },
  { id: 'docs', label: t('enterprise.tabs.documentation') }
])

const overviewLabels = computed(() => [
  t('enterprise.tabs.apiKeys'),
  t('enterprise.tabs.usage'),
  t('enterprise.tabs.webhooks'),
  t('enterprise.tabs.billing'),
  t('enterprise.tabs.documentation')
])

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

const loadDashboardStats = async () => {
  try {
    dashboardError.value = null
    loading.value = true
    const response = await enterpriseAPI.getDashboardStats()
    dashboardStats.value = response
  } catch (error: any) {
    // Redirect if not enterprise user
    if (error.response?.status === 403) {
      router.push(localePath('/pricing'))
      return
    }

    dashboardError.value = formatUserFacingError(error, {
      area: 'ENTERPRISE',
      fallbackTitle: t('enterprise.dashboard.failureTitle'),
      fallbackMessage: t('enterprise.dashboard.failureMessage'),
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Check if user is enterprise
  if (!userStore.isEnterpriseTier) {
    router.push(localePath('/pricing'))
    return
  }

  loadDashboardStats()
})
</script>
