import { createOperationsDomain } from './domains/operations'
import { createOverviewDomain } from './domains/overview'
import { createProductConfigDomain } from './domains/productConfig'
import { createRevenueDomain } from './domains/revenue'
import { createSecurityDomain } from './domains/security'
import { createUsersDomain } from './domains/users'
import type { ControlRoomActions, ControlRoomClipboard } from './domains/types'
import type { ControlRoomContext } from './context'

export const createControlRoomDomains = (
  ctx: ControlRoomContext,
  actions: ControlRoomActions,
  clipboard: ControlRoomClipboard,
) => {
  const deps = { ctx, actions, clipboard }

  return {
    overview: createOverviewDomain(deps),
    users: createUsersDomain(deps),
    revenue: createRevenueDomain(deps),
    productConfig: createProductConfigDomain(deps),
    operations: createOperationsDomain(deps),
    security: createSecurityDomain(deps),
  }
}

export type ControlRoomDomains = ReturnType<typeof createControlRoomDomains>
