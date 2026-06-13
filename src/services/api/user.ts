import apiClient from '../http'
import type { User } from './auth'

export interface UserStats {
  total_requests: number
  requests_today: number
  storage_used: number
  quota_remaining: number
  quota_limit: number
  role: string
}

export const userAPI = {
  async getStats(): Promise<UserStats> {
    const response = await apiClient.get<UserStats>('/api/v1/users/me/stats')
    return response.data
  },

  async updateProfile(data: { full_name?: string; email?: string }): Promise<User> {
    const response = await apiClient.patch<User>('/api/v1/users/me', data)
    return response.data
  },

  async deleteAccount(): Promise<void> {
    await apiClient.delete('/api/v1/users/me')
  },
}
