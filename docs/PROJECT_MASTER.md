# PDF-Flow Maintenance Notes

This file keeps the project state short and current. Historical rewrite logs were removed from the repository so the active codebase stays readable.

## Current Deployment

- Repository: `https://github.com/bedlatess/PDF_Flow_v2`
- Branch: `main`
- Server path: `/root/data/docker_data/PDF/pdf-flow`
- Frontend: Docker service `frontend`, exposed on port `5173`
- Backend: Docker service `backend`, exposed on port `8000`
- Database: bundled Docker Compose Postgres service
- Redis: bundled Docker Compose Redis service

## Routine Server Update

```bash
cd /root/data/docker_data/PDF/pdf-flow
git pull --ff-only origin main
bash scripts/deploy-main.sh
```

## Admin Bootstrap

Create or promote the first admin from the trusted server shell:

```bash
cd /root/data/docker_data/PDF/pdf-flow
PDF_FLOW_ADMIN_EMAIL=owner@example.com \
PDF_FLOW_ADMIN_PASSWORD='change-this-strong-password' \
PDF_FLOW_ADMIN_NAME='PDF-Flow Owner' \
bash scripts/init-admin.sh
```

- Existing accounts are promoted to `admin`, reactivated, and verified.
- Existing passwords are kept unless `UPDATE_ADMIN_PASSWORD=1` is set.
- No public admin-initialization API is exposed.

## Verification Gates

Local frontend:

```bash
npm run type-check
npm run build
```

Local backend:

```bash
cd backend
pytest tests -q
```

Server:

```bash
bash scripts/smoke-test.sh
bash scripts/main-smoke-suite.sh
docker compose --env-file backend/.env -f docker-compose.yml ps
curl http://localhost:8000/health
```

## Product Priorities

1. Keep the public PDF tools fast, clear, and visually consistent.
2. Keep Pro differentiation subtle and based on capability, not repeated labels.
3. Keep payment trust on the backend; frontend checkout pages only initiate orders.
4. Keep production secrets out of Git.
5. Prefer small, verified changes over broad rewrites.

## Current Stage

- Stage: pre-P0 acceptance hardening.
- Focus: public UI quality, account recovery, payment entry, and production deploy stability.
- P0 resumes after the public shell, account recovery, pricing/payment entry, admin access, and deploy smoke checks are stable on the v2 server.
- Independent backend split should wait until the single-repo deployment is stable in production. The current backend has the domain boundaries needed for a later split; separating it too early would add deployment risk before P0 closes.

## Latest Progress

- Public page polish: Features and Pricing now use denser, tool-first layouts with clearer plan comparison, quieter Pro treatment, and fewer oversized promotional sections.
- Tool pages: shared tool headers and upload zones were tightened, and each tool page now shows concise next-step guidance below the upload area so empty states feel intentional instead of unfinished.
- Public tools: tightened Home and Tools Center spacing so free tool cards use less empty vertical space.
- Copy cleanup: public tool and pricing pages now avoid internal phrases such as local-first/cloud-processing in ordinary user flows. Legal and admin diagnostics keep precise processing terms where needed.
- Pro presentation: Pro badge styling is smaller and quieter, with Pro used as the main visual differentiator instead of repeated upgrade copy.
- Pricing/payment: Pro checkout now opens a payment-method modal. Users click upgrade, choose a provider, and continue; unavailable provider states remain user-facing and backend payment confirmation is still the source of truth.
- Account recovery: frontend routes for `/auth/forgot-password` and `/auth/reset-password` are connected to the existing backend reset endpoints. Email delivery remains configurable for production; when mail is not configured, the UI gives a manual recovery fallback instead of pretending the email definitely arrived.
- Admin bootstrap: trusted CLI initializer added for first-admin creation or promotion, including audit logging and repeat-safe behavior.
- Completion audit: public tool copy was re-scanned and cleaned again so ordinary tool/pricing/account flows no longer lean on internal local/cloud/server wording. Legal policy and admin diagnostics keep precise processing terms where they are necessary.

## Cleanup Rules

- Do not commit `dist/`, `node_modules/`, `.tmp/`, `.env`, `.deploy_state/`, `.deploy_backups/`, or SSH credentials.
- Keep rollback and smoke scripts while the single-server deployment depends on them.
- Keep generated screenshots and browser traces out of Git unless they are deliberate documentation artifacts.
- Replace temporary assets with real static assets when they are referenced by `manifest.json` or `index.html`.

## Known Follow-Ups

- Configure and verify real payment provider callbacks.
- Configure OAuth, email, and AI credentials for production acceptance.
- Add a polished product icon and favicon set when branding is final.
- Consider moving backend and frontend into separate deployables only after the current single-server release is stable.
