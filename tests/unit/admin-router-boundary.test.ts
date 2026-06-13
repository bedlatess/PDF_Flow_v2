import { describe, expect, it } from 'vitest'
import adminRouter from '@/admin/router'

describe('admin router boundary', () => {
  it('keeps the admin app rooted at its own control room route', () => {
    const routeNames = adminRouter.getRoutes().map((route) => route.name)

    expect(routeNames).toContain('admin-control-room')
    expect(routeNames).toContain('admin-access-state')
    expect(adminRouter.resolve('/').name).toBe('admin-control-room')
  })

  it('does not depend on the public locale route tree', () => {
    const routes = adminRouter.getRoutes()

    expect(routes.some((route) => route.path.includes(':locale'))).toBe(false)
    expect(routes.some((route) => route.path === '/control-room')).toBe(false)
  })
})
