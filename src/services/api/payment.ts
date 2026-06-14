import apiClient from '../http'

export interface CheckoutSessionRequest {
  plan: 'monthly' | 'yearly'
  success_url: string
  cancel_url: string
  provider?: PaymentProviderKey
}

export interface CheckoutSessionResponse {
  checkout_url: string
  session_id: string
  provider: PaymentProviderKey
  order_id: string
  merchant_order_id: string
  qr_code_url?: string | null
  expires_at?: string | null
}

export type PaymentProviderKey =
  | 'stripe'
  | 'paypal'
  | 'epay'
  | 'alipay'
  | 'wechat'
  | 'tokenpay'
  | 'bepusdt'
  | 'epusdt'
  | 'okpay'
  | 'gmpay'

export interface PaymentProviderOption {
  key: PaymentProviderKey
  enabled: boolean
  display_name: string
  settlement: string
  supports_subscription: boolean
  supports_one_time: boolean
}

export interface PaymentProviderList {
  providers: PaymentProviderOption[]
}

export interface PaymentCaptureResponse {
  provider: PaymentProviderKey
  order_id: string
  merchant_order_id: string
  status: string
  current_period_end?: string | null
}

export interface SubscriptionInfo {
  has_subscription: boolean
  status?: string
  plan?: string
  current_period_end?: string
  cancel_at_period_end: boolean
}

export const paymentAPI = {
  async createCheckoutSession(
    data: CheckoutSessionRequest,
  ): Promise<CheckoutSessionResponse> {
    const response = await apiClient.post<CheckoutSessionResponse>(
      '/api/v1/payment/create-checkout-session',
      data,
    )
    return response.data
  },

  async listProviders(): Promise<PaymentProviderList> {
    const response = await apiClient.get<PaymentProviderList>('/api/v1/payment/providers')
    return response.data
  },

  async captureOrder(merchantOrderId: string): Promise<PaymentCaptureResponse> {
    const response = await apiClient.post<PaymentCaptureResponse>(
      `/api/v1/payment/orders/${merchantOrderId}/capture`,
    )
    return response.data
  },

  async getSubscription(): Promise<SubscriptionInfo> {
    const response = await apiClient.get<SubscriptionInfo>('/api/v1/payment/subscription')
    return response.data
  },

  async cancelSubscription(): Promise<{ message: string; cancel_at: string }> {
    const response = await apiClient.post('/api/v1/payment/cancel-subscription')
    return response.data
  },

  async reactivateSubscription(): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/payment/reactivate-subscription')
    return response.data
  },
}
