import apiClient from '../http'

export interface PublicFeatureFlag {
  label: string
  description: string | null
  enabled: boolean
  is_public: boolean
  requires_login: boolean
  requires_pro: boolean
  maintenance_message: string | null
  free_daily_limit: number | null
  free_max_file_size_mb: number | null
  free_batch_file_limit: number | null
  pro_daily_limit: number | null
  pro_max_file_size_mb: number | null
  pro_batch_file_limit: number | null
  pro_unlimited: boolean
}

export type PublicOAuthProviderKey = 'google' | 'github'

export interface PublicOAuthProvider {
  label: string
  enabled: boolean
}

export interface PublicSiteConfig {
  settings: Record<
    string,
    {
      value: string
      value_type: string
      group: string
      label: string
    }
  >
  feature_flags: Record<string, PublicFeatureFlag>
  content_blocks: Record<
    string,
    {
      title: string
      content: string
      description: string | null
    }
  >
  oauth_providers?: Partial<Record<PublicOAuthProviderKey, PublicOAuthProvider>>
}

export const siteConfigAPI = {
  async getPublicConfig(): Promise<PublicSiteConfig> {
    const response = await apiClient.get<PublicSiteConfig>('/api/v1/admin/public-config')
    return response.data
  },
}
