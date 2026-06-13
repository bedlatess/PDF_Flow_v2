import {
  Activity,
  ClipboardList,
  CreditCard,
  FileText,
  Flag,
  Flame,
  GaugeCircle,
  Settings2,
  Trash2,
  UserCog,
} from 'lucide-vue-next'
import type { ControlRoomTabId } from './types'

export const controlRoomTabs: Array<{
  id: ControlRoomTabId
  label: string
  icon: typeof GaugeCircle
}> = [
  { id: 'overview', label: '运营总览', icon: GaugeCircle },
  { id: 'flags', label: '功能开关', icon: Flag },
  { id: 'settings', label: '站点配置', icon: Settings2 },
  { id: 'content', label: '内容块', icon: FileText },
  { id: 'users', label: '用户管理', icon: UserCog },
  { id: 'jobs', label: '任务观察', icon: GaugeCircle },
  { id: 'payments', label: '支付对账', icon: CreditCard },
  { id: 'feedback', label: '问题反馈', icon: ClipboardList },
  { id: 'errors', label: '错误观察', icon: Flame },
  { id: 'maintenance', label: '维护清理', icon: Trash2 },
  { id: 'audit', label: '审计日志', icon: Activity },
]
