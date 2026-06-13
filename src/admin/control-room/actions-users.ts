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

  const deleteUser = async (user: AdminUser) => {
    ctx.openAdminConfirmation({
      title: '确认删除用户',
      summary: `将删除 ${user.email} 及其关联数据。`,
      details: [
        '此操作不能直接撤销。',
        '当前管理员账号不能删除自己，后端仍会再次校验权限。',
        '执行结果会写入审计日志。',
      ],
      confirmLabel: '确认删除用户',
      savingKey: `delete:${user.id}`,
      tone: 'danger',
      run: async () => {
        ctx.savingKey.value = `delete:${user.id}`
        ctx.error.value = ''

        try {
          await adminAPI.deleteUser(user.id)
          ctx.users.value = ctx.users.value.filter((item) => item.id !== user.id)
          await refreshAdminMeta()
          ctx.setMessage(`已删除用户：${user.email}`)
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
    deleteUser,
  }
}
