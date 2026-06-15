import { adminAPI, type AdminUser } from '@/admin/api'
import type { ControlRoomContext } from './context'

type UsersActionDeps = {
  refreshAdminMeta: () => Promise<void>
}

export const createControlRoomUsersActions = (
  ctx: ControlRoomContext,
  { refreshAdminMeta }: UsersActionDeps,
) => {
  const searchUsers = async () => {
    ctx.savingKey.value = 'users:search'
    ctx.error.value = ''

    try {
      ctx.users.value = await adminAPI.listUsers({
        search: ctx.userSearch.value.trim() || undefined,
      })
    } catch {
      ctx.error.value = 'User list failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const saveUser = async (user: AdminUser) => {
    ctx.savingKey.value = `user:${user.id}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateUser(user.id, {
        role: user.role,
        is_active: user.is_active,
        is_verified: user.is_verified,
        subscription_id: user.subscription_id || null,
        subscription_status: user.subscription_status || null,
        subscription_end_date: user.subscription_end_date || null,
      })
      const index = ctx.users.value.findIndex((item) => item.id === updated.id)
      if (index >= 0) ctx.users.value[index] = updated
      await refreshAdminMeta()
      ctx.setMessage(`Updated user: ${updated.email}`)
    } catch (err: any) {
      ctx.error.value =
        err?.response?.data?.detail || 'User update failed. Please check permissions and retry.'
      ctx.users.value = await adminAPI.listUsers({
        search: ctx.userSearch.value.trim() || undefined,
      })
    } finally {
      ctx.savingKey.value = null
    }
  }

  const toggleUserBan = async (user: AdminUser) => {
    const nextActive = !user.is_active
    ctx.savingKey.value = `ban:${user.id}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateUser(user.id, {
        is_active: nextActive,
      })
      const index = ctx.users.value.findIndex((item) => item.id === updated.id)
      if (index >= 0) ctx.users.value[index] = updated
      await refreshAdminMeta()
      ctx.setMessage(`${nextActive ? 'Unblocked' : 'Blocked'} user: ${updated.email}`)
    } catch (err: any) {
      ctx.error.value =
        err?.response?.data?.detail || 'User status update failed. Please try again later.'
      await searchUsers()
    } finally {
      ctx.savingKey.value = null
    }
  }

  const createPasswordResetLink = async (user: AdminUser) => {
    ctx.savingKey.value = `reset-link:${user.id}`
    ctx.error.value = ''

    try {
      const result = await adminAPI.createUserPasswordResetLink(user.id)
      ctx.userPasswordResetLinks.value[user.id] = result

      try {
        await navigator.clipboard?.writeText(result.reset_url)
        ctx.setMessage(`Reset link copied for ${result.email}`)
      } catch {
        ctx.setMessage(`Reset link generated for ${result.email}`)
      }
    } catch (err: any) {
      ctx.error.value =
        err?.response?.data?.detail ||
        'Password reset link could not be generated. Please check the user status.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const deleteUser = async (user: AdminUser) => {
    ctx.openAdminConfirmation({
      title: 'Confirm user deletion',
      summary: `This will delete ${user.email} and related account data.`,
      details: [
        'This action cannot be directly undone.',
        'The current admin account cannot delete itself; backend permissions are checked again.',
        'The result is recorded in the audit log.',
      ],
      confirmLabel: 'Delete user',
      savingKey: `delete:${user.id}`,
      tone: 'danger',
      run: async () => {
        ctx.savingKey.value = `delete:${user.id}`
        ctx.error.value = ''

        try {
          await adminAPI.deleteUser(user.id)
          ctx.users.value = ctx.users.value.filter((item) => item.id !== user.id)
          await refreshAdminMeta()
          ctx.setMessage(`Deleted user: ${user.email}`)
        } catch (err: any) {
          ctx.error.value =
            err?.response?.data?.detail ||
            'User deletion failed. Confirm this is not the current admin account.'
          throw err
        } finally {
          ctx.savingKey.value = null
        }
      },
    })
  }

  return {
    searchUsers,
    saveUser,
    toggleUserBan,
    createPasswordResetLink,
    deleteUser,
  }
}
