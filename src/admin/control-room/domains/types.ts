import type { createControlRoomActions } from '../actions'
import type { createControlRoomClipboard } from '../clipboard'
import type { ControlRoomContext } from '../context'

export type ControlRoomActions = ReturnType<typeof createControlRoomActions>
export type ControlRoomClipboard = ReturnType<typeof createControlRoomClipboard>

export type ControlRoomDomainDeps = {
  ctx: ControlRoomContext
  actions: ControlRoomActions
  clipboard: ControlRoomClipboard
}
