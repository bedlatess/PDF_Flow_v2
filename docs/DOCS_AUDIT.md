# Documentation Audit

Last reviewed: 2026-06-13

This folder is for short-lived operations knowledge and current project direction. It should not contain old rewrite diaries, broken encoding, credentials, or implementation claims that are no longer true.

## Current Docs

### `PROJECT_MASTER.md`

Purpose: compact project state, deployment target, verification gates, product priorities, and near-term follow-ups.

Current fit: mostly accurate. It correctly points to `PDF_Flow_v2`, the single-server Docker Compose deployment, and the need to keep public UI quality and Pro presentation restrained.

Gap: the stage language still says "pre-P0 acceptance hardening". The current code has moved past several items listed there: public shell, account recovery, pricing/payment entry, admin access, deployment smoke checks, gated tool flow, and tool-page regression coverage now exist. It should be periodically refreshed after each acceptance batch.

### `STAGING_DEPLOY_GUIDE.md`

Purpose: server deployment runbook for the current single-server setup.

Current fit: accurate for the active deployment. The deploy script still builds Compose services, runs migrations, smoke tests `/health`, and records `.deploy_state/main/current_deployed_commit`.

Gap: the filename says "staging", while the content now describes `main` deployment on the active v2 server. Rename to `DEPLOY_GUIDE.md` later if we want cleaner naming; leave it for now because README and backend README already link to it.

### `OAUTH_SETUP.md`

Purpose: OAuth provider setup and acceptance checklist.

Current fit: refreshed. The previous file contained mojibake and stale implementation-history prose. It now reflects the current backend routes, frontend callback route, environment variables, provider callback URLs, and regression tests.

Gap: account linking routes exist in backend, but no polished user-facing account-link/unlink UI is part of the current acceptance surface.

### `backend/README.md`

Purpose: backend runbook and API ownership summary.

Current fit: refreshed. It describes auth, file jobs, admin, payments, and backend-owned trust boundaries.

Gap: payment provider framework exists, but production acceptance still depends on real provider credentials, webhook dashboard setup, and sandbox or low-value live smoke tests.

### `backend/docs/EMAIL_SERVICE.md`

Purpose: email delivery setup notes.

Current fit: still relevant because password recovery and account emails rely on provider configuration.

Gap: production needs real sender/domain verification and a successful reset-email smoke test.

## Code vs Docs Delta

- Docs should say the active repository is `bedlatess/PDF_Flow_v2`; code and deployment already use that.
- Docs should treat the app as a single repo and single-server deployment for now; the backend has domain boundaries, but it is not split into a separate deployable.
- Docs should not promise production OAuth, payment, AI, or email acceptance unless credentials and callback/smoke evidence exist.
- Docs should mention that public tool flow regressions now exist in `tests/e2e-playwright/tool-flow-regression.spec.ts`.
- Docs should avoid internal rewrite logs. Keep durable runbooks, setup notes, and current roadmap only.

## Cleanup Policy

Keep:

- Deployment, rollback, smoke, OAuth, email, and project-state docs.
- Backend README as the service runbook.
- Alembic migrations and tests, even if they look old; they are executable history.

Remove or rewrite:

- Mojibake or unreadable text.
- Historical plan diaries that no longer guide current work.
- Generated output, browser traces, caches, build artifacts, and local credentials.
- Documentation that claims a feature is production-ready without a matching smoke test or provider configuration.

## Recommended Next Direction

1. Finish production acceptance for external integrations: OAuth credentials, email reset delivery, payment webhooks, AI/OCR provider keys, and evidence from smoke tests.
2. Keep tightening public tool UX with regression tests before adding more tools.
3. Refresh `PROJECT_MASTER.md` after each acceptance batch so it stays a control document, not a history dump.
4. Consider renaming `STAGING_DEPLOY_GUIDE.md` to `DEPLOY_GUIDE.md` once external links are updated.
5. Split frontend/backend deployables only after the current single-server release is stable with real provider callbacks.
