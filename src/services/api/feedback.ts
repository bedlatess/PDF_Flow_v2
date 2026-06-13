import apiClient from '../http'

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

export const feedbackAPI = {
  async create(data: FeedbackCreate): Promise<FeedbackResponse> {
    const response = await apiClient.post<FeedbackResponse>('/api/v1/feedback', data)
    return response.data
  },
}
