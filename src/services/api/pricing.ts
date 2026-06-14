import apiClient from '../http'

export type PricingPlanKey = 'free' | 'pro_monthly' | 'pro_yearly' | 'enterprise'

export interface PricingProviderMappings {
  stripe: {
    price_id: string
  }
  paypal: {
    plan_id: string
    product_id: string
  }
  gmpay: {
    amount_cents: number
    currency: string
    token: string
    network: string
  }
}

export interface PublicPricingPlan {
  plan_key: PricingPlanKey
  display_name: string
  is_public: boolean
  price_amount_cents: number
  display_price: string
  currency: string
  billing_interval: 'none' | 'month' | 'year' | 'custom' | string
  description: string | null
  provider_mappings: PricingProviderMappings
  sort_order: number
  highlighted: boolean
  updated_at?: string | null
}

export interface PublicPricingPlanList {
  source: string
  plans: PublicPricingPlan[]
}

export const pricingAPI = {
  async listPlans(): Promise<PublicPricingPlanList> {
    const response = await apiClient.get<PublicPricingPlanList>('/api/v1/pricing/plans')
    return response.data
  },
}
