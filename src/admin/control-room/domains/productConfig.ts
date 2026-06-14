import type { ControlRoomDomainDeps } from './types'

export const createProductConfigDomain = ({ ctx, actions }: ControlRoomDomainDeps) => ({
  state: {
    settings: ctx.settings,
    flags: ctx.flags,
    contentBlocks: ctx.contentBlocks,
    serviceProviderConfigs: ctx.serviceProviderConfigs,
    selectedContent: ctx.selectedContent,
    enabledFlagCount: ctx.enabledFlagCount,
    lockedFlagCount: ctx.lockedFlagCount,
    savingKey: ctx.savingKey,
  },
  actions: {
    saveFlag: actions.saveFlag,
    saveSetting: actions.saveSetting,
    saveContentBlock: actions.saveContentBlock,
    loadServiceProviders: actions.loadServiceProviders,
    saveServiceProvider: actions.saveServiceProvider,
    validateServiceProvider: actions.validateServiceProvider,
  },
})
