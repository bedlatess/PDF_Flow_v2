import type { PublicFeatureFlag } from '@/services/api'

export type ReleaseTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

export const betaToolIds = new Set(['pdfToWord', 'pdfToExcel', 'batchConvert'])
export const scanFirstToolIds = new Set(['pdfToWord', 'pdfToExcel'])

export function featureAccessSummary(flag: PublicFeatureFlag | null | undefined) {
  if (!flag?.enabled) {
    return {
      label: 'Maintenance',
      detail: flag?.maintenance_message || 'This tool is temporarily unavailable.',
      tone: 'danger' as ReleaseTone,
    }
  }
  if (flag.requires_pro) {
    return {
      label: 'Pro',
      detail: 'Requires Pro access before creating new tasks.',
      tone: 'warning' as ReleaseTone,
    }
  }
  if (flag.requires_login) {
    return {
      label: 'Sign in',
      detail: 'Requires a signed-in account before creating new tasks.',
      tone: 'info' as ReleaseTone,
    }
  }
  return {
    label: 'Free',
    detail: 'Available on the free plan, subject to configured limits.',
    tone: 'success' as ReleaseTone,
  }
}

export function quotaSummary(flag: PublicFeatureFlag | null | undefined, isPro: boolean) {
  if (!flag) return 'Limits load from server configuration.'
  if (isPro && flag.pro_unlimited) return 'Unlimited Pro usage for this tool.'

  const daily = isPro ? flag.pro_daily_limit : flag.free_daily_limit
  const size = isPro ? flag.pro_max_file_size_mb : flag.free_max_file_size_mb
  const batch = isPro ? flag.pro_batch_file_limit : flag.free_batch_file_limit
  const parts = [
    daily ? `${daily}/day` : 'daily limit not set',
    size ? `${size} MB/file` : 'file size not set',
    batch ? `${batch}/batch` : 'batch limit not set',
  ]

  return parts.join(' · ')
}

export function shortFailureMessage(message?: string | null) {
  if (!message) return 'The task failed before a result was produced.'
  const clean = message
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  if (!clean) return 'The task failed before a result was produced.'

  const lower = clean.toLowerCase()
  if (
    lower.includes('traceback') ||
    lower.includes('sqlalchemy') ||
    lower.includes('celery') ||
    lower.includes('/tmp/') ||
    lower.includes('c:\\') ||
    lower.includes('\\app\\')
  ) {
    return 'The task failed because the server could not finish processing. Try again or share the job ID with support.'
  }

  if (lower.includes('scanned') || lower.includes('image-based') || lower.includes('image only')) {
    return 'This looks like a scanned PDF. Run OCR PDF first, then retry this tool.'
  }
  if (lower.includes('password') || lower.includes('encrypted')) {
    return 'This PDF appears to be password-protected. Unlock it first, then retry.'
  }
  if (lower.includes('too large') || lower.includes('exceed')) {
    return 'This file exceeds the current limit. Try a smaller file or split it first.'
  }
  if (lower.includes('unsupported') || lower.includes('file type')) {
    return 'This file type is not supported by the selected tool.'
  }

  return clean.length > 180 ? `${clean.slice(0, 177)}...` : clean
}

export function toneClass(tone: ReleaseTone) {
  if (tone === 'success') return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
  if (tone === 'warning') return 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100'
  if (tone === 'danger') return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200'
  if (tone === 'info') return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200'
  return 'border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200'
}
