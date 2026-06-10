import type { Router, RouteLocationNormalizedLoaded } from 'vue-router'

interface FeatureAccessParams {
  router: Router
  route: RouteLocationNormalizedLoaded
  isAuthenticated: boolean
  canUseCloudFeatures?: boolean
  requiresPro?: boolean
  pricingFeature?: string
}

export function redirectForFeatureAccess({
  router,
  route,
  isAuthenticated,
  canUseCloudFeatures = false,
  requiresPro = false,
  pricingFeature,
}: FeatureAccessParams) {
  if (!isAuthenticated) {
    router.push({
      path: '/auth/login',
      query: { redirect: route.fullPath },
    })
    return false
  }

  if (requiresPro && !canUseCloudFeatures) {
    router.push({
      path: '/pricing',
      query: { feature: pricingFeature || String(route.name || 'pro') },
    })
    return false
  }

  return true
}
