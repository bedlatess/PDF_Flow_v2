import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  getLocaleByRoutePrefix,
  resolvePreferredLocale,
  withLocalePrefix,
  type SupportedLocale,
} from '@/locales/registry'

const getRouteLocale = (route: RouteLocationNormalized): SupportedLocale => {
  const localeParam = route.params.locale
  const prefix = Array.isArray(localeParam) ? localeParam[0] : localeParam
  return (typeof prefix === 'string' && getLocaleByRoutePrefix(prefix)) || resolvePreferredLocale()
}

const localePath = (path: string, route: RouteLocationNormalized) =>
  withLocalePrefix(path, getRouteLocale(route))

export async function authGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const userStore = useUserStore()

  if (userStore.isAuthenticated) {
    next()
    return
  }

  const isLoggedIn = await userStore.checkAuth()
  if (isLoggedIn) {
    next()
    return
  }

  next({
    path: localePath('/auth/login', to),
    query: { redirect: to.fullPath },
  })
}

export function guestGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const userStore = useUserStore()

  if (userStore.isAuthenticated) {
    next(localePath('/', to))
    return
  }

  next()
}

export async function proGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const userStore = useUserStore()

  if (!userStore.isAuthenticated) {
    await userStore.checkAuth()
  }

  if (userStore.canUseCloudFeatures) {
    next()
    return
  }

  next({
    path: localePath('/pricing', to),
    query: { feature: (to.meta.featureName as string) || 'pro' },
  })
}

export async function enterpriseGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const userStore = useUserStore()

  if (!userStore.isAuthenticated) {
    await userStore.checkAuth()
  }

  if (userStore.isEnterpriseTier) {
    next()
    return
  }

  next({
    path: localePath('/pricing', to),
    query: { plan: 'enterprise' },
  })
}

export async function adminGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const userStore = useUserStore()

  if (!userStore.isAuthenticated) {
    const isLoggedIn = await userStore.checkAuth()
    if (!isLoggedIn) {
      next({
        path: localePath('/auth/login', to),
        query: { redirect: to.fullPath },
      })
      return
    }
  }

  if (userStore.isAdmin) {
    next()
    return
  }

  next(localePath('/', to))
}
