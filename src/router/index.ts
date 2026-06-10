import { createRouter, createWebHistory } from 'vue-router'
import { watch } from 'vue'
import i18n from '@/i18n'
import { guestGuard, authGuard, enterpriseGuard } from './guards'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/features',
      name: 'features',
      component: () => import('@/views/Features.vue'),
      meta: { titleKey: 'nav.features' }
    },
    {
      path: '/pricing',
      name: 'pricing',
      component: () => import('@/views/Pricing.vue'),
      meta: { titleKey: 'nav.pricing' }
    },
    {
      path: '/auth',
      children: [
        {
          path: 'login',
          name: 'login',
          component: () => import('@/views/auth/Login.vue'),
          beforeEnter: guestGuard,
          meta: { titleKey: 'auth.login' }
        },
        {
          path: 'register',
          name: 'register',
          component: () => import('@/views/auth/Register.vue'),
          beforeEnter: guestGuard,
          meta: { titleKey: 'auth.register' }
        },
        {
          path: 'oauth-callback',
          name: 'oauth-callback',
          component: () => import('@/views/auth/OAuthCallback.vue'),
          meta: { titleKey: 'auth.processingLogin' }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/auth/Profile.vue'),
          beforeEnter: authGuard,
          meta: { titleKey: 'account.myAccount' }
        }
      ]
    },
    {
      path: '/payment',
      children: [
        {
          path: 'success',
          name: 'payment-success',
          component: () => import('@/views/payment/PaymentSuccess.vue'),
          meta: { titleKey: 'payment.success.title' }
        },
        {
          path: 'cancel',
          name: 'payment-cancel',
          component: () => import('@/views/payment/PaymentCancel.vue'),
          meta: { titleKey: 'payment.cancel.title' }
        }
      ]
    },
    {
      path: '/enterprise',
      children: [
        {
          path: 'dashboard',
          name: 'enterprise-dashboard',
          component: () => import('@/views/enterprise/Dashboard.vue'),
          beforeEnter: enterpriseGuard,
          meta: { titleKey: 'enterprise.dashboard.title' }
        }
      ]
    },
    {
      path: '/tools',
      children: [
        {
          path: 'merge',
          name: 'merge-pdf',
          component: () => import('@/views/tools/MergePDF.vue'),
        },
        {
          path: 'split',
          name: 'split-pdf',
          component: () => import('@/views/tools/SplitPDF.vue'),
        },
        {
          path: 'rotate',
          name: 'rotate-pdf',
          component: () => import('@/views/tools/RotatePDF.vue'),
        },
        {
          path: 'compress',
          name: 'compress-pdf',
          component: () => import('@/views/tools/CompressPDF.vue'),
        },
        {
          path: 'image-to-pdf',
          name: 'image-to-pdf',
          component: () => import('@/views/tools/ImageToPDF.vue'),
        },
        {
          path: 'pdf-to-image',
          name: 'pdf-to-image',
          component: () => import('@/views/tools/PDFToImage.vue'),
        },
        {
          path: 'ocr',
          name: 'ocr-pdf',
          component: () => import('@/views/tools/OCRPDF.vue'),
          meta: { titleKey: 'tools.ocr.title' }
        },
        {
          path: 'office-to-pdf',
          name: 'office-to-pdf',
          component: () => import('@/views/tools/OfficeToPDF.vue'),
          meta: { titleKey: 'tools.officeToPdf.title' }
        },
        {
          path: 'ai-analyzer',
          name: 'ai-analyzer',
          component: () => import('@/views/tools/AIPDFAnalyzer.vue'),
          meta: { titleKey: 'ai.title' }
        },
        {
          path: 'watermark',
          name: 'watermark-pdf',
          component: () => import('@/views/tools/WatermarkPDF.vue'),
          meta: { titleKey: 'tools.watermark.title' }
        },
        {
          path: 'fill-form',
          name: 'fill-form-pdf',
          component: () => import('@/views/tools/FillFormPDF.vue'),
          meta: { titleKey: 'tools.fillForm.title', requiresPro: true }
        },
        {
          path: 'annotate',
          name: 'annotate-pdf',
          component: () => import('@/views/tools/AnnotatePDF.vue'),
          meta: { titleKey: 'tools.annotate.title', requiresPro: true }
        },
      ],
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

const resolveDocumentTitle = (route = router.currentRoute.value) => {
  const titleKey = route.meta.titleKey as string | undefined
  const fallbackTitle = route.meta.title as string | undefined
  const title = titleKey ? i18n.global.t(titleKey) : fallbackTitle
  if (title) {
    document.title = `${title} - PDF-Flow`
  } else {
    document.title = `PDF-Flow - ${i18n.global.t('app.tagline')}`
  }
}

// 全局前置守卫 - 设置页面标题
router.beforeEach((to, _from, next) => {
  resolveDocumentTitle(to)
  next()
})

watch(
  () => i18n.global.locale.value,
  () => {
    resolveDocumentTitle()
  },
)

router.afterEach((to) => {
  if (typeof window === 'undefined') {
    return
  }

  sessionStorage.removeItem(`pdf-flow:reload:${to.fullPath}`)
})

export default router
