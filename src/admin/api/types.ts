export interface AdminOverview {
  settings_count: number
  feature_flags_count: number
  content_blocks_count: number
  users_count: number
  active_users_count: number
  admin_users_count: number
  jobs_count: number
  failed_jobs_count: number
  feedback_count: number
  open_feedback_count: number
  api_error_count: number
  recent_audit_logs: AdminAuditLog[]
}

export interface AdminAuditLog {
  id: number
  admin_user_id: number
  action: string
  target_type: string
  target_key: string
  status: string
  detail: string | null
  created_at: string
}

export interface SiteSetting {
  id: number
  key: string
  value: string
  value_type: string
  group: string
  label: string
  description: string | null
  is_public: boolean
  updated_at: string
}

export interface FeatureFlag {
  id: number
  key: string
  label: string
  description: string | null
  enabled: boolean
  requires_login: boolean
  requires_pro: boolean
  maintenance_message: string | null
  updated_at: string
}

export interface ContentBlock {
  id: number
  key: string
  locale: string
  title: string
  content: string
  description: string | null
  is_public: boolean
  updated_at: string
}

export interface AdminUser {
  id: number
  email: string
  full_name: string | null
  role: 'free' | 'pro' | 'enterprise' | 'admin'
  is_active: boolean
  is_verified: boolean
  is_test_account: boolean
  subscription_id: string | null
  subscription_status: string | null
  subscription_end_date: string | null
  created_at: string
  last_login_at: string | null
}

export interface AdminUserUpdate {
  role?: AdminUser['role']
  is_active?: boolean
  is_verified?: boolean
  subscription_id?: string | null
  subscription_status?: string | null
  subscription_end_date?: string | null
}

export interface AdminPasswordResetLink {
  user_id: number
  email: string
  reset_url: string
  expires_at: string
}

export interface AdminJob {
  id: number | null
  job_id: string
  user_id: number | null
  user_email: string | null
  job_type: string
  status: string
  progress: number
  input_file_name: string
  input_file_size: number
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface AdminApiError {
  id: number
  user_id: number | null
  request_id: string | null
  method: string
  path: string
  query_string: string | null
  status_code: number
  error_type: string | null
  error_message: string | null
  traceback_summary: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface AdminServiceStatus {
  status: string
  detail: string | null
}

export interface AdminOperations {
  generated_at: string
  services: Record<string, AdminServiceStatus>
  total_users: number
  active_users: number
  banned_users: number
  test_users: number
  total_jobs: number
  visible_jobs: number
  failed_jobs: number
  running_jobs: number
  recent_users: AdminUser[]
  recent_failed_jobs: AdminJob[]
  recent_jobs: AdminJob[]
}

export interface AdminDiagnosticFeedbackSummary {
  id: number
  title: string
  status: string
  severity: string
  page_url: string | null
  diagnostic_code: string | null
  created_at: string
}

export interface AdminDiagnostics {
  generated_at: string
  recent_errors: AdminApiError[]
  recent_failed_jobs: AdminJob[]
  recent_feedback: AdminDiagnosticFeedbackSummary[]
  diagnostic_summary: string
  open_feedback_count: number
  failed_jobs_count: number
  api_error_count: number
}

export interface AdminHealthReport {
  generated_at: string
  app_version: string
  environment: string
  migration_version: string | null
  services: Record<string, AdminServiceStatus>
  users_count: number
  active_users_count: number
  open_feedback_count: number
  api_error_count: number
  failed_jobs_count: number
  running_jobs_count: number
  recent_error_path: string | null
  recent_feedback_title: string | null
}

export interface AdminPaymentOrder {
  id: number
  user_id: number
  user_email: string | null
  provider: string
  provider_display_name: string
  merchant_order_id: string
  provider_order_id: string | null
  plan: string
  amount_cents: number
  currency: string
  status: string
  checkout_url_present: boolean
  qr_code_url_present: boolean
  created_at: string
  updated_at: string
  expires_at: string | null
  paid_at: string | null
}

export interface AdminPaymentProviderHealth {
  key: string
  display_name: string
  enabled: boolean
  configured: boolean
  acceptance_status: string
  acceptance_label: string
  acceptance_detail: string
  acceptance_blockers: string[]
  latest_paid_event_at: string | null
  settlement: string
  supports_subscription: boolean
  supports_one_time: boolean
  open_orders: number
  paid_orders: number
  failed_orders: number
  latest_order_at: string | null
  detail: string
  webhook_url: string
  success_return_url: string
  cancel_return_url: string
  merchant_console_hint: string
  required_config_keys: string[]
  missing_config_keys: string[]
  setup_notes: string[]
  sandbox_runbook: string[]
  go_live_checklist: string[]
  expected_event_flow: string[]
  troubleshooting_steps: string[]
  evidence_fields: string[]
}

export interface AdminPaymentEvent {
  id: number
  order_id: number | null
  provider: string
  provider_event_id: string
  merchant_order_id: string
  provider_order_id: string | null
  event_type: string
  processing_status: string
  amount_cents: number | null
  currency: string | null
  raw_summary: string | null
  error_message: string | null
  created_at: string
}

export interface AdminPaymentSummary {
  generated_at: string
  total_orders: number
  pending_orders: number
  paid_orders: number
  failed_orders: number
  amount_mismatch_orders: number
  currency_mismatch_orders: number
  expired_pending_orders: number
  paid_amount_cents: number
  currency_breakdown: Record<string, number>
  providers: AdminPaymentProviderHealth[]
  recent_orders: AdminPaymentOrder[]
  recent_events: AdminPaymentEvent[]
  reconciliation_summary: string
  integration_evidence_packet: string
}

export interface AdminFeedback {
  id: number
  user_id: number | null
  email: string | null
  category: string
  severity: string
  status: 'new' | 'reviewing' | 'resolved' | 'closed'
  page_url: string | null
  title: string
  message: string
  diagnostic_code: string | null
  diagnostics: string | null
  admin_note: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
  updated_at: string
}

export interface AdminFeedbackUpdate {
  status?: AdminFeedback['status']
  admin_note?: string | null
}

export interface AdminFeedbackCleanup {
  closed_count: number
  remaining_open_count: number
}

export interface AdminMaintenance {
  test_users_count: number
  live_acceptance_feedback_count: number
  open_feedback_count: number
  api_error_count: number
  failed_jobs_count: number
  running_jobs_count: number
  file_retention: AdminFileRetention
}

export interface AdminFileRetention {
  scanned_count: number
  removable_count: number
  removed_count: number
  removed_bytes: number
  skipped_count: number
  upload_dir: string
}

export interface AdminCleanupTestUsers {
  deleted_count: number
  deleted_emails: string[]
  remaining_test_users_count: number
}
