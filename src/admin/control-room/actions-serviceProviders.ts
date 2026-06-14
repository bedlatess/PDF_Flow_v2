import { adminAPI } from '@/admin/api'
import type { AdminServiceProviderConfig } from '@/admin/api'
import type { ControlRoomContext } from './context'

export const createControlRoomServiceProvidersActions = (ctx: ControlRoomContext) => {
  const loadServiceProviders = async () => {
    ctx.savingKey.value = 'service-providers:refresh'
    ctx.error.value = ''

    try {
      const [ocrProviderData, officeProviderData] = await Promise.all([
        adminAPI.listServiceProviderConfigs('ocr'),
        adminAPI.listServiceProviderConfigs('office'),
      ])
      ctx.serviceProviderConfigs.value = [...ocrProviderData, ...officeProviderData]
    } catch {
      ctx.error.value = 'Service provider config failed to load. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const saveServiceProvider = async (config: AdminServiceProviderConfig) => {
    ctx.savingKey.value = `service-provider:${config.service_key}:${config.provider_key}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateServiceProviderConfig(config.service_key, config.provider_key, {
        enabled: config.enabled,
        priority: Number(config.priority || 100),
        public_config: config.public_config,
        secrets: {},
      })
      const index = ctx.serviceProviderConfigs.value.findIndex(
        (item) =>
          item.service_key === updated.service_key &&
          item.provider_key === updated.provider_key,
      )
      if (index >= 0) ctx.serviceProviderConfigs.value[index] = updated
      ctx.auditLogs.value = await adminAPI.listAuditLogs()
      ctx.setMessage(`已保存服务提供方：${updated.display_name}`)
    } catch {
      ctx.error.value = 'Service provider config save failed. Please check the config and try again.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const validateServiceProvider = async (config: AdminServiceProviderConfig) => {
    ctx.savingKey.value = `service-provider:${config.service_key}:${config.provider_key}:validate`
    ctx.error.value = ''

    try {
      const result = await adminAPI.validateServiceProviderConfig(config.service_key, config.provider_key, {
        enabled: config.enabled,
        priority: Number(config.priority || 100),
        public_config: config.public_config,
        secrets: {},
      })
      ctx.setMessage(
        result.valid
          ? `${config.display_name} 本地校验通过`
          : `${config.display_name} 需要补齐配置：${result.errors.join(', ')}`,
      )
    } catch {
      ctx.error.value = 'Service provider validation failed. Please try again later.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    loadServiceProviders,
    saveServiceProvider,
    validateServiceProvider,
  }
}
