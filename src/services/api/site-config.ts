import apiClient from '../http'

export interface PublicFeatureFlag {
  label: string
  description: string | null
  enabled: boolean
  requires_login: boolean
  requires_pro: boolean
  maintenance_message: string | null
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
}

export const siteConfigAPI = {
  async getPublicConfig(): Promise<PublicSiteConfig> {
    const response = await apiClient.get<PublicSiteConfig>('/api/v1/admin/public-config')
    return response.data
  },
}
