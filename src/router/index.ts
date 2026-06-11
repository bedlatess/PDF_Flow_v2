import { createRouter, createWebHistory } from 'vue-router'
import { watch } from 'vue'
import i18n from '@/i18n'
import { guestGuard, authGuard, enterpriseGuard, adminGuard, featureFlagGuard } from './guards'

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
      path: '/history',
      name: 'history',
      component: () => import('@/views/History.vue'),
      meta: { title: '处理记录' }
    },
    {
      path: '/privacy',
      name: 'privacy-policy',
      component: () => import('@/views/legal/PrivacyPolicy.vue'),
      meta: { titleKey: 'footer.privacyPolicy' }
    },
    {
      path: '/terms',
      name: 'terms-of-service',
      component: () => import('@/views/legal/TermsOfService.vue'),
      meta: { titleKey: 'footer.termsOfService' }
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
      path: '/control-room',
      name: 'control-room',
      component: () => import('@/views/admin/ControlRoom.vue'),
      beforeEnter: adminGuard,
      meta: { title: 'Control Room' }
    },
    {
      path: '/tools',
      children: [
        {
          path: 'merge',
          name: 'merge-pdf',
          component: () => import('@/views/tools/MergePDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.merge.title', featureKey: 'merge_pdf' }
        },
        {
          path: 'split',
          name: 'split-pdf',
          component: () => import('@/views/tools/SplitPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.split.title', featureKey: 'split_pdf' }
        },
        {
          path: 'rotate',
          name: 'rotate-pdf',
          component: () => import('@/views/tools/RotatePDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.rotate.title', featureKey: 'rotate_pdf' }
        },
        {
          path: 'compress',
          name: 'compress-pdf',
          component: () => import('@/views/tools/CompressPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.compress.title', featureKey: 'compress_pdf' }
        },
        {
          path: 'image-to-pdf',
          name: 'image-to-pdf',
          component: () => import('@/views/tools/ImageToPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.imageToPdf.title', featureKey: 'image_to_pdf' }
        },
        {
          path: 'pdf-to-image',
          name: 'pdf-to-image',
          component: () => import('@/views/tools/PDFToImage.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.pdfToImage.title', featureKey: 'pdf_to_image' }
        },
        {
          path: 'delete-pages',
          name: 'delete-pages-pdf',
          component: () => import('@/views/tools/DeletePagesPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.deletePages.title', featureKey: 'delete_pages_pdf' }
        },
        {
          path: 'organize',
          name: 'organize-pdf',
          component: () => import('@/views/tools/OrganizePDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.organize.title', featureKey: 'organize_pdf' }
        },
        {
          path: 'page-numbers',
          name: 'page-numbers-pdf',
          component: () => import('@/views/tools/PageNumbersPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.pageNumbers.title', featureKey: 'page_numbers_pdf' }
        },
        {
          path: 'protect',
          name: 'protect-pdf',
          component: () => import('@/views/tools/ProtectPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.protect.title', featureKey: 'protect_pdf' }
        },
        {
          path: 'ocr',
          name: 'ocr-pdf',
          component: () => import('@/views/tools/OCRPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.ocr.title', featureKey: 'ocr_pdf' }
        },
        {
          path: 'office-to-pdf',
          name: 'office-to-pdf',
          component: () => import('@/views/tools/OfficeToPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.officeToPdf.title', featureKey: 'office_to_pdf' }
        },
        {
          path: 'ai-analyzer',
          name: 'ai-analyzer',
          component: () => import('@/views/tools/AIPDFAnalyzer.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'ai.title', featureKey: 'ai_analyzer' }
        },
        {
          path: 'watermark',
          name: 'watermark-pdf',
          component: () => import('@/views/tools/WatermarkPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.watermark.title', featureKey: 'watermark_pdf' }
        },
        {
          path: 'fill-form',
          name: 'fill-form-pdf',
          component: () => import('@/views/tools/FillFormPDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.fillForm.title', featureKey: 'fill_form', requiresPro: true }
        },
        {
          path: 'annotate',
          name: 'annotate-pdf',
          component: () => import('@/views/tools/AnnotatePDF.vue'),
          beforeEnter: featureFlagGuard,
          meta: { titleKey: 'tools.annotate.title', featureKey: 'annotate_pdf', requiresPro: true }
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
