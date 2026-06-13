import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { watch } from 'vue'
import i18n from '@/i18n'
import { useSettingsStore } from '@/stores/settings'
import { guestGuard, authGuard, enterpriseGuard } from './guards'
import { useSiteConfigStore } from '@/stores/siteConfig'
import { useUserStore } from '@/stores/user'
import { toolRoutes } from '@/data/pdfTools'
import {
  getLocaleByRoutePrefix,
  localeRoutePattern,
  resolvePreferredLocale,
  withLocalePrefix,
  type SupportedLocale,
} from '@/locales/registry'
import { updateRouteSeo } from '@/utils/seo'

const baseRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
  },
  {
    path: '/features',
    name: 'features',
    component: () => import('@/views/Features.vue'),
    meta: { titleKey: 'nav.features' },
  },
  {
    path: '/pricing',
    name: 'pricing',
    component: () => import('@/views/Pricing.vue'),
    meta: { titleKey: 'nav.pricing' },
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('@/views/History.vue'),
    meta: { titleKey: 'history.title' },
  },
  {
    path: '/privacy',
    name: 'privacy-policy',
    component: () => import('@/views/legal/PrivacyPolicy.vue'),
    meta: { titleKey: 'footer.privacyPolicy' },
  },
  {
    path: '/terms',
    name: 'terms-of-service',
    component: () => import('@/views/legal/TermsOfService.vue'),
    meta: { titleKey: 'footer.termsOfService' },
  },
  {
    path: '/auth',
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/Login.vue'),
        beforeEnter: guestGuard,
        meta: { titleKey: 'auth.login' },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/Register.vue'),
        beforeEnter: guestGuard,
        meta: { titleKey: 'auth.register' },
      },
      {
        path: 'forgot-password',
        name: 'forgot-password',
        component: () => import('@/views/auth/ForgotPassword.vue'),
        beforeEnter: guestGuard,
        meta: { titleKey: 'auth.passwordRecoveryTitle' },
      },
      {
        path: 'reset-password',
        name: 'reset-password',
        component: () => import('@/views/auth/ResetPassword.vue'),
        beforeEnter: guestGuard,
        meta: { titleKey: 'auth.resetPasswordTitle' },
      },
      {
        path: 'oauth-callback',
        name: 'oauth-callback',
        component: () => import('@/views/auth/OAuthCallback.vue'),
        meta: { titleKey: 'auth.processingLogin' },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/auth/Profile.vue'),
        beforeEnter: authGuard,
        meta: { titleKey: 'account.myAccount' },
      },
    ],
  },
  {
    path: '/payment',
    children: [
      {
        path: 'success',
        name: 'payment-success',
        component: () => import('@/views/payment/PaymentSuccess.vue'),
        meta: { titleKey: 'payment.success.title' },
      },
      {
        path: 'cancel',
        name: 'payment-cancel',
        component: () => import('@/views/payment/PaymentCancel.vue'),
        meta: { titleKey: 'payment.cancel.title' },
      },
    ],
  },
  {
    path: '/enterprise',
    children: [
      {
        path: 'dashboard',
        name: 'enterprise-dashboard',
        component: () => import('@/views/enterprise/Dashboard.vue'),
        beforeEnter: enterpriseGuard,
        meta: { titleKey: 'enterprise.dashboard.title' },
      },
    ],
  },
  {
    path: '/availability/feature-disabled',
    name: 'feature-disabled',
    component: () => import('@/views/AvailabilityState.vue'),
    meta: { titleKey: 'availability.featureDisabledTitle' },
  },
  {
    path: '/tools',
    component: () => import('@/views/ToolsLayout.vue'),
    children: [
      {
        path: '',
        name: 'tools-center',
        component: () => import('@/views/ToolsCenter.vue'),
        meta: { titleKey: 'nav.tools' },
      },
      ...toolRoutes,
    ],
  },
]

const localeRoutes: RouteRecordRaw[] = [
  {
    path: `/:locale(${localeRoutePattern})`,
    children: [
      ...baseRoutes.map((route) => ({
        ...route,
        path: route.path === '/' ? '' : route.path.replace(/^\//, ''),
      })),
      {
        path: ':pathMatch(.*)*',
        name: 'not-found',
        component: () => import('@/views/AvailabilityState.vue'),
        meta: { titleKey: 'availability.notFoundTitle' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    ...localeRoutes,
    {
      path: '/:pathMatch(.*)*',
      name: 'legacy-locale-redirect',
      component: () => import('@/views/AvailabilityState.vue'),
      meta: { legacyLocaleRedirect: true },
    },
  ],
})

const dynamicImportErrorPattern = /Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module|Loading chunk [\d\w-]+ failed/i

router.onError((error, to) => {
  if (typeof window === 'undefined') {
    return
  }

  const message = error instanceof Error ? error.message : String(error)
  if (!dynamicImportErrorPattern.test(message)) {
    return
  }

  const reloadKey = `pdf-flow:reload:${to.fullPath}`
  if (sessionStorage.getItem(reloadKey) === '1') {
    sessionStorage.removeItem(reloadKey)
    return
  }

  sessionStorage.setItem(reloadKey, '1')
  window.location.assign(to.fullPath)
})

const updateRouteHead = (route = router.currentRoute.value) => {
  const routeLocale = resolveRouteLocale(route) ?? resolvePreferredLocale()
  updateRouteSeo(route, routeLocale, i18n.global.t)
}

// 全局前置守卫 - 设置页面标题
const resolveRouteLocale = (to: { params: Record<string, unknown> }): SupportedLocale | null => {
  const localeParam = to.params.locale
  const prefix = Array.isArray(localeParam) ? localeParam[0] : localeParam
  return typeof prefix === 'string' ? getLocaleByRoutePrefix(prefix) : null
}

router.beforeEach(async (to, _from, next) => {
  const routeLocale = resolveRouteLocale(to)

  if (!routeLocale) {
    const preferredLocale = resolvePreferredLocale()
    next({
      path: withLocalePrefix(to.path, preferredLocale),
      query: to.query,
      hash: to.hash,
      replace: true,
    })
    return
  }

  const settingsStore = useSettingsStore()
  if (settingsStore.locale !== routeLocale || i18n.global.locale.value !== routeLocale) {
    settingsStore.setLocale(routeLocale)
  }

  const featureKey = to.meta.featureKey as string | undefined
  if (featureKey) {
    const siteConfigStore = useSiteConfigStore()
    const userStore = useUserStore()
    await siteConfigStore.fetchPublicConfig(true)
    const flag = siteConfigStore.getFeatureFlag(featureKey, String(to.meta.titleKey || featureKey))

    if (!flag.enabled) {
      next({
        path: withLocalePrefix('/availability/feature-disabled', routeLocale),
        query: {
          state: 'feature-disabled',
          feature: featureKey,
          message: flag.maintenance_message || 'feature_unavailable',
          returnTo: to.fullPath,
        },
      })
      return
    }

    if (flag.requires_login && !userStore.isAuthenticated) {
      const isLoggedIn = await userStore.checkAuth()
      if (!isLoggedIn) {
        next({
          path: withLocalePrefix('/auth/login', routeLocale),
          query: { redirect: to.fullPath },
        })
        return
      }
    }

    if (flag.requires_pro && !userStore.canUseCloudFeatures) {
      next({
        path: withLocalePrefix('/pricing', routeLocale),
        query: { feature: featureKey },
      })
      return
    }
  }

  next()
})

watch(
  () => i18n.global.locale.value,
  () => {
    updateRouteHead()
  },
)

router.afterEach((to) => {
  if (typeof window === 'undefined') {
    return
  }

  sessionStorage.removeItem(`pdf-flow:reload:${to.fullPath}`)
  updateRouteHead(to)
})

export default router
