import {
  adminAPI,
  type ContentBlock,
  type FeatureFlag,
  type SiteSetting,
} from '@/admin/api'
import type { ControlRoomContext } from './context'

export const createControlRoomSettingsActions = (ctx: ControlRoomContext) => {
  const saveFlag = async (flag: FeatureFlag) => {
    ctx.savingKey.value = `flag:${flag.key}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateFeatureFlag(flag.key, {
        label: flag.label,
        description: flag.description,
        enabled: flag.enabled,
        is_public: flag.is_public,
        requires_login: flag.requires_login,
        requires_pro: flag.requires_pro,
        maintenance_message: flag.maintenance_message,
      })
      const index = ctx.flags.value.findIndex((item) => item.key === updated.key)
      if (index >= 0) ctx.flags.value[index] = updated
      ctx.auditLogs.value = await adminAPI.listAuditLogs()
      await ctx.siteConfigStore.fetchPublicConfig(true)
      ctx.setMessage(`Saved tool config: ${updated.label}`)
    } catch {
      ctx.error.value = 'Tool config save failed. Check the input and retry.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const saveSetting = async (setting: SiteSetting) => {
    ctx.savingKey.value = `setting:${setting.key}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateSetting(setting.key, {
        value: setting.value,
        value_type: setting.value_type,
        group: setting.group,
        label: setting.label,
        description: setting.description,
        is_public: setting.is_public,
      })
      const index = ctx.settings.value.findIndex((item) => item.key === updated.key)
      if (index >= 0) ctx.settings.value[index] = updated
      ctx.auditLogs.value = await adminAPI.listAuditLogs()
      await ctx.siteConfigStore.fetchPublicConfig(true)
      ctx.setMessage(`Saved setting: ${updated.label}`)
    } catch {
      ctx.error.value = 'Site setting save failed. Please check the input and retry.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  const saveContentBlock = async (block: ContentBlock) => {
    ctx.savingKey.value = `content:${block.key}:${block.locale}`
    ctx.error.value = ''

    try {
      const updated = await adminAPI.updateContentBlock(block.key, block.locale, {
        locale: block.locale,
        title: block.title,
        content: block.content,
        description: block.description,
        is_public: block.is_public,
      })
      const index = ctx.contentBlocks.value.findIndex(
        (item) => item.key === updated.key && item.locale === updated.locale,
      )
      if (index >= 0) ctx.contentBlocks.value[index] = updated
      ctx.selectedContent.value = updated
      ctx.auditLogs.value = await adminAPI.listAuditLogs()
      await ctx.siteConfigStore.fetchPublicConfig(true)
      ctx.setMessage(`Saved content block: ${updated.title}`)
    } catch {
      ctx.error.value = 'Content block save failed. Please check the input and retry.'
    } finally {
      ctx.savingKey.value = null
    }
  }

  return {
    saveFlag,
    saveSetting,
    saveContentBlock,
  }
}
