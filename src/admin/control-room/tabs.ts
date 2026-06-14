import {
  Activity,
  ClipboardList,
  CreditCard,
  FileCog,
  FileText,
  Flag,
  Flame,
  GaugeCircle,
  KeyRound,
  Settings2,
  Trash2,
  UserCog,
} from 'lucide-vue-next'
import type { ControlRoomTabGroup, ControlRoomTabId } from './types'

export const controlRoomTabs: Array<{
  id: ControlRoomTabId
  label: string
  description: string
  group: ControlRoomTabGroup
  icon: typeof GaugeCircle
}> = [
  {
    id: 'overview',
    label: '运营总览',
    description: '核心健康度、用户、任务和待处理风险。',
    group: '概览',
    icon: GaugeCircle,
  },
  {
    id: 'users',
    label: '用户与权限',
    description: '账号状态、手动权益、重置链接和封禁。',
    group: '客户与收入',
    icon: UserCog,
  },
  {
    id: 'paymentSetup',
    label: '支付配置',
    description: '商户密钥就绪度、回调地址和上线清单。',
    group: '客户与收入',
    icon: FileCog,
  },
  {
    id: 'payments',
    label: '支付对账',
    description: '订单、回调事件、金额异常和证据包。',
    group: '客户与收入',
    icon: CreditCard,
  },
  {
    id: 'flags',
    label: '功能开关',
    description: '控制工具、登录要求、Pro 要求和维护提示。',
    group: '产品配置',
    icon: Flag,
  },
  {
    id: 'settings',
    label: '站点配置',
    description: '公开配置、站点文案和运营参数。',
    group: '产品配置',
    icon: Settings2,
  },
  {
    id: 'content',
    label: '内容块',
    description: '首页、工具页和公共页面的可编辑内容。',
    group: '产品配置',
    icon: FileText,
  },
  {
    id: 'jobs',
    label: '任务观察',
    description: 'PDF、OCR、Office 和 AI 后台任务状态。',
    group: '运营支持',
    icon: GaugeCircle,
  },
  {
    id: 'feedback',
    label: '问题反馈',
    description: '用户反馈、诊断码和处理备注。',
    group: '运营支持',
    icon: ClipboardList,
  },
  {
    id: 'errors',
    label: '错误观察',
    description: 'API 错误、失败任务和诊断摘要。',
    group: '运营支持',
    icon: Flame,
  },
  {
    id: 'maintenance',
    label: '维护清理',
    description: '验收反馈、测试账号和过期文件清理。',
    group: '运营支持',
    icon: Trash2,
  },
  {
    id: 'security',
    label: 'Account Security',
    description: 'Admin password rotation and session handoff.',
    group: '安全',
    icon: KeyRound,
  },
  {
    id: 'audit',
    label: '审计日志',
    description: '管理员操作记录和关键变更留痕。',
    group: '安全',
    icon: Activity,
  },
]
