import { describe, expect, it } from 'vitest'
import type { AdminFeedback, AdminHealthReport } from '@/admin/api'
import {
  formatAdminBytes,
  formatAdminMoney,
  parseAdminDiagnostics,
  serviceStatusText,
} from '@/admin/control-room/formatters'
import { buildFeedbackSummary, buildHealthReportSummary } from '@/admin/control-room/summaries'
import { controlRoomTabs } from '@/admin/control-room/tabs'

describe('admin control room utilities', () => {
  it('formats bytes, money, and diagnostics for operator-facing views', () => {
    expect(formatAdminBytes(0)).toBe('0 B')
    expect(formatAdminBytes(4096)).toBe('4.0 KB')
    expect(formatAdminMoney(990, 'USD')).toContain('9.90')
    expect(parseAdminDiagnostics('{"route":"/tools/compress"}')).toContain('"route"')
    expect(parseAdminDiagnostics('plain text')).toBe('plain text')
  })

  it('keeps the admin tab registry stable', () => {
    expect(controlRoomTabs.map((tab) => tab.id)).toEqual([
      'overview',
      'users',
      'paymentSetup',
      'payments',
      'flags',
      'settings',
      'content',
      'jobs',
      'feedback',
      'errors',
      'maintenance',
      'audit',
    ])
    expect(controlRoomTabs.map((tab) => tab.group)).toEqual([
      '概览',
      '客户与收入',
      '客户与收入',
      '客户与收入',
      '产品配置',
      '产品配置',
      '产品配置',
      '运营支持',
      '运营支持',
      '运营支持',
      '运营支持',
      '安全',
    ])
  })

  it('builds feedback summaries without exposing raw document content', () => {
    const feedback = {
      id: 501,
      user_id: 2,
      email: 'tester@example.com',
      category: 'bug',
      severity: 'high',
      status: 'new',
      page_url: '/tools/compress',
      title: 'Download did not start',
      message: 'The generated file button did not respond.',
      diagnostic_code: 'PDF-FLOW-501',
      diagnostics: JSON.stringify({ viewport: '390x844', route: '/tools/compress' }),
      admin_note: 'Check mobile click target.',
      ip_address: '127.0.0.1',
      user_agent: 'Playwright Chromium',
      created_at: '2026-06-11T09:05:00.000Z',
      updated_at: '2026-06-11T09:05:00.000Z',
    } satisfies AdminFeedback

    const summary = buildFeedbackSummary(feedback)

    expect(summary).toContain('PDF-Flow 反馈 #501')
    expect(summary).toContain('PDF-FLOW-501')
    expect(summary).toContain('"viewport"')
    expect(summary).toContain('Check mobile click target.')
  })

  it('builds health report summaries from the latest backend report', () => {
    const report = {
      generated_at: '2026-06-11T09:30:00.000Z',
      app_version: 'api-test',
      environment: 'playwright',
      migration_version: '20260611_admin_tabs',
      services: {
        database: { status: 'healthy', detail: 'ok' },
        redis: { status: 'degraded', detail: 'slow' },
      },
      users_count: 10,
      active_users_count: 8,
      open_feedback_count: 2,
      api_error_count: 1,
      failed_jobs_count: 3,
      running_jobs_count: 4,
      recent_error_path: '/api/v1/files/compress',
      recent_feedback_title: 'Compress issue',
    } satisfies AdminHealthReport

    expect(serviceStatusText(report)).toBe('database=healthy, redis=degraded')
    expect(
      buildHealthReportSummary(report, {
        appVersion: 'frontend-test',
        pageUrl: 'https://admin.pdf-flow.test',
      }),
    ).toContain('前端版本：frontend-test')
  })
})
