import apiClient from '../http'

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

export interface PasswordResetRequestData {
  email: string
}

export interface PasswordResetConfirmData {
  token: string
  new_password: string
}

export interface PasswordChangeData {
  current_password: string
  new_password: string
}

export interface MessageResponse {
  message: string
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
  subscription_status: string | null
  subscription_end_date: string | null
  created_at: string
}

export const authAPI = {
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post<User>('/api/v1/auth/register', data)
    return response.data
  },

  async login(data: LoginData): Promise<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', data.email)
    formData.append('password', data.password)

    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  },

  async forgotPassword(data: PasswordResetRequestData): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/v1/auth/forgot-password', data)
    return response.data
  },

  async resetPassword(data: PasswordResetConfirmData): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/v1/auth/reset-password', data)
    return response.data
  },

  async changePassword(data: PasswordChangeData): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/v1/auth/change-password', data)
    return response.data
  },
}
