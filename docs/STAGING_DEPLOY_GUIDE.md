# PDF-Flow Deployment Guide

This is the current single-server deployment runbook for `PDF_Flow_v2`.

## Server Location

```bash
ssh root@155.248.195.94
cd /root/data/docker_data/PDF/pdf-flow
```

The official Git remote is named `v2` and points to:

```text
https://github.com/bedlatess/PDF_Flow_v2.git
```

If an older checkout still names this remote `origin`, rename it once:

```bash
git remote rename origin v2
git remote -v
```

## Deploy Main

```bash
git pull --ff-only v2 main
bash scripts/deploy-main.sh
```

The deploy script:

1. Uses `backend/.env` as the Docker Compose env file when present.
2. Refuses tracked server-side changes.
3. Creates a timestamped deploy backup under `.deploy_backups/`.
4. Pulls the selected branch with `--ff-only`.
5. Builds and starts Docker Compose services.
6. Runs Alembic migrations inside the backend container.
7. Runs the health smoke test.
8. Records the successful commit under `.deploy_state/`.

## Check Status

```bash
docker compose --env-file backend/.env -f docker-compose.yml ps
curl http://localhost:8000/health
cat .deploy_state/main/current_deployed_commit
```

Expected services:

- `frontend`
- `backend`
- `celery-worker`
- `postgres`
- `redis`

## Full Smoke Suite

```bash
bash scripts/main-smoke-suite.sh
```

This runs:

- health smoke
- business PDF smoke
- OCR smoke
- Office-to-PDF smoke

## Rollback

```bash
bash scripts/rollback-main.sh
```

Rollback uses the last successful commit recorded in `.deploy_state/`. Database schema rollback is not automatic, so keep database backups before risky migrations.

## Environment

Server secrets live in `backend/.env`. Do not commit real credentials.

Review these values before production acceptance:

- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `ALLOWED_HOSTS`
- `FRONTEND_URL`
- `BACKEND_PUBLIC_URL`
- OAuth provider keys
- Email provider keys
- Payment provider keys and webhook settings
- AI provider keys

## Payment Webhooks

Provider dashboards should call:

```text
{BACKEND_PUBLIC_URL}/api/v1/payment/webhooks/{provider}
```

Frontend success and cancel URLs are only return pages. Entitlements must come from backend-verified payment events.

## Local Release Checks

```bash
npm run type-check
npm run build
cd backend
pytest tests -q
```
