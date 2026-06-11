/**
 * API Service for Backend Integration
 * 处理所有与后端的 HTTP 通信
 */
import axios, { AxiosInstance } from 'axios'

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 JWT Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理 Token 过期
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 如果是 401 且不是 refresh 请求，尝试刷新 token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          })

          const { access_token, refresh_token } = response.data
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)

          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh 失败，清除 token 并跳转登录
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/auth/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// ==================== Auth API ====================

export interface RegisterData {
  email: string
  password: string
  full_name: string
}

export interface LoginData {
  email: string
  password: string
  remember?: boolean
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export const authAPI = {
  /**
   * 用户注册
   */
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post<User>('/api/v1/auth/register', data)
    return response.data
  },

  /**
   * 用户登录
   */
  async login(data: LoginData): Promise<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', data.email)
    formData.append('password', data.password)

    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    return response.data
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  /**
   * 刷新 Token
   */
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data
  },

  /**
   * 登出
   */
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  }
}

// ==================== File API ====================

export interface FileUploadResponse {
  file_id: string
  filename: string
  size: number
  mime_type: string
  upload_time: number
}

export interface ProcessingJobResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message?: string
  progress?: number
  result_url?: string
  error?: string
}

export interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: number
  updated_at: number
  progress?: number
  result?: any
  error?: string
}

export const fileAPI = {
  /**
   * 上传文件
   */
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<FileUploadResponse>('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return response.data
  },

  /**
   * 合并 PDF
   */
  async mergePDFs(fileIds: string[], outputFilename?: string): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/merge', {
      file_ids: fileIds,
      output_filename: outputFilename
    })
    return response.data
  },

  /**
   * 拆分 PDF
   */
  async splitPDF(fileId: string, pageRanges: number[][]): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/split', {
      file_id: fileId,
      page_ranges: pageRanges
    })
    return response.data
  },

  /**
   * 压缩 PDF
   */
  async compressPDF(fileId: string, quality: 'low' | 'medium' | 'high'): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/compress', {
      file_id: fileId,
      quality
    })
    return response.data
  },

  /**
   * 旋转 PDF
   */
  async rotatePDF(fileId: string, rotation: 90 | 180 | 270): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/rotate', {
      file_id: fileId,
      rotation
    })
    return response.data
  },

  /**
   * 图片转 PDF
   */
  async imagesToPDF(fileIds: string[], outputFilename?: string): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/images-to-pdf', {
      file_ids: fileIds,
      output_filename: outputFilename
    })
    return response.data
  },

  /**
   * PDF 转图片
   */
  async pdfToImages(fileId: string, format: 'png' | 'jpeg' = 'png'): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/pdf-to-images', {
      file_id: fileId,
      format
    })
    return response.data
  },

  /**
   * OCR 识别
   */
  async extractTextOCR(fileId: string, language: string = 'eng'): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/ocr', {
      file_id: fileId,
      language
    })
    return response.data
  },

  /**
   * Office 文件转 PDF
   */
  async officeToPDF(formData: FormData): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/office-to-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 查询任务状态
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await apiClient.get<JobStatusResponse>(`/api/v1/files/jobs/${jobId}`)
    return response.data
  },

  /**
   * 下载已完成任务的结果（返回 Blob，调用方负责触发浏览器下载）
   */
  async downloadResult(jobId: string): Promise<Blob> {
    const response = await apiClient.get(`/api/v1/files/download/${jobId}`, {
      responseType: 'blob'
    })
    return response.data as Blob
  },

  /**
   * 轮询任务直到完成或失败（默认每 1.5s 一次，最多 ~2 分钟）
   */
  async pollJobUntilDone(
    jobId: string,
    onProgress?: (status: JobStatusResponse) => void,
    intervalMs = 1500,
    maxAttempts = 80
  ): Promise<JobStatusResponse> {
    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getJobStatus(jobId)
      onProgress?.(status)
      if (status.status === 'completed' || status.status === 'failed') {
        return status
      }
      await new Promise((r) => setTimeout(r, intervalMs))
    }
    throw new Error('Job polling timed out')
  },

  /**
   * 取消任务
   */
  async cancelJob(jobId: string): Promise<void> {
    await apiClient.delete(`/api/v1/files/jobs/${jobId}`)
  }
}

// ==================== User API ====================

export interface UserStats {
  total_requests: number
  requests_today: number
  storage_used: number
  quota_remaining: number
  quota_limit: number
  role: string
}

export const userAPI = {
  /**
   * 获取用户统计信息
   */
  async getStats(): Promise<UserStats> {
    const response = await apiClient.get<UserStats>('/api/v1/users/me/stats')
    return response.data
  },

  /**
   * 更新用户信息
   */
  async updateProfile(data: { full_name?: string; email?: string }): Promise<User> {
    const response = await apiClient.patch<User>('/api/v1/users/me', data)
    return response.data
  },

  /**
   * 删除账户
   */
  async deleteAccount(): Promise<void> {
    await apiClient.delete('/api/v1/users/me')
  }
}

// ==================== Hidden Admin API ====================

export interface AdminOverview {
  settings_count: number
  feature_flags_count: number
  content_blocks_count: number
  users_count: number
  active_users_count: number
  admin_users_count: number
  jobs_count: number
  failed_jobs_count: number
  feedback_count: number
  open_feedback_count: number
  api_error_count: number
  recent_audit_logs: AdminAuditLog[]
}

export interface AdminAuditLog {
  id: number
  admin_user_id: number
  action: string
  target_type: string
  target_key: string
  status: string
  detail: string | null
  created_at: string
}

export interface SiteSetting {
  id: number
  key: string
  value: string
  value_type: string
  group: string
  label: string
  description: string | null
  is_public: boolean
  updated_at: string
}

export interface FeatureFlag {
  id: number
  key: string
  label: string
  description: string | null
  enabled: boolean
  requires_login: boolean
  requires_pro: boolean
  maintenance_message: string | null
  updated_at: string
}

export interface ContentBlock {
  id: number
  key: string
  locale: string
  title: string
  content: string
  description: string | null
  is_public: boolean
  updated_at: string
}

export interface AdminUser {
  id: number
  email: string
  full_name: string | null
  role: 'free' | 'pro' | 'enterprise' | 'admin'
  is_active: boolean
  is_verified: boolean
  is_test_account: boolean
  created_at: string
  last_login_at: string | null
}

export interface AdminUserUpdate {
  role?: AdminUser['role']
  is_active?: boolean
  is_verified?: boolean
}

export interface AdminJob {
  id: number | null
  job_id: string
  user_id: number | null
  user_email: string | null
  job_type: string
  status: string
  progress: number
  input_file_name: string
  input_file_size: number
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface AdminApiError {
  id: number
  user_id: number | null
  request_id: string | null
  method: string
  path: string
  query_string: string | null
  status_code: number
  error_type: string | null
  error_message: string | null
  traceback_summary: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface AdminServiceStatus {
  status: string
  detail: string | null
}

export interface AdminOperations {
  generated_at: string
  services: Record<string, AdminServiceStatus>
  total_users: number
  active_users: number
  banned_users: number
  test_users: number
  total_jobs: number
  visible_jobs: number
  failed_jobs: number
  running_jobs: number
  recent_users: AdminUser[]
  recent_failed_jobs: AdminJob[]
  recent_jobs: AdminJob[]
}

export interface AdminDiagnosticFeedbackSummary {
  id: number
  title: string
  status: string
  severity: string
  page_url: string | null
  diagnostic_code: string | null
  created_at: string
}

export interface AdminDiagnostics {
  generated_at: string
  recent_errors: AdminApiError[]
  recent_failed_jobs: AdminJob[]
  recent_feedback: AdminDiagnosticFeedbackSummary[]
  open_feedback_count: number
  failed_jobs_count: number
  api_error_count: number
}

export interface AdminHealthReport {
  generated_at: string
  app_version: string
  environment: string
  migration_version: string | null
  services: Record<string, AdminServiceStatus>
  users_count: number
  active_users_count: number
  open_feedback_count: number
  api_error_count: number
  failed_jobs_count: number
  running_jobs_count: number
  recent_error_path: string | null
  recent_feedback_title: string | null
}

export interface FeedbackCreate {
  title: string
  message: string
  email?: string
  category?: string
  severity?: string
  page_url?: string
  diagnostic_code?: string
  diagnostics?: Record<string, any>
}

export interface FeedbackResponse {
  id: number
  status: string
  diagnostic_code: string | null
  created_at: string
}

export interface AdminFeedback {
  id: number
  user_id: number | null
  email: string | null
  category: string
  severity: string
  status: 'new' | 'reviewing' | 'resolved' | 'closed'
  page_url: string | null
  title: string
  message: string
  diagnostic_code: string | null
  diagnostics: string | null
  admin_note: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
  updated_at: string
}

export interface AdminFeedbackUpdate {
  status?: AdminFeedback['status']
  admin_note?: string | null
}

export interface AdminFeedbackCleanup {
  closed_count: number
  remaining_open_count: number
}

export interface AdminMaintenance {
  test_users_count: number
  live_acceptance_feedback_count: number
  open_feedback_count: number
  api_error_count: number
  failed_jobs_count: number
  running_jobs_count: number
  file_retention: AdminFileRetention
}

export interface AdminFileRetention {
  scanned_count: number
  removable_count: number
  removed_count: number
  removed_bytes: number
  skipped_count: number
  upload_dir: string
}

export interface AdminCleanupTestUsers {
  deleted_count: number
  deleted_emails: string[]
  remaining_test_users_count: number
}

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

  async updateSetting(key: string, data: Omit<SiteSetting, 'id' | 'key' | 'updated_at'>): Promise<SiteSetting> {
    const response = await apiClient.put<SiteSetting>(`/api/v1/admin/settings/${encodeURIComponent(key)}`, data)
    return response.data
  },

  async listFeatureFlags(): Promise<FeatureFlag[]> {
    const response = await apiClient.get<FeatureFlag[]>('/api/v1/admin/feature-flags')
    return response.data
  },

  async updateFeatureFlag(key: string, data: Omit<FeatureFlag, 'id' | 'key' | 'updated_at'>): Promise<FeatureFlag> {
    const response = await apiClient.put<FeatureFlag>(`/api/v1/admin/feature-flags/${encodeURIComponent(key)}`, data)
    return response.data
  },

  async listContentBlocks(): Promise<ContentBlock[]> {
    const response = await apiClient.get<ContentBlock[]>('/api/v1/admin/content-blocks')
    return response.data
  },

  async updateContentBlock(
    key: string,
    locale: string,
    data: Omit<ContentBlock, 'id' | 'key' | 'updated_at'>
  ): Promise<ContentBlock> {
    const response = await apiClient.put<ContentBlock>(
      `/api/v1/admin/content-blocks/${encodeURIComponent(key)}/${encodeURIComponent(locale)}`,
      data
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

  async deleteUser(userId: number): Promise<void> {
    await apiClient.delete(`/api/v1/admin/users/${userId}`)
  },

  async cleanupTestUsers(): Promise<AdminCleanupTestUsers> {
    const response = await apiClient.post<AdminCleanupTestUsers>('/api/v1/admin/users/cleanup-test-users')
    return response.data
  },

  async cleanupExpiredFiles(): Promise<AdminFileRetention> {
    const response = await apiClient.post<AdminFileRetention>('/api/v1/admin/files/cleanup-expired')
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

  async listFeedback(params?: { status_filter?: string; limit?: number }): Promise<AdminFeedback[]> {
    const response = await apiClient.get<AdminFeedback[]>('/api/v1/admin/feedback', { params })
    return response.data
  },

  async updateFeedback(feedbackId: number, data: AdminFeedbackUpdate): Promise<AdminFeedback> {
    const response = await apiClient.patch<AdminFeedback>(`/api/v1/admin/feedback/${feedbackId}`, data)
    return response.data
  },

  async cleanupLiveAcceptanceFeedback(): Promise<AdminFeedbackCleanup> {
    const response = await apiClient.post<AdminFeedbackCleanup>('/api/v1/admin/feedback/cleanup-live-acceptance')
    return response.data
  },

  async listAuditLogs(): Promise<AdminAuditLog[]> {
    const response = await apiClient.get<AdminAuditLog[]>('/api/v1/admin/audit-logs')
    return response.data
  }
}

// ==================== Feedback API ====================

export const feedbackAPI = {
  async create(data: FeedbackCreate): Promise<FeedbackResponse> {
    const response = await apiClient.post<FeedbackResponse>('/api/v1/feedback', data)
    return response.data
  }
}

// ==================== Public Site Config API ====================

export interface PublicFeatureFlag {
  label: string
  description: string | null
  enabled: boolean
  requires_login: boolean
  requires_pro: boolean
  maintenance_message: string | null
}

export interface PublicSiteConfig {
  settings: Record<string, {
    value: string
    value_type: string
    group: string
    label: string
  }>
  feature_flags: Record<string, PublicFeatureFlag>
  content_blocks: Record<string, {
    title: string
    content: string
    description: string | null
  }>
}

export const siteConfigAPI = {
  async getPublicConfig(): Promise<PublicSiteConfig> {
    const response = await apiClient.get<PublicSiteConfig>('/api/v1/admin/public-config')
    return response.data
  }
}

// ==================== Payment API ====================

export interface CheckoutSessionRequest {
  plan: 'monthly' | 'yearly'
  success_url: string
  cancel_url: string
}

export interface CheckoutSessionResponse {
  checkout_url: string
  session_id: string
}

export interface SubscriptionInfo {
  has_subscription: boolean
  status?: string
  plan?: string
  current_period_end?: string
  cancel_at_period_end: boolean
}

export const paymentAPI = {
  /**
   * 创建Stripe结账会话
   */
  async createCheckoutSession(data: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
    const response = await apiClient.post<CheckoutSessionResponse>('/api/v1/payment/create-checkout-session', data)
    return response.data
  },

  /**
   * 获取当前订阅信息
   */
  async getSubscription(): Promise<SubscriptionInfo> {
    const response = await apiClient.get<SubscriptionInfo>('/api/v1/payment/subscription')
    return response.data
  },

  /**
   * 取消订阅
   */
  async cancelSubscription(): Promise<{ message: string; cancel_at: string }> {
    const response = await apiClient.post('/api/v1/payment/cancel-subscription')
    return response.data
  },

  /**
   * 重新激活订阅
   */
  async reactivateSubscription(): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/payment/reactivate-subscription')
    return response.data
  }
}

// ==================== Health API ====================

export const healthAPI = {
  /**
   * 基本健康检查
   */
  async check(): Promise<{ status: string; version: string; environment: string }> {
    const response = await apiClient.get('/health')
    return response.data
  },

  /**
   * 详细健康检查
   */
  async detailed(): Promise<any> {
    const response = await apiClient.get('/api/v1/health/detailed')
    return response.data
  }
}

// ==================== Enterprise API ====================

export interface APIKeyCreate {
  name: string
  rate_limit?: number
  expires_in_days?: number | null
}

export interface APIKeyUpdate {
  name?: string
  is_active?: boolean
  rate_limit?: number
}

export interface APIKeyResponse {
  id: number
  name: string
  key_prefix: string
  is_active: boolean
  rate_limit: number
  last_used_at: string | null
  expires_at: string | null
  created_at: string
  api_key?: string  // Only present on creation
}

export interface APIKeyList {
  keys: APIKeyResponse[]
  total: number
}

export interface UsageStatsResponse {
  period_start: string
  period_end: string
  total_requests: number
  successful_requests: number
  failed_requests: number
  total_files_processed: number
  total_bytes_processed: number
  total_tokens_used: number
  total_cost_cents: number
  endpoint_breakdown: Record<string, number>
  daily_breakdown: Array<{
    date: string
    requests: number
    tokens: number
    cost: number
  }>
}

export interface WebhookCreate {
  url: string
  events: string[]
  secret?: string
  is_active?: boolean
}

export interface WebhookUpdate {
  url?: string
  events?: string[]
  secret?: string
  is_active?: boolean
}

export interface WebhookResponse {
  id: number
  url: string
  events: string[]
  is_active: boolean
  last_triggered_at: string | null
  created_at: string
  updated_at: string
  total_deliveries: number
  successful_deliveries: number
  failed_deliveries: number
}

export interface WebhookList {
  webhooks: WebhookResponse[]
  total: number
}

export interface BillingStatsResponse {
  current_period_start: string
  current_period_end: string
  tokens_used: number
  tokens_included: number
  tokens_overage: number
  subscription_cost: number
  overage_cost: number
  total_cost: number
  next_billing_date: string
  estimated_next_bill: number
}

export interface TokenPricing {
  free_tier_tokens: number
  pro_tier_tokens: number
  enterprise_included_tokens: number
  overage_price_per_1k_tokens: number
}

export interface DashboardStats {
  total_api_keys: number
  active_api_keys: number
  total_requests_30d: number
  total_files_processed_30d: number
  total_bytes_processed_30d: number
  current_month_tokens: number
  current_month_cost_cents: number
  total_webhooks: number
  active_webhooks: number
  rate_limit_hits_today: number
  last_request_at: string | null
  last_api_key_created_at: string | null
}

export const enterpriseAPI = {
  // ===== API Keys =====

  /**
   * 创建 API Key
   */
  async createAPIKey(data: APIKeyCreate): Promise<APIKeyResponse> {
    const response = await apiClient.post<APIKeyResponse>('/api/v1/enterprise/api-keys', data)
    return response.data
  },

  /**
   * 获取 API Key 列表
   */
  async listAPIKeys(): Promise<APIKeyList> {
    const response = await apiClient.get<APIKeyList>('/api/v1/enterprise/api-keys')
    return response.data
  },

  /**
   * 获取单个 API Key
   */
  async getAPIKey(keyId: number): Promise<APIKeyResponse> {
    const response = await apiClient.get<APIKeyResponse>(`/api/v1/enterprise/api-keys/${keyId}`)
    return response.data
  },

  /**
   * 更新 API Key
   */
  async updateAPIKey(keyId: number, data: APIKeyUpdate): Promise<APIKeyResponse> {
    const response = await apiClient.patch<APIKeyResponse>(`/api/v1/enterprise/api-keys/${keyId}`, data)
    return response.data
  },

  /**
   * 删除 API Key
   */
  async deleteAPIKey(keyId: number): Promise<void> {
    await apiClient.delete(`/api/v1/enterprise/api-keys/${keyId}`)
  },

  // ===== Usage Stats =====

  /**
   * 获取使用统计
   */
  async getUsageStats(params?: { start_date?: string; end_date?: string }): Promise<UsageStatsResponse> {
    const response = await apiClient.get<UsageStatsResponse>('/api/v1/enterprise/usage/stats', { params })
    return response.data
  },

  // ===== Webhooks =====

  /**
   * 创建 Webhook
   */
  async createWebhook(data: WebhookCreate): Promise<WebhookResponse> {
    const response = await apiClient.post<WebhookResponse>('/api/v1/enterprise/webhooks', data)
    return response.data
  },

  /**
   * 获取 Webhook 列表
   */
  async listWebhooks(): Promise<WebhookList> {
    const response = await apiClient.get<WebhookList>('/api/v1/enterprise/webhooks')
    return response.data
  },

  /**
   * 获取单个 Webhook
   */
  async getWebhook(webhookId: number): Promise<WebhookResponse> {
    const response = await apiClient.get<WebhookResponse>(`/api/v1/enterprise/webhooks/${webhookId}`)
    return response.data
  },

  /**
   * 更新 Webhook
   */
  async updateWebhook(webhookId: number, data: WebhookUpdate): Promise<WebhookResponse> {
    const response = await apiClient.patch<WebhookResponse>(`/api/v1/enterprise/webhooks/${webhookId}`, data)
    return response.data
  },

  /**
   * 删除 Webhook
   */
  async deleteWebhook(webhookId: number): Promise<void> {
    await apiClient.delete(`/api/v1/enterprise/webhooks/${webhookId}`)
  },

  // ===== Billing =====

  /**
   * 获取计费统计
   */
  async getBillingStats(): Promise<BillingStatsResponse> {
    const response = await apiClient.get<BillingStatsResponse>('/api/v1/enterprise/billing/stats')
    return response.data
  },

  /**
   * 获取定价信息
   */
  async getPricing(): Promise<TokenPricing> {
    const response = await apiClient.get<TokenPricing>('/api/v1/enterprise/billing/pricing')
    return response.data
  },

  // ===== Dashboard =====

  /**
   * 获取仪表板统计
   */
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/api/v1/enterprise/dashboard')
    return response.data
  }
}

// ==================== AI API ====================

export const aiAPI = {
  /**
   * PDF 智能摘要
   */
  async summarize(file: File, length: string = 'medium'): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('length', length)

    const response = await apiClient.post('/api/v1/ai/summarize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      params: { length }
    })
    return response.data
  },

  /**
   * PDF 智能问答
   */
  async ask(file: File, question: string): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('question', question)

    const response = await apiClient.post('/api/v1/ai/ask', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 结构化数据提取
   */
  async extract(file: File, dataType: string = 'general'): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/v1/ai/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      params: { data_type: dataType }
    })
    return response.data
  },

  /**
   * 批量分析
   */
  async batchAnalyze(file: File, operations: string[]): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    operations.forEach((operation) => {
      formData.append('operations', operation)
    })

    const response = await apiClient.post('/api/v1/ai/batch-analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}

/**
 * 高级 PDF API (Pro+)
 */
export const advancedAPI = {
  /**
   * Add an open password to a PDF.
   */
  async protectPDF(file: File, password: string): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('password', password)

    const response = await apiClient.post('/api/v1/advanced/protect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  /**
   * 获取 PDF 表单字段
   */
  async getFormFields(file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/v1/advanced/form/fields', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 填写 PDF 表单
   */
  async fillForm(file: File, formData: Record<string, any>): Promise<Blob> {
    const data = new FormData()
    data.append('file', file)
    data.append('form_data', JSON.stringify(formData))

    const response = await apiClient.post('/api/v1/advanced/form/fill', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  /**
   * 添加文本注释
   */
  async annotateText(
    file: File,
    text: string,
    page: number,
    x: number,
    y: number,
    color: string = '#FF0000'
  ): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('text', text)
    formData.append('page_number', Math.max(0, page - 1).toString())
    formData.append('x', x.toString())
    formData.append('y', y.toString())
    formData.append('color', color)

    const response = await apiClient.post('/api/v1/advanced/annotate/text', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  /**
   * 添加高亮注释
   */
  async annotateHighlight(
    file: File,
    page: number,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color: string = '#FFFF00'
  ): Promise<Blob> {
    const x = Math.min(x1, x2)
    const y = Math.min(y1, y2)
    const width = Math.abs(x2 - x1)
    const height = Math.abs(y2 - y1)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('page_number', Math.max(0, page - 1).toString())
    formData.append('x', x.toString())
    formData.append('y', y.toString())
    formData.append('width', width.toString())
    formData.append('height', height.toString())
    formData.append('color', color)

    const response = await apiClient.post('/api/v1/advanced/annotate/highlight', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  /**
   * 添加签名字段
   */
  async addSignatureField(
    file: File,
    page: number,
    x: number,
    y: number,
    width: number,
    height: number
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('page', page.toString())
    formData.append('x', x.toString())
    formData.append('y', y.toString())
    formData.append('width', width.toString())
    formData.append('height', height.toString())

    const response = await apiClient.post('/api/v1/advanced/signature/field', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 下载处理结果
   */
  async downloadResult(jobId: string, filename: string): Promise<void> {
    const response = await apiClient.get(`/api/v1/files/download/${jobId}`, {
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }
}

// 导出默认实例
export default apiClient
