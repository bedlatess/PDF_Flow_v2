# PDF-Flow

PDF-Flow is a Vue and FastAPI PDF workspace with free browser tools, Pro document workflows, account management, admin operations, and payment infrastructure.

## What Is Included

- Vue 3 frontend with public pages, PDF tools, account pages, pricing, enterprise dashboard, and admin Control Room.
- FastAPI backend with authentication, file APIs, advanced PDF jobs, AI/OCR/Office workflows, payments, feedback, admin diagnostics, and Alembic migrations.
- Docker Compose production path for the current single-server deployment.
- Playwright, Vitest, and backend pytest coverage for the main product surfaces.

## Quick Start

Install frontend dependencies:

```bash
npm install
```

Run the frontend dev server:

```bash
npm run dev
```

Run the backend locally:

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verification

Frontend:

```bash
npm run type-check
npm run build
npm run test:e2e:core
```

Backend:

```bash
cd backend
pytest tests -q
```

Useful server smoke checks:

```bash
bash scripts/smoke-test.sh
bash scripts/main-smoke-suite.sh
```

## Project Layout

```text
src/                    Vue frontend application
backend/                FastAPI backend, migrations, services, tests
tests/e2e-playwright/   Browser regression specs
scripts/                Deploy, rollback, smoke, and test helpers
docs/                   Operations and setup notes
public/                 Static manifest, service worker, and icons
```

## Deployment

The current server deployment uses the `main` branch from `PDF_Flow_v2`.

```bash
ssh root@155.248.195.94
cd /root/data/docker_data/PDF/pdf-flow
git pull --ff-only v2 main
bash scripts/deploy-main.sh
```

If an older checkout still names the `PDF_Flow_v2` remote `origin`, rename it with `git remote rename origin v2` before deploying.

Check the result:

```bash
docker compose --env-file backend/.env -f docker-compose.yml ps
curl http://localhost:8000/health
```

See [docs/STAGING_DEPLOY_GUIDE.md](./docs/STAGING_DEPLOY_GUIDE.md) for the full runbook.

## Configuration

Never commit real credentials. Use local `.env` files and server-side `backend/.env`.

Useful setup docs:

- [docs/STAGING_DEPLOY_GUIDE.md](./docs/STAGING_DEPLOY_GUIDE.md)
- [docs/OAUTH_SETUP.md](./docs/OAUTH_SETUP.md)
- [docs/DOCS_AUDIT.md](./docs/DOCS_AUDIT.md)
- [backend/README.md](./backend/README.md)
- [backend/docs/EMAIL_SERVICE.md](./backend/docs/EMAIL_SERVICE.md)

## License

MIT License. See [LICENSE](./LICENSE).
