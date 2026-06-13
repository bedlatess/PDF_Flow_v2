import apiClient from '../http'

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
  api_key?: string
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
  async createAPIKey(data: APIKeyCreate): Promise<APIKeyResponse> {
    const response = await apiClient.post<APIKeyResponse>('/api/v1/enterprise/api-keys', data)
    return response.data
  },

  async listAPIKeys(): Promise<APIKeyList> {
    const response = await apiClient.get<APIKeyList>('/api/v1/enterprise/api-keys')
    return response.data
  },

  async getAPIKey(keyId: number): Promise<APIKeyResponse> {
    const response = await apiClient.get<APIKeyResponse>(
      `/api/v1/enterprise/api-keys/${keyId}`,
    )
    return response.data
  },

  async updateAPIKey(keyId: number, data: APIKeyUpdate): Promise<APIKeyResponse> {
    const response = await apiClient.patch<APIKeyResponse>(
      `/api/v1/enterprise/api-keys/${keyId}`,
      data,
    )
    return response.data
  },

  async deleteAPIKey(keyId: number): Promise<void> {
    await apiClient.delete(`/api/v1/enterprise/api-keys/${keyId}`)
  },

  async getUsageStats(params?: {
    start_date?: string
    end_date?: string
  }): Promise<UsageStatsResponse> {
    const response = await apiClient.get<UsageStatsResponse>(
      '/api/v1/enterprise/usage/stats',
      { params },
    )
    return response.data
  },

  async createWebhook(data: WebhookCreate): Promise<WebhookResponse> {
    const response = await apiClient.post<WebhookResponse>('/api/v1/enterprise/webhooks', data)
    return response.data
  },

  async listWebhooks(): Promise<WebhookList> {
    const response = await apiClient.get<WebhookList>('/api/v1/enterprise/webhooks')
    return response.data
  },

  async getWebhook(webhookId: number): Promise<WebhookResponse> {
    const response = await apiClient.get<WebhookResponse>(
      `/api/v1/enterprise/webhooks/${webhookId}`,
    )
    return response.data
  },

  async updateWebhook(webhookId: number, data: WebhookUpdate): Promise<WebhookResponse> {
    const response = await apiClient.patch<WebhookResponse>(
      `/api/v1/enterprise/webhooks/${webhookId}`,
      data,
    )
    return response.data
  },

  async deleteWebhook(webhookId: number): Promise<void> {
    await apiClient.delete(`/api/v1/enterprise/webhooks/${webhookId}`)
  },

  async getBillingStats(): Promise<BillingStatsResponse> {
    const response = await apiClient.get<BillingStatsResponse>(
      '/api/v1/enterprise/billing/stats',
    )
    return response.data
  },

  async getPricing(): Promise<TokenPricing> {
    const response = await apiClient.get<TokenPricing>('/api/v1/enterprise/billing/pricing')
    return response.data
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/api/v1/enterprise/dashboard')
    return response.data
  },
}
