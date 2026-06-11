export type HistoryToolType =
  | 'merge'
  | 'split'
  | 'rotate'
  | 'compress'
  | 'imageToPdf'
  | 'pdfToImage'
  | 'deletePages'
  | 'organize'
  | 'pageNumbers'
  | 'protect'
  | 'watermark'

export interface HistoryItem {
  id: string
  type: HistoryToolType
  fileName: string
  timestamp: number
  fileSize?: number
  resultSize?: number
}

export interface HistoryStats {
  totalFiles: number
  todayFiles: number
  mostUsedTool: HistoryToolType | null
  totalSaved?: number
}

const STORAGE_KEY = 'pdf-flow-history'
const MAX_HISTORY_ITEMS = 20

class HistoryManager {
  addHistory(item: Omit<HistoryItem, 'id' | 'timestamp'>): void {
    const history = this.getHistory()

    const newItem: HistoryItem = {
      ...item,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      timestamp: Date.now(),
    }

    history.unshift(newItem)

    if (history.length > MAX_HISTORY_ITEMS) {
      history.splice(MAX_HISTORY_ITEMS)
    }

    this.saveHistory(history)
  }

  getHistory(): HistoryItem[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      if (!data) return []
      return JSON.parse(data) as HistoryItem[]
    } catch (error) {
      console.error('Failed to load history:', error)
      return []
    }
  }

  removeHistory(id: string): void {
    const history = this.getHistory()
    this.saveHistory(history.filter((item) => item.id !== id))
  }

  clearHistory(): void {
    localStorage.removeItem(STORAGE_KEY)
  }

  getHistoryByType(type: HistoryToolType): HistoryItem[] {
    return this.getHistory().filter((item) => item.type === type)
  }

  getTodayHistory(history = this.getHistory()): HistoryItem[] {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return history.filter((item) => item.timestamp >= today.getTime())
  }

  getStats(history = this.getHistory()): HistoryStats {
    const todayHistory = this.getTodayHistory(history)

    const toolCount: Partial<Record<HistoryToolType, number>> = {}
    history.forEach((item) => {
      toolCount[item.type] = (toolCount[item.type] || 0) + 1
    })

    const mostUsedTool = Object.entries(toolCount).sort((a, b) => b[1] - a[1])[0]?.[0] as
      | HistoryToolType
      | undefined

    const totalSaved = history
      .filter((item) => item.type === 'compress' && item.fileSize && item.resultSize)
      .reduce((sum, item) => sum + Math.max(item.fileSize! - item.resultSize!, 0), 0)

    return {
      totalFiles: history.length,
      todayFiles: todayHistory.length,
      mostUsedTool: mostUsedTool || null,
      totalSaved: totalSaved > 0 ? totalSaved : undefined,
    }
  }

  private saveHistory(history: HistoryItem[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history))
    } catch (error) {
      console.error('Failed to save history:', error)
    }
  }
}

export const historyManager = new HistoryManager()

export function formatToolType(type: HistoryToolType): string {
  const typeNames: Record<HistoryToolType, string> = {
    merge: '合并 PDF',
    split: '拆分 PDF',
    rotate: '旋转 PDF',
    compress: '压缩 PDF',
    imageToPdf: '图片转 PDF',
    pdfToImage: 'PDF 转图片',
    deletePages: '删除 PDF 页面',
    organize: '整理 PDF 页面',
    pageNumbers: '添加 PDF 页码',
    protect: '保护 PDF',
    watermark: '添加水印',
  }
  return typeNames[type]
}

export function formatHistoryTime(timestamp: number): string {
  const diff = Date.now() - timestamp

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`

  return new Date(timestamp).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  })
}
