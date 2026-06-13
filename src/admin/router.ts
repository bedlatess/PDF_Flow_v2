import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'admin-control-room',
    component: () => import('@/views/admin/ControlRoom.vue'),
    meta: { title: 'PDF-Flow Admin' },
  },
  {
    path: '/access',
    name: 'admin-access-state',
    component: () => import('@/admin/AdminAccessState.vue'),
    meta: { title: 'Admin Access' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory('/'),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  if (to.name === 'admin-access-state') {
    next()
    return
  }

  const userStore = useUserStore()
  if (!userStore.isAuthenticated) {
    const isLoggedIn = await userStore.checkAuth()
    if (!isLoggedIn) {
      next({ path: '/access', query: { reason: 'auth', redirect: to.fullPath } })
      return
    }
  }

  if (!userStore.isAdmin) {
    next({ path: '/access', query: { reason: 'forbidden' } })
    return
  }

  document.title = String(to.meta.title || 'PDF-Flow Admin')
  next()
})

export default router
