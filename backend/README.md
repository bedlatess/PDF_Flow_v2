# PDF-Flow Backend

FastAPI backend for PDF-Flow. It owns authentication, account and enterprise APIs, cloud PDF jobs, OCR/Office/AI integrations, admin operations, feedback diagnostics, file retention, email, and provider-neutral payment verification.

For current project status and roadmap, read [../docs/PROJECT_MASTER.md](../docs/PROJECT_MASTER.md). This file is only a backend runbook.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Create local environment config:

```bash
cp .env.example .env
```

Run migrations:

```bash
alembic upgrade head
```

Start API and worker through the helper:

```bash
./start.sh
```

Or start them manually:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
celery -A app.celery_worker worker --loglevel=info
```

API docs are available after startup:

- `http://localhost:8000/api/docs`
- `http://localhost:8000/api/redoc`
- `http://localhost:8000/health`

## Docker Compose

From the repository root, start dependencies only:

```bash
docker compose up -d postgres redis
```

For the full local stack:

```bash
docker compose --env-file backend/.env up -d --build
```

The deploy and rollback scripts automatically pass `backend/.env` to Docker Compose when that file exists. To use a different env file, set `COMPOSE_ENV_FILE=/path/to/file`.

## Test Commands

```bash
pytest tests -q
```

Common targeted checks:

```bash
pytest tests/test_auth.py -q
pytest tests/test_admin.py -q
pytest tests/test_admin_bootstrap.py -q
pytest tests/test_files.py -q
pytest tests/test_payment_domain.py -q
```

## Admin Bootstrap

The first admin is created from a trusted shell, not from a public web route.

Docker deployment:

```bash
PDF_FLOW_ADMIN_EMAIL=owner@example.com \
PDF_FLOW_ADMIN_PASSWORD='change-this-strong-password' \
PDF_FLOW_ADMIN_NAME='PDF-Flow Owner' \
bash scripts/init-admin.sh
```

Backend container or local backend working directory:

```bash
python -m app.cli.init_admin --email owner@example.com --password 'change-this-strong-password'
```

If the email already exists, the command promotes the account to `admin`, activates and verifies it, and keeps the existing password. Add `UPDATE_ADMIN_PASSWORD=1` for the script or `--update-password` for the Python command when you intentionally want to rotate the password.

## Main API Areas

- Auth and OAuth
- Users and account usage
- File upload, download, and processing jobs
- Cloud PDF/OCR/Office/AI workflows
- Enterprise API keys, usage, billing, webhooks, and documentation data
- Feedback and diagnostic logging
- Admin Control Room APIs
- Payment providers, payment orders, provider callbacks/webhooks, and payment event ledgering
- Health and operational checks

## Payment Boundary

The backend is the payment trust boundary. Frontend return pages are never payment proof. Entitlements are granted only after backend-created orders are verified through provider callbacks, captures, amount/currency checks, and idempotent `PaymentEvent` handling.

Supported provider framework:

- Stripe
- PayPal
- EPay
- Alipay
- WeChat Pay
- TokenPay
- BEPUSDT
- EPUSDT
- OKPay

Real acceptance requires merchant credentials, dashboard callback setup, and sandbox or low-value live smoke tests.

## Environment Notes

Use `.env.example` as the template. Important groups:

- Core: `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `BACKEND_PUBLIC_URL`, `FRONTEND_URL`
- OAuth: Google/GitHub client ids and secrets
- Email: Resend config, see [docs/EMAIL_SERVICE.md](./docs/EMAIL_SERVICE.md)
- AI/OCR/Office: Gemini and processing service settings
- Payments: provider credentials, signing secrets, webhook ids, and hosted gateway configs
- Monitoring: Sentry/PostHog keys

For Docker Compose, the bundled Postgres service is used by default. If you want an external database in Compose, set `COMPOSE_DATABASE_URL` or provide a `docker-compose.override.yml`.

Never commit real credentials.

## Migrations

Alembic migrations are database history and must not be deleted during cleanup.

```bash
alembic upgrade head
alembic current
```

## Related Docs

- [Project master manual](../docs/PROJECT_MASTER.md)
- [OAuth setup](../docs/OAUTH_SETUP.md)
- [Staging deploy guide](../docs/STAGING_DEPLOY_GUIDE.md)
- [Email service](./docs/EMAIL_SERVICE.md)
