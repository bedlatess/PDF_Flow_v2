import { formatAdminDate } from '../formatters'
import type { ControlRoomDomainDeps } from './types'

export const createUsersDomain = ({ ctx, actions }: ControlRoomDomainDeps) => ({
  state: {
    users: ctx.users,
    userSearch: ctx.userSearch,
    userPasswordResetLinks: ctx.userPasswordResetLinks,
    savingKey: ctx.savingKey,
  },
  actions: {
    searchUsers: actions.searchUsers,
    saveUser: actions.saveUser,
    toggleUserBan: actions.toggleUserBan,
    createPasswordResetLink: actions.createPasswordResetLink,
    deleteUser: actions.deleteUser,
  },
  helpers: {
    formatDate: formatAdminDate,
  },
})
