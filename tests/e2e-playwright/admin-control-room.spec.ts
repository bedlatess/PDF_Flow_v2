import { expect, type Page, test } from '@playwright/test'

const now = '2026-06-11T09:30:00.000Z'

const adminUser = {
  id: 1,
  email: 'admin@pdf-flow.test',
  full_name: 'PDF-Flow Admin',
  role: 'admin',
  is_active: true,
  is_verified: true,
  created_at: '2026-01-01T08:00:00.000Z',
}

const users = [
  {
    id: 1,
    email: 'admin@pdf-flow.test',
    full_name: 'PDF-Flow Admin',
    role: 'admin',
    is_active: true,
    is_verified: true,
    is_test_account: false,
    created_at: '2026-01-01T08:00:00.000Z',
    last_login_at: now,
  },
  {
    id: 2,
    email: 'smoke-compress@example.com',
    full_name: 'Smoke Compress',
    role: 'free',
    is_active: true,
    is_verified: false,
    is_test_account: true,
    created_at: '2026-05-28T08:00:00.000Z',
    last_login_at: null,
  },
]

const jobs = [
  {
    id: 101,
    job_id: 'job_20260611_compress_failed_001',
    user_id: 2,
    user_email: 'smoke-compress@example.com',
    job_type: 'compress_pdf',
    status: 'failed',
    progress: 72,
    input_file_name: 'quarterly-board-pack-with-long-readable-name.pdf',
    input_file_size: 8847360,
    output_file_url: null,
    error_message: 'Worker timed out while optimizing embedded images.',
    created_at: '2026-06-11T09:12:00.000Z',
    started_at: '2026-06-11T09:12:03.000Z',
    completed_at: '2026-06-11T09:13:18.000Z',
    source: 'db',
    sources: ['db', 'redis'],
    is_durable: true,
  },
  {
    id: 102,
    job_id: 'job_20260611_ocr_running_002',
    user_id: 1,
    user_email: 'admin@pdf-flow.test',
    job_type: 'ocr_pdf',
    status: 'processing',
    progress: 46,
    input_file_name: 'scanned-contract.pdf',
    input_file_size: 2097152,
    output_file_url: '/api/v1/files/jobs/job_20260611_ocr_running_002/download',
    error_message: null,
    created_at: '2026-06-11T09:20:00.000Z',
    started_at: '2026-06-11T09:20:05.000Z',
    completed_at: null,
    source: 'redis',
    sources: ['redis'],
    is_durable: false,
  },
]

const auditLogs = [
  {
    id: 9001,
    admin_user_id: 1,
    action: 'feature_flag.update',
    target_type: 'feature_flag',
    target_key: 'ocr_pdf',
    status: 'success',
    detail: 'Enabled OCR queue after smoke verification.',
    created_at: '2026-06-11T09:22:00.000Z',
  },
  {
    id: 9002,
    admin_user_id: 1,
    action: 'maintenance.refresh',
    target_type: 'maintenance',
    target_key: 'file_retention',
    status: 'success',
    detail: null,
    created_at: '2026-06-11T09:18:00.000Z',
  },
]

const feedback = [
  {
    id: 501,
    user_id: 2,
    email: 'tester@example.com',
    category: 'bug',
    severity: 'high',
    status: 'new',
    page_url: '/tools/compress',
    title: '压缩完成后下载按钮没有响应',
    message:
      '在 Chrome 移动端上传一个 18MB 文件后，进度显示完成，但下载按钮点击后没有任何反馈。',
    diagnostic_code: 'PDF-FLOW-501',
    diagnostics: JSON.stringify({ viewport: '390x844', route: '/tools/compress' }),
    admin_note: '',
    ip_address: '127.0.0.1',
    user_agent: 'Playwright Chromium',
    created_at: '2026-06-11T09:05:00.000Z',
    updated_at: '2026-06-11T09:05:00.000Z',
  },
]

const apiErrors = [
  {
    id: 301,
    user_id: 2,
    request_id: 'req_visual_qa_001',
    method: 'POST',
    path: '/api/v1/files/compress',
    query_string: null,
    status_code: 500,
    error_type: 'WorkerTimeout',
    error_message: 'Compression worker timed out.',
    traceback_summary: 'TimeoutError: image optimization exceeded 30s',
    ip_address: '127.0.0.1',
    user_agent: 'Playwright Chromium',
    created_at: '2026-06-11T09:13:18.000Z',
  },
]

const overview = {
  settings_count: 3,
  feature_flags_count: 4,
  content_blocks_count: 3,
  users_count: users.length,
  active_users_count: 2,
  admin_users_count: 1,
  jobs_count: jobs.length,
  failed_jobs_count: 1,
  feedback_count: feedback.length,
  open_feedback_count: 1,
  api_error_count: apiErrors.length,
  recent_audit_logs: auditLogs,
}

const operations = {
  generated_at: now,
  services: {
    database: { status: 'healthy', detail: 'PostgreSQL connection pool is healthy.' },
    redis: { status: 'degraded', detail: 'Queue latency is above the normal threshold.' },
    worker: { status: 'healthy', detail: 'Two Celery workers are available.' },
  },
  total_users: users.length,
  active_users: 2,
  banned_users: 0,
  test_users: 1,
  total_jobs: jobs.length,
  visible_jobs: jobs.length,
  failed_jobs: 1,
  running_jobs: 1,
  recent_users: users,
  recent_failed_jobs: jobs.filter((job) => job.status === 'failed'),
  recent_jobs: jobs,
}

const healthReport = {
  generated_at: now,
  app_version: 'api-visual-qa',
  environment: 'playwright',
  migration_version: '20260611_admin_tabs',
  services: operations.services,
  users_count: users.length,
  active_users_count: 2,
  open_feedback_count: 1,
  api_error_count: apiErrors.length,
  failed_jobs_count: 1,
  running_jobs_count: 1,
  recent_error_path: '/api/v1/files/compress',
  recent_feedback_title: feedback[0].title,
}

const pricingPlans = [
  {
    id: 601,
    plan_key: 'free',
    display_name: 'Free',
    is_public: true,
    price_amount_cents: 0,
    display_price: '$0',
    currency: 'USD',
    billing_interval: 'none',
    description: 'Basic local PDF tools.',
    provider_mappings: {
      stripe: { price_id: '' },
      paypal: { plan_id: '', product_id: '' },
      gmpay: { amount_cents: 0, currency: 'CNY', token: 'usdt', network: 'tron' },
    },
    sort_order: 0,
    highlighted: false,
    updated_at: now,
  },
  {
    id: 602,
    plan_key: 'pro_monthly',
    display_name: 'Pro Monthly',
    is_public: true,
    price_amount_cents: 990,
    display_price: '$9.90',
    currency: 'USD',
    billing_interval: 'month',
    description: 'Monthly Pro plan.',
    provider_mappings: {
      stripe: { price_id: 'price_admin_monthly' },
      paypal: { plan_id: 'P-ADMIN-MONTHLY', product_id: 'PROD-ADMIN' },
      gmpay: { amount_cents: 990, currency: 'CNY', token: 'usdt', network: 'tron' },
    },
    sort_order: 10,
    highlighted: true,
    updated_at: now,
  },
]

const paymentConfigField = (
  key: string,
  label: string,
  input_type: 'text' | 'url' | 'number' | 'password' = 'text',
  required = true,
  secret = false,
) => ({
  key,
  label,
  input_type,
  required,
  secret,
  placeholder: '',
  help_text: '',
  min_value: input_type === 'number' ? 0 : null,
  max_value: null,
})

const paymentConfigs = [
  {
    provider_key: 'stripe',
    display_name: 'Stripe',
    enabled: true,
    configured: true,
    public_config: {
      price_id_monthly: 'price_admin_monthly',
      price_id_yearly: 'price_admin_yearly',
    },
    secret_fields: {
      secret_key: { configured: true, tail: '1234' },
      webhook_secret: { configured: true, tail: 'abcd' },
    },
    required_public_fields: ['price_id_monthly', 'price_id_yearly'],
    required_secret_fields: ['secret_key', 'webhook_secret'],
    missing_config_keys: [],
    webhook_url: 'https://api.pdf-flow.test/api/v1/payment/webhooks/stripe',
    updated_at: now,
    encryption_available: true,
    webhook_status: 'manual',
    metadata: {
      provider_key: 'stripe',
      display_name: 'Stripe',
      description: 'Stripe hosted checkout.',
      settlement: 'subscription',
      supports_subscription: true,
      supports_one_time: true,
      merchant_console_hint: 'Stripe Dashboard > Developers > Webhooks',
      setup_notes: ['Configure webhook URL before live use.'],
      validation_checks: ['required_fields'],
      fields: {
        public: [
          paymentConfigField('price_id_monthly', 'Monthly Price ID'),
          paymentConfigField('price_id_yearly', 'Yearly Price ID'),
        ],
        secret: [
          paymentConfigField('secret_key', 'Secret Key', 'password', true, true),
          paymentConfigField('webhook_secret', 'Webhook Secret', 'password', true, true),
        ],
      },
    },
    readiness: {
      status: 'ready',
      label: 'Ready',
      detail: 'Stripe config is complete.',
      missing_config_keys: [],
      validation_checks: ['required_fields'],
    },
  },
  {
    provider_key: 'paypal',
    display_name: 'PayPal',
    enabled: true,
    configured: true,
    public_config: {
      client_id: 'paypal-client',
      plan_id_monthly: 'P-ADMIN-MONTHLY',
      product_id: 'PROD-ADMIN',
    },
    secret_fields: {
      client_secret: { configured: true, tail: 'efgh' },
    },
    required_public_fields: ['client_id', 'plan_id_monthly'],
    required_secret_fields: ['client_secret'],
    missing_config_keys: [],
    webhook_url: 'https://api.pdf-flow.test/api/v1/payment/webhooks/paypal',
    updated_at: now,
    encryption_available: true,
    webhook_status: 'manual',
    metadata: {
      provider_key: 'paypal',
      display_name: 'PayPal',
      description: 'PayPal checkout order configuration.',
      settlement: 'subscription',
      supports_subscription: true,
      supports_one_time: true,
      merchant_console_hint: 'PayPal Developer Dashboard > Webhooks',
      setup_notes: ['Configure webhook URL before live use.'],
      validation_checks: ['required_fields'],
      fields: {
        public: [
          paymentConfigField('client_id', 'Client ID'),
          paymentConfigField('plan_id_monthly', 'Monthly Plan ID'),
        ],
        secret: [paymentConfigField('client_secret', 'Client Secret', 'password', true, true)],
      },
    },
    readiness: {
      status: 'ready',
      label: 'Ready',
      detail: 'PayPal config is complete.',
      missing_config_keys: [],
      validation_checks: ['required_fields'],
    },
  },
  {
    provider_key: 'gmpay',
    display_name: 'GM Pay',
    enabled: false,
    configured: true,
    public_config: {
      api_base_url: 'https://pay.pawn.eu.org',
      pid: '1000',
      currency: 'cny',
      token: 'usdt',
      network: 'tron',
      monthly_amount_cents: 990,
    },
    secret_fields: {
      secret_key: { configured: true, tail: '203d' },
    },
    required_public_fields: ['api_base_url', 'pid', 'currency', 'token', 'network'],
    required_secret_fields: ['secret_key'],
    missing_config_keys: [],
    webhook_url: 'https://api.pdf-flow.test/api/v1/payment/webhooks/gmpay',
    updated_at: now,
    encryption_available: true,
    webhook_status: 'manual',
    metadata: {
      provider_key: 'gmpay',
      display_name: 'GM Pay',
      description: 'GM Pay hosted crypto checkout.',
      settlement: 'one_time_entitlement',
      supports_subscription: false,
      supports_one_time: true,
      merchant_console_hint: 'GM Pay merchant console > notify URL',
      setup_notes: ['Only use for controlled smoke tests before webhook validation.'],
      validation_checks: ['required_fields', 'local_signature'],
      fields: {
        public: [
          paymentConfigField('api_base_url', 'API Base URL', 'url'),
          paymentConfigField('pid', 'PID'),
          paymentConfigField('currency', 'Currency'),
          paymentConfigField('token', 'Token'),
          paymentConfigField('network', 'Network'),
          paymentConfigField('monthly_amount_cents', 'Monthly Amount', 'number'),
        ],
        secret: [paymentConfigField('secret_key', 'Secret Key', 'password', true, true)],
      },
    },
    readiness: {
      status: 'ready',
      label: 'Ready',
      detail: 'GM Pay config is complete.',
      missing_config_keys: [],
      validation_checks: ['required_fields', 'local_signature'],
    },
  },
]

const serviceConfigField = (
  key: string,
  label: string,
  input_type: 'text' | 'url' | 'number' | 'password' = 'text',
  required = false,
  secret = false,
) => ({
  key,
  label,
  input_type,
  required,
  secret,
  placeholder: '',
  help_text: '',
  min_value: input_type === 'number' ? 1 : null,
  max_value: null,
})

const serviceProviderConfig = (
  service_key: string,
  provider_key: string,
  display_name: string,
  public_config: Record<string, string | number>,
  secret_fields: Record<string, { configured: boolean; tail: string }> = {},
) => ({
  service_key,
  provider_key,
  display_name,
  enabled: true,
  priority: 100,
  configured: true,
  public_config,
  secret_fields,
  required_public_fields: Object.keys(public_config),
  required_secret_fields: Object.keys(secret_fields),
  missing_config_keys: [],
  updated_at: now,
  encryption_available: true,
  metadata: {
    service_key,
    provider_key,
    display_name,
    description: `${display_name} runtime provider.`,
    validation_checks: ['required_fields'],
    setup_notes: ['Use DB config first, then fallback to server settings.'],
    runtime_fallback: 'settings/default command',
    fields: {
      public: Object.keys(public_config).map((key) =>
        serviceConfigField(key, key, typeof public_config[key] === 'number' ? 'number' : 'text', true),
      ),
      secret: Object.keys(secret_fields).map((key) =>
        serviceConfigField(key, key, 'password', true, true),
      ),
    },
  },
  readiness: {
    status: 'ready',
    label: 'Ready',
    detail: `${display_name} config is complete.`,
    missing_config_keys: [],
    validation_checks: ['required_fields'],
  },
})

const serviceProviders = {
  ocr: [
    serviceProviderConfig('ocr', 'local_tesseract', 'Local Tesseract', {
      tesseract_path: 'tesseract',
      default_language: 'eng',
      languages: 'eng,chi_sim',
    }),
  ],
  office: [
    serviceProviderConfig('office', 'local_libreoffice', 'Local LibreOffice', {
      binary_path: 'soffice',
      timeout_seconds: 120,
    }),
  ],
  ai: [
    serviceProviderConfig(
      'ai',
      'google_gemini',
      'Google Gemini',
      {
        api_base_url: 'https://generativelanguage.googleapis.com',
        model: 'gemini-1.5-pro',
        timeout_seconds: 60,
      },
      { api_key: { configured: true, tail: 'gkey' } },
    ),
  ],
}

const diagnostics = {
  generated_at: now,
  recent_errors: apiErrors,
  recent_failed_jobs: operations.recent_failed_jobs,
  recent_feedback: feedback.map((item) => ({
    id: item.id,
    title: item.title,
    status: item.status,
    severity: item.severity,
    page_url: item.page_url,
    diagnostic_code: item.diagnostic_code,
    created_at: item.created_at,
  })),
  diagnostic_summary: [
    'PDF-Flow diagnostic packet',
    'Generated: 2026-06-11T09:30:00.000Z',
    'Environment: playwright',
    'Services: database=healthy, redis=degraded, worker=healthy',
    'Counts: api_errors=1, failed_jobs=1, open_feedback=1',
    '',
    'Latest API error:',
    '- request_id=req_visual_qa_001',
    '- route=POST /api/v1/files/compress',
    '- status=500, type=WorkerTimeout',
    '- message=Compression worker timed out.',
    '',
    'Privacy note: request bodies and document contents are not included in this packet.',
  ].join('\n'),
  open_feedback_count: 1,
  failed_jobs_count: 1,
  api_error_count: apiErrors.length,
}

const maintenance = {
  test_users_count: 1,
  live_acceptance_feedback_count: 1,
  open_feedback_count: 1,
  api_error_count: apiErrors.length,
  failed_jobs_count: 1,
  running_jobs_count: 1,
  file_retention: {
    scanned_count: 8,
    removable_count: 2,
    removed_count: 0,
    removed_bytes: 0,
    skipped_count: 6,
    upload_dir: 'D:/code/PDF_Flow/backend/uploads',
  },
}

const paymentSummary = {
  generated_at: now,
  total_orders: 3,
  pending_orders: 1,
  paid_orders: 1,
  failed_orders: 0,
  amount_mismatch_orders: 1,
  currency_mismatch_orders: 0,
  expired_pending_orders: 1,
  paid_amount_cents: 990,
  currency_breakdown: {
    USD: 990,
  },
  providers: [
    {
      key: 'stripe',
      display_name: 'Stripe',
      enabled: true,
      configured: true,
      acceptance_status: 'accepted',
      acceptance_label: 'Smoke passed',
      acceptance_detail: 'At least one paid order has a matching applied PaymentEvent.',
      acceptance_blockers: [],
      latest_paid_event_at: '2026-06-11T09:25:30.000Z',
      settlement: 'subscription',
      supports_subscription: true,
      supports_one_time: true,
      open_orders: 0,
      paid_orders: 1,
      failed_orders: 0,
      latest_order_at: '2026-06-11T09:25:00.000Z',
      detail: 'Enabled and configuration is present.',
      webhook_url: 'https://api.pdf-flow.test/api/v1/payment/webhooks/stripe',
      success_return_url: 'https://app.pdf-flow.test/payment/success',
      cancel_return_url: 'https://app.pdf-flow.test/payment/cancel',
      merchant_console_hint: 'Stripe Dashboard > Developers > Webhooks',
      required_config_keys: [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'STRIPE_PRICE_ID_MONTHLY',
        'STRIPE_PRICE_ID_YEARLY',
      ],
      missing_config_keys: [],
      setup_notes: [
        'Use the webhook/notify URL as the provider server callback URL.',
        'Success and cancel URLs are user return pages only; they must not be treated as payment proof.',
      ],
      sandbox_runbook: [
        'Enable this provider in PAYMENT_ENABLED_PROVIDERS only after required backend config is present.',
        'Use Stripe test card 4242 4242 4242 4242 and confirm the checkout.session.completed webhook is delivered.',
      ],
      go_live_checklist: [
        'Webhook/notify URL is configured in the provider dashboard exactly as shown here.',
        'Duplicate webhook replay does not create duplicate entitlement time.',
      ],
      expected_event_flow: [
        'checkout_created -> Stripe Checkout',
        'checkout.session.completed webhook received',
        'PaymentEvent processing_status=applied',
      ],
      troubleshooting_steps: [
        'If no PaymentEvent appears, check provider dashboard delivery logs and BACKEND_PUBLIC_URL reachability.',
      ],
      evidence_fields: [
        'provider',
        'merchant_order_id',
        'provider_event_id',
        'PaymentEvent.processing_status',
      ],
    },
    {
      key: 'epusdt',
      display_name: 'EPUSDT',
      enabled: true,
      configured: false,
      acceptance_status: 'missing_config',
      acceptance_label: 'Missing config',
      acceptance_detail: 'Add backend merchant config before starting sandbox or live smoke tests.',
      acceptance_blockers: [
        'PAYMENT_GATEWAY_CONFIGS.epusdt.merchant_id',
        'PAYMENT_GATEWAY_CONFIGS.epusdt.secret',
        'PAYMENT_GATEWAY_CONFIGS.epusdt.create_url',
      ],
      latest_paid_event_at: null,
      settlement: 'one_time_entitlement',
      supports_subscription: false,
      supports_one_time: true,
      open_orders: 1,
      paid_orders: 0,
      failed_orders: 0,
      latest_order_at: '2026-06-11T09:26:00.000Z',
      detail: 'Enabled but merchant configuration is incomplete.',
      webhook_url: 'https://api.pdf-flow.test/api/v1/payment/webhooks/epusdt',
      success_return_url: 'https://app.pdf-flow.test/payment/success',
      cancel_return_url: 'https://app.pdf-flow.test/payment/cancel',
      merchant_console_hint: 'EPUSDT 管理后台 > 异步通知地址',
      required_config_keys: [
        'PAYMENT_GATEWAY_CONFIGS.epusdt.merchant_id',
        'PAYMENT_GATEWAY_CONFIGS.epusdt.secret',
        'PAYMENT_GATEWAY_CONFIGS.epusdt.create_url',
      ],
      missing_config_keys: [
        'PAYMENT_GATEWAY_CONFIGS.epusdt.merchant_id',
        'PAYMENT_GATEWAY_CONFIGS.epusdt.secret',
        'PAYMENT_GATEWAY_CONFIGS.epusdt.create_url',
      ],
      setup_notes: [
        'Use the webhook/notify URL as the provider server callback URL.',
        'If the gateway supports a custom notify_url, leave it unset to use the backend default unless the merchant console requires an override.',
      ],
      sandbox_runbook: [
        'Create a small monthly test checkout from the Pricing page while signed in as a test account.',
        'Use a low-value USDT test order and verify the gateway callback amount/currency mapping.',
      ],
      go_live_checklist: [
        'Gateway create_url, merchant id, secret, and sign_type match the live gateway documentation.',
        'Amount and currency mismatches remain in a review state instead of granting access.',
      ],
      expected_event_flow: [
        'checkout_created -> provider hosted/QR payment page',
        'provider asynchronous notify/webhook received by backend',
        'PaymentOrder status=paid and entitlement extended once',
      ],
      troubleshooting_steps: [
        'For hosted gateway failures, verify sign_type and parameter ordering against the gateway documentation.',
      ],
      evidence_fields: [
        'provider',
        'merchant_order_id',
        'gateway trade id',
        'gateway callback timestamp',
      ],
    },
    {
      key: 'wechat',
      display_name: 'WeChat Pay',
      enabled: true,
      configured: true,
      acceptance_status: 'needs_review',
      acceptance_label: 'Needs review',
      acceptance_detail: 'Configuration exists, but a payment order or callback needs manual reconciliation.',
      acceptance_blockers: [
        'At least one order is in a manual review state.',
        'At least one payment event failed processing.',
      ],
      latest_paid_event_at: null,
      settlement: 'one_time_entitlement',
      supports_subscription: false,
      supports_one_time: true,
      open_orders: 0,
      paid_orders: 0,
      failed_orders: 1,
      latest_order_at: '2026-06-11T09:27:00.000Z',
      detail: 'Enabled and configuration is present.',
      webhook_url: 'https://api.pdf-flow.test/api/v1/payment/webhooks/wechat',
      success_return_url: 'https://app.pdf-flow.test/payment/success',
      cancel_return_url: 'https://app.pdf-flow.test/payment/cancel',
      merchant_console_hint: '微信支付商户平台 > 产品中心/开发配置 > 支付通知地址',
      required_config_keys: [
        'WECHAT_PAY_APP_ID',
        'WECHAT_PAY_MCH_ID',
        'WECHAT_PAY_SERIAL_NO',
        'WECHAT_PAY_PRIVATE_KEY',
        'WECHAT_PAY_API_V3_KEY',
        'WECHAT_PAY_PLATFORM_CERT',
      ],
      missing_config_keys: [],
      setup_notes: [
        'Use the webhook/notify URL as the provider server callback URL.',
        'WeChat Pay notifications require API v3 key, merchant private key, and platform certificate verification.',
      ],
      sandbox_runbook: [
        'Use WeChat Pay sandbox or a low-value live test because Native pay may depend on merchant account capability.',
        'Verify API v3 notification decryption and platform signature validation before treating the order as paid.',
      ],
      go_live_checklist: [
        'WeChat Pay merchant serial, private key, platform certificate, and API v3 key all match the live merchant.',
        'A real paid test order has a matching PaymentOrder and applied PaymentEvent.',
      ],
      expected_event_flow: [
        'checkout_created -> provider hosted/QR payment page',
        'signature, merchant order id, amount, and currency validated',
        'PaymentEvent processing_status=applied',
      ],
      troubleshooting_steps: [
        'For WeChat Pay decrypt failures, verify API v3 key length and platform certificate freshness.',
      ],
      evidence_fields: [
        'Wechat transaction_id',
        'Wechat out_trade_no',
        'Wechat trade_state',
      ],
    },
  ],
  recent_orders: [
    {
      id: 701,
      user_id: 2,
      user_email: 'smoke-compress@example.com',
      provider: 'wechat',
      provider_display_name: 'WeChat Pay',
      merchant_order_id: 'pf_admin_mismatch',
      provider_order_id: 'wx_mismatch',
      plan: 'monthly',
      amount_cents: 990,
      currency: 'CNY',
      status: 'amount_mismatch',
      checkout_url_present: false,
      qr_code_url_present: true,
      created_at: '2026-06-11T09:27:00.000Z',
      updated_at: '2026-06-11T09:27:30.000Z',
      expires_at: null,
      paid_at: null,
    },
    {
      id: 702,
      user_id: 2,
      user_email: 'smoke-compress@example.com',
      provider: 'stripe',
      provider_display_name: 'Stripe',
      merchant_order_id: 'pf_admin_paid',
      provider_order_id: 'cs_paid',
      plan: 'monthly',
      amount_cents: 990,
      currency: 'USD',
      status: 'paid',
      checkout_url_present: true,
      qr_code_url_present: false,
      created_at: '2026-06-11T09:25:00.000Z',
      updated_at: '2026-06-11T09:25:30.000Z',
      expires_at: null,
      paid_at: '2026-06-11T09:25:30.000Z',
    },
  ],
  recent_events: [
    {
      id: 801,
      order_id: 702,
      provider: 'stripe',
      provider_event_id: 'evt_paid_admin_001',
      merchant_order_id: 'pf_admin_paid',
      provider_order_id: 'cs_paid',
      event_type: 'paid',
      processing_status: 'applied',
      amount_cents: 990,
      currency: 'USD',
      raw_summary: '{"type":"checkout.session.completed"}',
      error_message: null,
      created_at: '2026-06-11T09:25:30.000Z',
    },
    {
      id: 802,
      order_id: 701,
      provider: 'wechat',
      provider_event_id: 'evt_mismatch_admin_001',
      merchant_order_id: 'pf_admin_mismatch',
      provider_order_id: 'wx_mismatch',
      event_type: 'paid',
      processing_status: 'failed',
      amount_cents: 100,
      currency: 'CNY',
      raw_summary: '{"trade_state":"SUCCESS"}',
      error_message: 'Payment amount mismatch',
      created_at: '2026-06-11T09:27:30.000Z',
    },
  ],
  reconciliation_summary: [
    'PDF-Flow payment reconciliation packet',
    'Generated: 2026-06-11T09:30:00.000Z',
    'Environment: playwright',
    'Orders: total=3, paid=1, pending=1, expired_pending=1, needs_review=1',
    'Events: total=2, applied=1, failed=1, ignored=0',
    'Paid amount cents: 990',
    'Provider config: stripe=configured, epusdt=missing_config, wechat=configured',
    '',
    'Latest order:',
    '- merchant_order_id=pf_admin_mismatch',
    '- provider=wechat, status=amount_mismatch, plan=monthly',
    '- amount=990 CNY',
    '',
    'Latest payment event:',
    '- provider_event_id=evt_mismatch_admin_001',
    '- provider=wechat, status=failed, type=paid',
    '- merchant_order_id=pf_admin_mismatch',
    '',
    'Privacy note: provider raw payloads, document contents, and checkout URLs are not included.',
  ].join('\n'),
  integration_evidence_packet: [
    'PDF-Flow payment integration evidence packet',
    'Generated: 2026-06-11T09:30:00.000Z',
    'Environment: playwright',
    'Backend public URL: https://api.pdf-flow.test',
    'Frontend URL: https://app.pdf-flow.test',
    '',
    'Manual test fields to fill:',
    '- tester=',
    '- provider_dashboard_event_url=',
    '- sandbox_or_live=',
    '',
    'Provider: EPUSDT (epusdt)',
    '- enabled=true, configured=false, settlement=one_time_entitlement',
    '- acceptance_status=missing_config, label=Missing config',
    '- acceptance_detail=Add backend merchant config before starting sandbox or live smoke tests.',
    '- acceptance_blockers=PAYMENT_GATEWAY_CONFIGS.epusdt.merchant_id; PAYMENT_GATEWAY_CONFIGS.epusdt.secret; PAYMENT_GATEWAY_CONFIGS.epusdt.create_url',
    '- webhook_url=https://api.pdf-flow.test/api/v1/payment/webhooks/epusdt',
    '- missing_config=PAYMENT_GATEWAY_CONFIGS.epusdt.merchant_id, PAYMENT_GATEWAY_CONFIGS.epusdt.secret, PAYMENT_GATEWAY_CONFIGS.epusdt.create_url',
    '- latest_order:',
    '  merchant_order_id=pf_admin_pending',
    '  provider_order_id=usdt_pending',
    '  status=pending, amount=7900 USD',
    '- expected_event_flow:',
    '  1. checkout_created -> provider hosted/QR payment page',
    '  2. provider asynchronous notify/webhook received by backend',
    '- evidence_fields:',
    '  provider, merchant_order_id, gateway trade id, gateway callback timestamp',
    '',
    'Privacy note: checkout URLs, raw provider payloads, document contents, and secrets are not included.',
  ].join('\n'),
}

const publicConfig = {
  settings: {
    site_name: {
      value: 'PDF-Flow',
      value_type: 'string',
      group: 'brand',
      label: '站点名称',
    },
    maintenance_mode: {
      value: 'false',
      value_type: 'boolean',
      group: 'ops',
      label: '维护模式',
    },
    global_announcement: {
      value: '',
      value_type: 'string',
      group: 'ops',
      label: '全站公告',
    },
  },
  feature_flags: {},
  content_blocks: {},
}

const settings = [
  {
    id: 1,
    key: 'site_name',
    value: 'PDF-Flow',
    value_type: 'string',
    group: 'brand',
    label: '站点名称',
    description: '显示在导航与公开页面中的产品名称。',
    is_public: true,
    updated_at: now,
  },
  {
    id: 2,
    key: 'global_announcement',
    value: '',
    value_type: 'textarea',
    group: 'ops',
    label: '全站公告',
    description: '为空时不显示公告条。',
    is_public: true,
    updated_at: now,
  },
]

const flags = [
  {
    id: 11,
    key: 'compress_pdf',
    label: '压缩 PDF',
    description: '允许用户通过本地或云端流程压缩 PDF 文件。',
    enabled: true,
    is_public: true,
    requires_login: false,
    requires_pro: false,
    maintenance_message: null,
    updated_at: now,
  },
  {
    id: 12,
    key: 'ocr_pdf',
    label: 'OCR 识别',
    description: '使用云端 OCR 队列识别扫描件文本。',
    enabled: true,
    is_public: true,
    requires_login: true,
    requires_pro: true,
    maintenance_message: 'OCR 队列正在扩容，短时间内可能排队。',
    updated_at: now,
  },
]

const contentBlocks = [
  {
    id: 21,
    key: 'homepage.hero',
    locale: 'zh',
    title: 'PDF 工作台',
    content: '快速处理 PDF，同时保留本地优先的隐私体验。',
    description: '首页主视觉文案。',
    is_public: true,
    updated_at: now,
  },
  {
    id: 22,
    key: 'pricing.note',
    locale: 'zh',
    title: '价格说明',
    content: '本地工具免费，云端增强能力按套餐开放。',
    description: '价格页补充说明。',
    is_public: true,
    updated_at: now,
  },
]

interface AdminMockCalls {
  maintenanceGets: number
  cleanupLive: number
  cleanupUsers: number
  cleanupFiles: number
  deleteUsers: number
  passwordChanges?: number
}

async function mockAdminControlRoom(page: Page, calls?: AdminMockCalls) {
  await page.addInitScript(() => {
    if (window.location.search.includes('reason=password_changed')) return
    window.localStorage.setItem('access_token', 'visual-qa-admin-token')
    window.localStorage.setItem('refresh_token', 'visual-qa-refresh-token')
  })

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({ json: adminUser })
  })

  await page.route('**/api/v1/users/me/stats', async (route) => {
    await route.fulfill({
      json: {
        total_requests: 42,
        requests_today: 6,
        storage_used: 1024,
        quota_remaining: -1,
        quota_limit: -1,
        role: 'admin',
      },
    })
  })

  await page.route('**/api/v1/auth/change-password', async (route) => {
    if (calls) calls.passwordChanges = (calls.passwordChanges ?? 0) + 1
    await route.fulfill({ json: { message: 'Password successfully changed' } })
  })

  await page.route('**/api/v1/admin/public-config', async (route) => {
    await route.fulfill({ json: publicConfig })
  })

  await page.route('**/api/v1/admin/**', async (route) => {
    const url = new URL(route.request().url())
    const method = route.request().method()

    if (method !== 'GET') {
      if (url.pathname === '/api/v1/admin/feedback/cleanup-live-acceptance') {
        if (calls) calls.cleanupLive += 1
        await route.fulfill({
          json: {
            closed_count: 1,
            remaining_open_count: 0,
          },
        })
        return
      }

      if (url.pathname === '/api/v1/admin/users/cleanup-test-users') {
        if (calls) calls.cleanupUsers += 1
        await route.fulfill({
          json: {
            deleted_count: 1,
            deleted_emails: ['smoke-compress@example.com'],
            remaining_test_users_count: 0,
          },
        })
        return
      }

      if (url.pathname === '/api/v1/admin/files/cleanup-expired') {
        if (calls) calls.cleanupFiles += 1
        await route.fulfill({
          json: {
            scanned_count: 8,
            removable_count: 2,
            removed_count: 2,
            removed_bytes: 4096,
            skipped_count: 6,
            upload_dir: 'D:/code/PDF_Flow/backend/uploads',
          },
        })
        return
      }

      if (url.pathname === '/api/v1/admin/users/2' && method === 'DELETE') {
        if (calls) calls.deleteUsers += 1
        await route.fulfill({ json: { ok: true } })
        return
      }

      await route.fulfill({ json: { ok: true } })
      return
    }

    if (calls && url.pathname === '/api/v1/admin/maintenance') {
      calls.maintenanceGets += 1
    }

    const responses: Record<string, unknown> = {
      '/api/v1/admin/overview': overview,
      '/api/v1/admin/operations': operations,
      '/api/v1/admin/settings': settings,
      '/api/v1/admin/feature-flags': flags,
      '/api/v1/admin/content-blocks': contentBlocks,
      '/api/v1/admin/users': users,
      '/api/v1/admin/jobs': jobs,
      '/api/v1/admin/payments': paymentSummary,
      '/api/v1/admin/payment-configs': paymentConfigs,
      '/api/v1/admin/pricing-plans': pricingPlans,
      '/api/v1/admin/service-provider-configs/ocr': serviceProviders.ocr,
      '/api/v1/admin/service-provider-configs/office': serviceProviders.office,
      '/api/v1/admin/service-provider-configs/ai': serviceProviders.ai,
      '/api/v1/admin/errors': apiErrors,
      '/api/v1/admin/diagnostics': diagnostics,
      '/api/v1/admin/maintenance': maintenance,
      '/api/v1/admin/health-report': healthReport,
      '/api/v1/admin/feedback': feedback,
      '/api/v1/admin/audit-logs': auditLogs,
    }

    const body = responses[url.pathname]
    if (body === undefined) {
      await route.fulfill({ status: 404, json: { detail: `Unhandled mock path: ${url.pathname}` } })
      return
    }

    await route.fulfill({ json: body })
  })
}

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    bodyScrollWidth: document.body.scrollWidth,
    bodyClientWidth: document.body.clientWidth,
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    offenders: Array.from(document.querySelectorAll<HTMLElement>('body *'))
      .map((element) => {
        const rect = element.getBoundingClientRect()
        return {
          tag: element.tagName.toLowerCase(),
          className: element.getAttribute('class') ?? '',
          text: element.textContent?.trim().replace(/\s+/g, ' ').slice(0, 120),
          width: Math.round(rect.width),
          scrollWidth: element.scrollWidth,
          clientWidth: element.clientWidth,
          right: Math.round(rect.right),
        }
      })
      .filter(
        (item) =>
          item.right > document.documentElement.clientWidth + 2 ||
          item.scrollWidth > item.clientWidth + 2,
      )
      .sort((a, b) => Math.max(b.right, b.scrollWidth) - Math.max(a.right, a.scrollWidth))
      .slice(0, 8),
  }))

  expect(metrics.bodyScrollWidth, JSON.stringify(metrics.offenders, null, 2)).toBeLessThanOrEqual(
    metrics.bodyClientWidth + 2,
  )
  expect(metrics.docScrollWidth, JSON.stringify(metrics.offenders, null, 2)).toBeLessThanOrEqual(
    metrics.docClientWidth + 2,
  )
}

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

async function clickAdminModule(page: Page, label: string) {
  await page
    .getByLabel('Admin modules')
    .getByRole('button', { name: new RegExp(`^${escapeRegExp(label)}\\b`) })
    .click()
}

test.describe('Admin Control Room visual QA', () => {
  for (const viewport of [
    { label: 'desktop', width: 1440, height: 1100 },
    { label: 'mobile', width: 390, height: 900 },
  ]) {
    test(`renders all admin tabs without overflow on ${viewport.label}`, async ({ page }) => {
      await mockAdminControlRoom(page)
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/')

      await expect(page.getByRole('heading', { name: 'PDF-Flow Admin' })).toBeVisible()
      await expect(page.getByLabel('Admin modules').getByText('Command', { exact: true })).toBeVisible()
      await expect(page.getByLabel('Admin modules').getByText('Revenue', { exact: true })).toBeVisible()
      await expectNoHorizontalOverflow(page)

      const tabs = [
        { label: 'Command Center', visibleText: 'Attention Queue' },
        { label: 'Users & Access', visibleText: 'smoke-compress@example.com' },
        { label: 'Job Center', visibleText: 'Readable task operations' },
        { label: 'Feedback Inbox', visibleText: 'tester@example.com' },
        { label: 'Tools & Features', visibleText: 'Tools & Features' },
        { label: 'Service Providers', visibleText: 'Local Tesseract' },
        { label: 'Site Settings', visibleText: 'site_name' },
        { label: 'Content Blocks', visibleText: 'homepage.hero' },
        { label: 'Plans & Pricing', visibleText: 'pro_monthly' },
        { label: 'Payment Providers', visibleText: 'Webhook / Notify URL' },
        { label: 'Payments & Evidence', visibleText: 'PDF-Flow payment reconciliation packet' },
        { label: 'Errors & Diagnostics', visibleText: '/api/v1/files/compress' },
        { label: 'Maintenance', visibleText: 'backend/uploads' },
        { label: 'Security', visibleText: 'Change and sign out' },
        { label: 'Audit Logs', visibleText: 'feature_flag.update' },
      ]

      for (const tab of tabs) {
        await clickAdminModule(page, tab.label)
        await expect(page.locator('h2').filter({ hasText: tab.label }).first()).toBeVisible()
        await expect(page.getByText(tab.visibleText).filter({ visible: true }).first()).toBeVisible()
        await expectNoHorizontalOverflow(page)
      }
    })
  }

  test('presents the job center as readable operations with folded technical details', async ({ page }) => {
    await mockAdminControlRoom(page)
    await page.setViewportSize({ width: 1440, height: 1100 })
    await page.goto('/')

    await clickAdminModule(page, 'Job Center')
    await expect(page.getByText('Readable task operations')).toBeVisible()
    await expect(page.getByText('Running now')).toBeVisible()
    await expect(page.getByText('Failed 24h')).toBeVisible()
    await expect(page.getByText('Most failing')).toBeVisible()
    await expect(page.getByText('Compress PDF').first()).toBeVisible()
    await expect(page.getByText('Failed').first()).toBeVisible()
    await expect(page.getByText('Mixed').filter({ visible: true }).first()).toBeVisible()
    const failedJob = page.locator('article').filter({ hasText: 'quarterly-board-pack-with-long-readable-name.pdf' })
    await expect(failedJob.getByText('Failure summary')).toBeVisible()
    await expect(failedJob.getByText('Worker timed out while optimizing embedded images.').first()).toBeVisible()
    await expect(page.getByTestId('job-technical-details')).toHaveCount(0)

    await failedJob.getByRole('button', { name: 'Details' }).click()
    await expect(failedJob.getByTestId('job-technical-details')).toBeVisible()
    await expect(failedJob.getByText('job_20260611_compress_failed_001')).toBeVisible()
    await expect(failedJob.getByText('source / sources / durable')).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })

  test('changes the admin password from the account security tab and signs out', async ({ page }) => {
    const calls = {
      maintenanceGets: 0,
      cleanupLive: 0,
      cleanupUsers: 0,
      cleanupFiles: 0,
      deleteUsers: 0,
      passwordChanges: 0,
    }
    await mockAdminControlRoom(page, calls)
    await page.goto('/')

    await clickAdminModule(page, 'Security')
    await expect(page.getByRole('heading', { name: 'Change password' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Change and sign out' })).toBeDisabled()

    await page.getByLabel('Current password').fill('CurrentPass123!')
    await page.getByLabel('New password').fill('LettersOnly')
    await page.getByLabel('Confirm password').fill('LettersOnly')
    await expect(page.getByRole('button', { name: 'Change and sign out' })).toBeDisabled()

    await page.getByLabel('New password').fill('NewAdminPass123!')
    await page.getByLabel('Confirm password').fill('DifferentPass123!')
    await expect(page.getByRole('button', { name: 'Change and sign out' })).toBeDisabled()

    await page.getByLabel('Confirm password').fill('NewAdminPass123!')
    await page.getByRole('button', { name: 'Change and sign out' }).click()

    await expect(page.getByText('Password changed. Sign in again')).toBeVisible()
    await page.waitForURL('**/access?reason=password_changed&redirect=/', { timeout: 5000 })
    expect(calls.passwordChanges).toBe(1)
    expect(await page.evaluate(() => window.localStorage.getItem('access_token'))).toBeNull()
    expect(await page.evaluate(() => window.localStorage.getItem('refresh_token'))).toBeNull()
  })

  test('keeps maintenance refresh separate from destructive cleanup actions', async ({ page }) => {
    const calls = {
      maintenanceGets: 0,
      cleanupLive: 0,
      cleanupUsers: 0,
      cleanupFiles: 0,
      deleteUsers: 0,
    }
    await mockAdminControlRoom(page, calls)

    await page.goto('/')
    await clickAdminModule(page, 'Maintenance')
    await expect(page.getByRole('button', { name: 'Refresh counts' })).toBeVisible()

    const maintenanceGetsAfterLoad = calls.maintenanceGets
    await page.getByRole('button', { name: 'Refresh counts' }).click()
    await expect(page.getByText('Maintenance counts refreshed. No cleanup action was executed.')).toBeVisible()
    expect(calls.maintenanceGets).toBeGreaterThan(maintenanceGetsAfterLoad)
    expect(calls.cleanupLive).toBe(0)
    expect(calls.cleanupUsers).toBe(0)
    expect(calls.cleanupFiles).toBe(0)

    await page.getByRole('button', { name: 'Close acceptance feedback' }).click()
    await expect(page.getByText('Closed 1 acceptance feedback report; 0 remain open.')).toBeVisible()
    expect(calls.cleanupLive).toBe(1)

    await page.getByRole('button', { name: 'Delete test accounts' }).click()
    await expect(page.getByRole('dialog', { name: 'Confirm test account deletion' })).toBeVisible()
    await expect(page.getByText('Only smoke-, ocr-, office-, and @example.com test accounts are matched.')).toBeVisible()
    expect(calls.cleanupUsers).toBe(0)
    await page.getByRole('button', { name: 'Cancel' }).click()
    await expect(page.getByRole('dialog', { name: 'Confirm test account deletion' })).toBeHidden()
    expect(calls.cleanupUsers).toBe(0)

    await page.getByRole('main').getByRole('button', { name: 'Delete test accounts' }).click()
    await page.getByRole('dialog', { name: 'Confirm test account deletion' }).getByRole('button', { name: 'Delete test accounts' }).click()
    await expect(page.getByText('Deleted 1 test account; 0 remain.')).toBeVisible()
    expect(calls.cleanupUsers).toBe(1)

    await page.getByRole('button', { name: 'Clean expired temp files' }).click()
    await expect(page.getByRole('dialog', { name: 'Confirm expired temporary file cleanup' })).toBeVisible()
    expect(calls.cleanupFiles).toBe(0)
    await page.getByRole('button', { name: 'Clean temporary files' }).click()
    await expect(page.getByText('Cleaned 2 expired temporary paths and freed 4.0 KB.')).toBeVisible()
    expect(calls.cleanupFiles).toBe(1)
  })

  test('requires in-app confirmation before deleting a user', async ({ page }) => {
    const calls = {
      maintenanceGets: 0,
      cleanupLive: 0,
      cleanupUsers: 0,
      cleanupFiles: 0,
      deleteUsers: 0,
    }
    await mockAdminControlRoom(page, calls)
    await page.goto('/')

    await clickAdminModule(page, 'Users & Access')
    const smokeUserRow = page
      .getByText('smoke-compress@example.com', { exact: true })
      .locator('xpath=ancestor::div[contains(@class, "border-t")][1]')
    await smokeUserRow.getByRole('button', { name: 'Delete' }).click()
    await expect(page.getByRole('dialog', { name: 'Confirm user deletion' })).toBeVisible()
    await expect(page.getByText('This will delete smoke-compress@example.com and related account data.')).toBeVisible()
    expect(calls.deleteUsers).toBe(0)

    await page.getByRole('button', { name: 'Cancel' }).click()
    await expect(page.getByRole('dialog', { name: 'Confirm user deletion' })).toBeHidden()
    expect(calls.deleteUsers).toBe(0)

    await smokeUserRow.getByRole('button', { name: 'Delete' }).click()
    await page.getByRole('button', { name: 'Delete user' }).click()
    await expect(page.getByText('Deleted user: smoke-compress@example.com')).toBeVisible()
    expect(calls.deleteUsers).toBe(1)
  })

  test('copies the diagnostics packet from the errors tab', async ({ page }) => {
    await page.addInitScript(() => {
      let clipboardText = ''
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: {
          writeText: async (value: string) => {
            clipboardText = String(value)
          },
          readText: async () => clipboardText,
        },
      })
    })
    await mockAdminControlRoom(page)
    await page.goto('/')

    await clickAdminModule(page, 'Errors & Diagnostics')
    await expect(page.getByText('PDF-Flow diagnostic packet')).toBeVisible()
    await page.getByRole('button', { name: 'Copy packet' }).click()
    await expect(page.getByText('Copied diagnostic packet')).toBeVisible()

    const copied = await page.evaluate(() => navigator.clipboard.readText())
    expect(copied).toContain('request_id=req_visual_qa_001')
    expect(copied).toContain('Privacy note')
    expect(copied).not.toContain('18MB 文件')
  })
})

test.describe('Admin payment reconciliation QA', () => {
  test('copies the payment reconciliation packet from the payments tab', async ({ page }) => {
    await page.addInitScript(() => {
      let clipboardText = ''
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: {
          writeText: async (value: string) => {
            clipboardText = String(value)
          },
          readText: async () => clipboardText,
        },
      })
    })
    await mockAdminControlRoom(page)
    await page.goto('/')

    await clickAdminModule(page, 'Payment Providers')
    await expect(page.getByText('Payment Provider Center')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Stripe / PayPal / GM Pay configuration' })).toBeVisible()
    await expect(page.getByText('What this controls').first()).toBeVisible()
    await expect(page.getByText('When to use').first()).toBeVisible()
    await expect(page.getByText('Impact').first()).toBeVisible()
    await expect(page.getByText('Readiness').first()).toBeVisible()
    await expect(page.getByText('Public config').first()).toBeVisible()
    await expect(page.getByText('Secret config').first()).toBeVisible()
    await expect(page.getByText('Secrets are write-only').first()).toBeVisible()
    await expect(page.getByText('Configured, ending 1234')).toBeVisible()
    await expect(page.getByText('Operational status').first()).toBeVisible()
    await expect(page.getByText('Smoke passed').first()).toBeVisible()
    await expect(page.getByText('At least one paid order has a matching applied PaymentEvent.').first()).toBeVisible()
    await expect(page.getByText('Stripe hosted checkout, price mapping').first()).toBeVisible()
    await expect(page.getByText('GM Pay cashier creation for crypto checkout').first()).toBeVisible()
    await expect(page.getByText('https://api.pdf-flow.test/api/v1/payment/webhooks/gmpay')).toBeVisible()
    await expect(page.getByText('EPUSDT')).toHaveCount(0)
    await expect(page.getByText('PAYMENT_GATEWAY_CONFIGS.epusdt.secret')).toHaveCount(0)

    await clickAdminModule(page, 'Payments & Evidence')
    await expect(page.getByText('PDF-Flow payment reconciliation packet')).toBeVisible()
    await expect(page.getByText('evt_mismatch_admin_001', { exact: true })).toBeVisible()
    await expect(page.getByText('Payment amount mismatch')).toBeVisible()
    await page.getByRole('button', { name: 'Copy evidence' }).click()
    await expect(page.getByText('Copied payment evidence packet')).toBeVisible()
    const evidenceCopied = await page.evaluate(() => navigator.clipboard.readText())
    expect(evidenceCopied).toContain('PDF-Flow payment integration evidence packet')
    expect(evidenceCopied).toContain('acceptance_status=missing_config')
    expect(evidenceCopied).toContain('provider_dashboard_event_url=')
    expect(evidenceCopied).toContain('gateway trade id')
    expect(evidenceCopied).not.toContain('checkout.stripe.local')
    expect(evidenceCopied).not.toContain('tron:private-payment-address')

    await page.getByRole('button', { name: 'Copy packet' }).click()
    await expect(page.getByText('Copied reconciliation packet')).toBeVisible()

    const copied = await page.evaluate(() => navigator.clipboard.readText())
    expect(copied).toContain('pf_admin_mismatch')
    expect(copied).toContain('Provider config')
    expect(copied).not.toContain('checkout.stripe.local')
  })
})
