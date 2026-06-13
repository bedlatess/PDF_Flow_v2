import apiClient from '../http'

export const healthAPI = {
  async check(): Promise<{ status: string; version: string; environment: string }> {
    const response = await apiClient.get('/health')
    return response.data
  },

  async detailed(): Promise<any> {
    const response = await apiClient.get('/api/v1/health/detailed')
    return response.data
  },
}
