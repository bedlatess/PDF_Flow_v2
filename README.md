# PDF-Flow

PDF-Flow is a Vue 3 and FastAPI workspace for everyday PDF work. It combines browser-based tools, account workflows, Pro cloud processing, payment infrastructure, and operational APIs in one repository.

## Features

- Browser PDF tools: merge, split, rotate, compress, image to PDF, PDF to image, delete pages, organize pages, page numbers, crop, watermark, extract text, extract images, flatten, unlock, protect, repair, and visual signing.
- Pro and cloud workflows: OCR, Office to PDF, AI PDF analysis, form filling, annotation, larger processing jobs, and account-level history.
- Account system: email/password auth, OAuth entry points for Google and GitHub, password reset, profile and usage pages.
- Backend operations: file jobs, payment orders and webhooks, feedback diagnostics, feature flags, site settings, content blocks, audit logs, and admin APIs.
- Test coverage: Vitest unit tests, Playwright browser regression tests, pytest backend tests, and server smoke scripts.

## Tech Stack

- Frontend: Vue 3, TypeScript, Vite, Pinia, Vue Router, Vue I18n, Tailwind CSS, Lucide icons.
- PDF processing: pdf-lib, pdfjs-dist, jsPDF, browser workers, and backend PDF services.
- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, Celery, Pydantic.
- Integrations: OAuth providers, Resend-style transactional email, payment provider abstraction, AI/OCR/Office processing hooks.
- Deployment: Docker Compose single-server path with deploy, rollback, and smoke scripts.

## Requirements

- Node.js 22
- npm 10+
- Python 3.11
- Docker and Docker Compose for the full backend stack

## Quick Start

Install frontend dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

Set up the backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For local dependencies through Docker:

```bash
docker compose up -d postgres redis
```

For the full Docker stack from the repository root:

```bash
docker compose --env-file backend/.env up -d --build
```

## Verification

Frontend:

```bash
npm run test:unit:ci
npm run type-check
npm run build
```

Backend:

```bash
cd backend
pytest tests -q
```

Core browser regression suite:

```bash
npm run test:e2e:core
```

Server smoke checks:

```bash
bash scripts/smoke-test.sh
bash scripts/main-smoke-suite.sh
```

## Project Layout

```text
src/                    Vue frontend application
src/admin/              Dedicated admin frontend entry and admin API client
backend/                FastAPI backend, migrations, services, tasks, and tests
tests/e2e-playwright/   Playwright browser regression specs
tests/unit/             Vitest unit tests
tests/fixtures/         Test PDF fixtures and fixture generators
scripts/                Deploy, rollback, smoke, and Playwright helpers
docs/PROJECT_MASTER.md  Internal development direction and progress tracker
public/                 Static manifest, service worker, and icons
```

## Configuration

Never commit real credentials. Use local `.env` files and server-side `backend/.env`.

Important backend configuration groups:

- Core: `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `BACKEND_PUBLIC_URL`, `FRONTEND_URL`, `ADMIN_FRONTEND_URL`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`
- OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
- Email: `RESEND_API_KEY`, `EMAIL_FROM`, `PASSWORD_RESET_TOKEN_EXPIRE_HOURS`
- Payments: provider credentials, webhook secrets, signing keys, hosted gateway URLs
- AI/OCR/Office: provider keys and processing service settings

The public frontend and admin frontend are separate Vite entries. Local Docker exposes them as:

```text
http://localhost:5173  public app
http://localhost:5174  admin app
```

For production, set `FRONTEND_URL` to the public HTTPS origin and `ADMIN_FRONTEND_URL` to the prepared admin HTTPS origin. The backend automatically includes both URLs in CORS, and `ALLOWED_ORIGINS` can list additional trusted origins when needed.

OAuth callback URLs use this pattern:

```text
{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/google/callback
{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/github/callback
```

Payment providers should call:

```text
{BACKEND_PUBLIC_URL}/api/v1/payment/webhooks/{provider}
```

Frontend payment success and cancel pages are return pages only. Backend-verified provider events are the payment trust boundary.

## Deployment

The active repository is:

```text
https://github.com/bedlatess/PDF_Flow_v2.git
```

This workspace and the production server use the remote name `v2`.
The latest verified production deployment is commit `77d7d8d8e4551fb3e3118a0bf16df20d89f73e69` at `https://pdf.pawn.eu.org`.

```bash
git remote -v
git pull --ff-only v2 main
```

Current single-server deployment:

```bash
cd /root/data/docker_data/PDF/pdf-flow
git pull --ff-only v2 main
bash scripts/deploy-main.sh
```

Local server access notes:

- `ssh/ssh.example.md` documents the expected local access-file shape.
- Put real server access values in `ssh/ssh.md` only. It is ignored by Git and must stay out of commits.

The frontend image builds both `dist/` and `dist-admin/`. Nginx serves the public app from `PUBLIC_FRONTEND_HOST` and the admin app from `ADMIN_FRONTEND_HOST`; the admin server adds `X-Robots-Tag: noindex, nofollow` and a stricter CSP. For local Compose, ports `5173` and `5174` map to those two entries.

For production, keep backend-only values in `backend/.env`. Put Compose/frontend host values in an untracked `.deploy.env` file:

```text
PUBLIC_FRONTEND_HOST=pdf.pawn.eu.org
ADMIN_FRONTEND_HOST=admin.pawn.eu.org
```

Check status:

```bash
docker compose --env-file backend/.env -f docker-compose.yml ps
curl http://localhost:8000/health
cat .deploy_state/main/current_deployed_commit
```

Production acceptance:

```bash
PUBLIC_URL=https://pdf.pawn.eu.org \
ADMIN_URL=https://admin.pawn.eu.org \
bash scripts/production-acceptance.sh
```

Set `RUN_WRITE_PROBE=1` only when you also provide `LIVE_ADMIN_EMAIL` and `LIVE_ADMIN_PASSWORD`; otherwise the acceptance script stays read-only.

Rollback:

```bash
bash scripts/rollback-main.sh
```

Rollback uses the last successful commit recorded in `.deploy_state/`. Database schema rollback is not automatic, so back up data before risky migrations.

## Contributing

1. Create a focused branch from `main`.
2. Keep changes scoped and follow the existing frontend/backend boundaries.
3. Add or update tests for touched behavior.
4. Run the relevant verification commands.
5. Open a pull request against `bedlatess/PDF_Flow_v2`.

Use concise conventional-style commit messages:

```text
feat: add new PDF tool
fix: resolve file upload timeout
docs: update project direction
refactor: simplify auth service
test: add coverage for merge PDF
chore: update dependencies
```

## Development Direction

For internal progress, architecture decisions, known risks, and the next refactor plan, read [docs/PROJECT_MASTER.md](./docs/PROJECT_MASTER.md).

## License

MIT License. See [LICENSE](./LICENSE).
