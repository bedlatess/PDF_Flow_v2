/**
 * User Store - 用户状态管理
 * 处理用户认证、个人信息和使用统计
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI, userAPI, type User, type UserStats, type LoginData, type RegisterData } from '@/services/api'
import { toUserStoreErrorMessage } from '@/utils/error-messages'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const stats = ref<UserStats | null>(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const isFreeTier = computed(() => user.value?.role === 'free')
  const isProTier = computed(() => user.value?.role === 'pro')
  const isEnterpriseTier = computed(
    () => user.value?.role === 'enterprise' || user.value?.role === 'admin'
  )

  const canUseCloudFeatures = computed(() => {
    return isProTier.value || isEnterpriseTier.value
  })

  const quotaUsagePercentage = computed(() => {
    if (!stats.value) return 0
    if (stats.value.quota_limit === -1) return 0 // Unlimited
    const used = stats.value.requests_today
    return Math.min(100, (used / stats.value.quota_limit) * 100)
  })

  // Actions
  /**
   * 用户注册
   */
  const register = async (data: RegisterData) => {
    loading.value = true
    error.value = null

    try {
      const newUser = await authAPI.register(data)
      console.log('User registered:', newUser)
      return newUser
    } catch (err: any) {
      error.value = toUserStoreErrorMessage(err, {
        area: 'AUTH',
        fallbackTitle: 'Registration failed',
        fallbackMessage: 'Please try again.',
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登录
   */
  const login = async (data: LoginData) => {
    loading.value = true
    error.value = null

    try {
      // 1. 登录获取 token
      const authResponse = await authAPI.login(data)

      // 2. 保存 token
      localStorage.setItem('access_token', authResponse.access_token)
      localStorage.setItem('refresh_token', authResponse.refresh_token)

      // 3. 获取用户信息
      const currentUser = await authAPI.getCurrentUser()
      user.value = currentUser
      isAuthenticated.value = true

      // 4. 获取使用统计
      await fetchStats()

      console.log('User logged in:', currentUser)
      return currentUser
    } catch (err: any) {
      error.value = toUserStoreErrorMessage(err, {
        area: 'AUTH',
        fallbackTitle: 'Sign-in failed',
        fallbackMessage: 'Please check your details and try again.',
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登出
   */
  const logout = async () => {
    loading.value = true

    try {
      await authAPI.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      // 清除本地状态
      user.value = null
      stats.value = null
      isAuthenticated.value = false
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      loading.value = false
    }
  }

  /**
   * 检查登录状态（从 localStorage 恢复）
   */
  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      isAuthenticated.value = false
      return false
    }

    loading.value = true

    try {
      const currentUser = await authAPI.getCurrentUser()
      user.value = currentUser
      isAuthenticated.value = true
      await fetchStats()
      return true
    } catch (err) {
      console.error('Auth check failed:', err)
      isAuthenticated.value = false
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取使用统计
   */
  const fetchStats = async () => {
    if (!isAuthenticated.value) return

    try {
      const userStats = await userAPI.getStats()
      stats.value = userStats
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  /**
   * 更新用户信息
   */
  const updateProfile = async (data: { full_name?: string; email?: string }) => {
    loading.value = true
    error.value = null

    try {
      const updatedUser = await userAPI.updateProfile(data)
      user.value = updatedUser
      return updatedUser
    } catch (err: any) {
      error.value = toUserStoreErrorMessage(err, {
        area: 'AUTH',
        fallbackTitle: 'Profile update failed',
        fallbackMessage: 'Please review your changes and try again.',
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除账户
   */
  const deleteAccount = async () => {
    loading.value = true
    error.value = null

    try {
      await userAPI.deleteAccount()
      await logout()
    } catch (err: any) {
      error.value = toUserStoreErrorMessage(err, {
        area: 'AUTH',
        fallbackTitle: 'Account deletion failed',
        fallbackMessage: 'Please try again or contact the administrator if the issue continues.',
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    user,
    stats,
    isAuthenticated,
    loading,
    error,

    // Computed
    isFreeTier,
    isProTier,
    isEnterpriseTier,
    canUseCloudFeatures,
    quotaUsagePercentage,

    // Actions
    register,
    login,
    logout,
    checkAuth,
    fetchStats,
    updateProfile,
    deleteAccount
  }
})
