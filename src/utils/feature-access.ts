import type { Router, RouteLocationNormalizedLoaded } from 'vue-router'
import {
  getLocaleByRoutePrefix,
  resolvePreferredLocale,
  withLocalePrefix,
  type SupportedLocale,
} from '@/locales/registry'

interface FeatureAccessParams {
  router: Router
  route: RouteLocationNormalizedLoaded
  isAuthenticated: boolean
  canUseCloudFeatures?: boolean
  requiresPro?: boolean
  pricingFeature?: string
}

const getRouteLocale = (route: RouteLocationNormalizedLoaded): SupportedLocale => {
  const localeParam = route.params.locale
  const prefix = Array.isArray(localeParam) ? localeParam[0] : localeParam
  return (typeof prefix === 'string' && getLocaleByRoutePrefix(prefix)) || resolvePreferredLocale()
}

const localePath = (path: string, route: RouteLocationNormalizedLoaded) =>
  withLocalePrefix(path, getRouteLocale(route))

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
      path: localePath('/auth/login', route),
      query: { redirect: route.fullPath },
    })
    return false
  }

  if (requiresPro && !canUseCloudFeatures) {
    router.push({
      path: localePath('/pricing', route),
      query: { feature: pricingFeature || String(route.name || 'pro') },
    })
    return false
  }

  return true
}
