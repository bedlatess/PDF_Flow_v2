import apiClient from '@/services/http'
import type {
  AdminApiError,
  AdminAuditLog,
  AdminCleanupTestUsers,
  AdminDiagnostics,
  AdminFeedback,
  AdminFeedbackCleanup,
  AdminFeedbackUpdate,
  AdminFileRetention,
  AdminHealthReport,
  AdminJob,
  AdminMaintenance,
  AdminOperations,
  AdminPasswordResetLink,
  AdminOverview,
  AdminPaymentProviderConfig,
  AdminPaymentProviderConfigUpdate,
  AdminPaymentProviderConfigValidation,
  AdminPaymentSummary,
  AdminUser,
  AdminUserUpdate,
  ContentBlock,
  FeatureFlag,
  SiteSetting,
} from './types'

export const adminAPI = {
  async getOverview(): Promise<AdminOverview> {
    const response = await apiClient.get<AdminOverview>('/api/v1/admin/overview')
    return response.data
  },

  async getOperations(): Promise<AdminOperations> {
    const response = await apiClient.get<AdminOperations>('/api/v1/admin/operations')
    return response.data
  },

  async listSettings(): Promise<SiteSetting[]> {
    const response = await apiClient.get<SiteSetting[]>('/api/v1/admin/settings')
    return response.data
  },

  async updateSetting(
    key: string,
    data: Omit<SiteSetting, 'id' | 'key' | 'updated_at'>,
  ): Promise<SiteSetting> {
    const response = await apiClient.put<SiteSetting>(
      `/api/v1/admin/settings/${encodeURIComponent(key)}`,
      data,
    )
    return response.data
  },

  async listFeatureFlags(): Promise<FeatureFlag[]> {
    const response = await apiClient.get<FeatureFlag[]>('/api/v1/admin/feature-flags')
    return response.data
  },

  async updateFeatureFlag(
    key: string,
    data: Omit<FeatureFlag, 'id' | 'key' | 'updated_at'>,
  ): Promise<FeatureFlag> {
    const response = await apiClient.put<FeatureFlag>(
      `/api/v1/admin/feature-flags/${encodeURIComponent(key)}`,
      data,
    )
    return response.data
  },

  async listContentBlocks(): Promise<ContentBlock[]> {
    const response = await apiClient.get<ContentBlock[]>('/api/v1/admin/content-blocks')
    return response.data
  },

  async updateContentBlock(
    key: string,
    locale: string,
    data: Omit<ContentBlock, 'id' | 'key' | 'updated_at'>,
  ): Promise<ContentBlock> {
    const response = await apiClient.put<ContentBlock>(
      `/api/v1/admin/content-blocks/${encodeURIComponent(key)}/${encodeURIComponent(locale)}`,
      data,
    )
    return response.data
  },

  async listUsers(params?: { search?: string; limit?: number }): Promise<AdminUser[]> {
    const response = await apiClient.get<AdminUser[]>('/api/v1/admin/users', { params })
    return response.data
  },

  async updateUser(userId: number, data: AdminUserUpdate): Promise<AdminUser> {
    const response = await apiClient.patch<AdminUser>(`/api/v1/admin/users/${userId}`, data)
    return response.data
  },

  async createUserPasswordResetLink(userId: number): Promise<AdminPasswordResetLink> {
    const response = await apiClient.post<AdminPasswordResetLink>(
      `/api/v1/admin/users/${userId}/password-reset-link`,
    )
    return response.data
  },

  async deleteUser(userId: number): Promise<void> {
    await apiClient.delete(`/api/v1/admin/users/${userId}`)
  },

  async cleanupTestUsers(): Promise<AdminCleanupTestUsers> {
    const response = await apiClient.post<AdminCleanupTestUsers>(
      '/api/v1/admin/users/cleanup-test-users',
    )
    return response.data
  },

  async cleanupExpiredFiles(): Promise<AdminFileRetention> {
    const response = await apiClient.post<AdminFileRetention>(
      '/api/v1/admin/files/cleanup-expired',
    )
    return response.data
  },

  async listJobs(params?: { status_filter?: string; limit?: number }): Promise<AdminJob[]> {
    const response = await apiClient.get<AdminJob[]>('/api/v1/admin/jobs', { params })
    return response.data
  },

  async listErrors(params?: { limit?: number }): Promise<AdminApiError[]> {
    const response = await apiClient.get<AdminApiError[]>('/api/v1/admin/errors', { params })
    return response.data
  },

  async getDiagnostics(): Promise<AdminDiagnostics> {
    const response = await apiClient.get<AdminDiagnostics>('/api/v1/admin/diagnostics')
    return response.data
  },

  async getMaintenance(): Promise<AdminMaintenance> {
    const response = await apiClient.get<AdminMaintenance>('/api/v1/admin/maintenance')
    return response.data
  },

  async getHealthReport(): Promise<AdminHealthReport> {
    const response = await apiClient.get<AdminHealthReport>('/api/v1/admin/health-report')
    return response.data
  },

  async getPaymentSummary(params?: {
    provider?: string
    status_filter?: string
    limit?: number
  }): Promise<AdminPaymentSummary> {
    const response = await apiClient.get<AdminPaymentSummary>('/api/v1/admin/payments', {
      params,
    })
    return response.data
  },

  async listPaymentConfigs(): Promise<AdminPaymentProviderConfig[]> {
    const response = await apiClient.get<AdminPaymentProviderConfig[]>(
      '/api/v1/admin/payment-configs',
    )
    return response.data
  },

  async updatePaymentConfig(
    providerKey: string,
    data: AdminPaymentProviderConfigUpdate,
  ): Promise<AdminPaymentProviderConfig> {
    const response = await apiClient.put<AdminPaymentProviderConfig>(
      `/api/v1/admin/payment-configs/${encodeURIComponent(providerKey)}`,
      data,
    )
    return response.data
  },

  async validatePaymentConfig(
    providerKey: string,
    data: AdminPaymentProviderConfigUpdate,
  ): Promise<AdminPaymentProviderConfigValidation> {
    const response = await apiClient.post<AdminPaymentProviderConfigValidation>(
      `/api/v1/admin/payment-configs/${encodeURIComponent(providerKey)}/validate`,
      data,
    )
    return response.data
  },

  async listFeedback(params?: { status_filter?: string; limit?: number }): Promise<AdminFeedback[]> {
    const response = await apiClient.get<AdminFeedback[]>('/api/v1/admin/feedback', { params })
    return response.data
  },

  async updateFeedback(feedbackId: number, data: AdminFeedbackUpdate): Promise<AdminFeedback> {
    const response = await apiClient.patch<AdminFeedback>(
      `/api/v1/admin/feedback/${feedbackId}`,
      data,
    )
    return response.data
  },

  async cleanupLiveAcceptanceFeedback(): Promise<AdminFeedbackCleanup> {
    const response = await apiClient.post<AdminFeedbackCleanup>(
      '/api/v1/admin/feedback/cleanup-live-acceptance',
    )
    return response.data
  },

  async listAuditLogs(): Promise<AdminAuditLog[]> {
    const response = await apiClient.get<AdminAuditLog[]>('/api/v1/admin/audit-logs')
    return response.data
  },
}
