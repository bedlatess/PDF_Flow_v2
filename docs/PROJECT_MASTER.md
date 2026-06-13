# PDF-Flow Project Master

Last updated: 2026-06-13

This is the internal source of truth for development direction, current progress, architecture decisions, known risks, and next work. Public-facing setup belongs in `README.md`.

## Current Status

- Official repository: `https://github.com/bedlatess/PDF_Flow_v2.git`
- Official remote name: `v2`
- Branch: `main`
- Current deployed commit after the last verified server run: `c10f65d8183954d7b7381c1189bc3a935f7c08f0`
- Server path: `/root/data/docker_data/PDF/pdf-flow`
- Deployment model: single repository, single Docker Compose server
- Runtime services: `frontend`, `backend`, `celery-worker`, `postgres`, `redis`
- Current stage: production acceptance hardening before a platform refactor

## Product Surface

Implemented public PDF tools:

- Merge PDF
- Split PDF
- Rotate PDF
- Compress PDF
- Image to PDF
- PDF to image
- Delete pages
- Organize pages
- Page numbers
- Crop PDF
- Flatten PDF
- Repair PDF
- Protect PDF
- Unlock PDF
- Sign PDF with a visual signature image
- Extract text
- Extract images
- Watermark PDF

Implemented login, Pro, and cloud surfaces:

- Email/password auth
- Google and GitHub OAuth routes
- Password recovery pages and backend reset endpoints
- Profile and usage pages
- Local browser history
- OCR PDF
- Office to PDF
- AI PDF analyzer
- Fill PDF form
- Annotate PDF
- Payment method selection and backend payment trust boundary
- Enterprise dashboard foundations

Implemented operations:

- Hidden admin Control Room at `/control-room`
- Admin bootstrap from trusted shell
- Feature flags
- Public site settings
- Content blocks
- User management
- Job observation
- Feedback triage
- API error summaries
- Payment reconciliation summaries
- Maintenance cleanup
- Audit logs
- Health reports

## Architecture Snapshot

Frontend:

- Vue 3, TypeScript, Vite, Pinia, Vue Router, Vue I18n, Tailwind CSS.
- Main source tree is currently `src/`.
- Admin UI is currently embedded in the main frontend under `src/views/admin` and `src/components/admin`.
- Tools are individual route components under `src/views/tools`.
- Tool metadata lives in `src/data/pdfTools.ts`.
- i18n currently combines `src/locales/*.json` with a large `src/locales/overrides.ts`.

Backend:

- FastAPI service under `backend/app`.
- Domain services already exist for auth, account, enterprise, files, payment, and admin.
- Alembic migrations are executable history and must be kept.
- Admin API routes are under `/api/v1/admin/*`.
- Public config is served from `/api/v1/admin/public-config`.
- Celery handles async jobs and background tasks.

Deployment:

- Server deploy uses `bash scripts/deploy-main.sh`.
- Deploy script builds Compose services, runs migrations, runs health smoke tests, and records `.deploy_state/main/current_deployed_commit`.
- Rollback uses `bash scripts/rollback-main.sh` and the last successful commit record.

## Recent Verified Work

- Cleaned GitHub/local repository history leftovers and removed old `origin` usage.
- Made `v2` the official remote locally and on the server.
- Cleaned stale generated artifacts and ignored local caches.
- Cleaned OAuth, backend, and repository docs into the two-document model.
- Cleaned locale JSON baselines to minimal valid fallbacks; the current UI copy still comes mainly from `src/locales/overrides.ts`.
- Removed fake scheduled email campaigns that only logged success instead of sending real messages.
- Cleaned backend Celery/task/email/monitoring text that still carried historical mojibake or fragile console characters.
- Normalized the PDF fixture generator to a single `.mjs` script and removed the duplicate `.ts` copy.
- Fixed CI/runtime alignment around Node 22 and current target tests.
- Fixed an outdated DragDropZone unit test.
- Verified server health after deploying `c10f65d`:
  - `frontend` healthy
  - `backend` healthy
  - `celery-worker` healthy
  - `postgres` healthy
  - `redis` healthy
  - `/health` returns production healthy
  - frontend home returns HTTP 200

## Known Code Issues

Fix these before large feature work:

1. Repository metadata in `package.json` previously pointed to placeholder GitHub URLs. Keep it aligned with `PDF_Flow_v2`.
2. `src/locales/overrides.ts` is too large and acts as an uncontrolled patch layer over JSON locale files.
3. `ControlRoom.vue` remains too large and mixes orchestration, formatting, clipboard summaries, confirmation flows, and tab-level actions.
4. Admin UI is embedded in the public app. This is workable for acceptance but not ideal for a formal production admin portal.
5. Locale handling is manual-only and defaults to `zh`; it does not support locale-prefixed routes or browser-language negotiation.
6. Public content blocks only normalize `zh*` to `zh` and otherwise fall back to `en`, so future languages need a more formal locale model.
7. Some internal diagnostic codes are still visible in advanced/account/admin-adjacent flows. They are useful for support, but public user-facing copy should stay calm and hide internal detail unless troubleshooting is needed.

## Documentation Policy

Only two Markdown files should be treated as primary docs:

- `README.md`: public/open-source introduction, setup, verification, deployment overview, contribution basics.
- `docs/PROJECT_MASTER.md`: internal development status, roadmap, operations details, acceptance checklist, and refactor direction.

Avoid adding new Markdown files unless there is a strong reason. If a topic is durable, add it here. If it is public setup, add it to `README.md`. Temporary notes should not be committed.

## Competitor Notes

Reviewed reference products:

- iLovePDF
- PDF24 Tools
- Smallpdf

Common patterns:

- Tool matrix is the product center.
- Every major tool has its own SEO page.
- Tools are grouped by user intent: organize, optimize, convert, edit, secure, sign, AI/OCR.
- Language is reflected in URL structure, not just a manual select.
- Trust copy explains privacy, local/online processing, limits, and plan boundaries.
- Conversion and edit workflows are broader than our current set.

Priority feature gaps:

1. PDF to Word
2. PDF to Excel
3. PDF to PowerPoint
4. Word/Excel/PowerPoint to PDF improvements
5. HTML or webpage to PDF
6. Real edit PDF workflow
7. Redact PDF
8. Compare PDFs
9. Translate PDF
10. PDF/A conversion or validation
11. Stronger e-sign workflow
12. Batch processing and cloud file import

Do not add all of these immediately. The platform refactor below should come first so new tools do not multiply route, i18n, and UI duplication.

## Refactor Direction

### Phase 1: Foundation Cleanup

Goal: remove obvious metadata and code hygiene risks before architecture work.

- Completed: `package.json` repository metadata points to `PDF_Flow_v2`.
- Completed: docs are consolidated to `README.md` and this file.
- Completed: generated artifacts and duplicate fixture scripts were removed from Git.
- Completed: `v2/main` is the only official project line.
- Completed: known mojibake patterns were removed from the scanned source/docs surface.
- Completed: unfinished scheduled email tasks were removed until real templates and product requirements exist.
- Ongoing: keep `src/locales/overrides.ts` stable until Phase 2 replaces the i18n model.

Acceptance:

- `rg` finds no known mojibake patterns in source/docs, excluding intentional non-English user copy.
- `npm run test:unit:ci`, `npm run type-check`, `npm run build`, and targeted backend tests pass.

### Phase 2: i18n v2 and Locale Routes

Goal: make internationalization a platform capability.

Recommended route model:

```text
/zh-cn/
/en/
/ja/
/ko/
/de/
/zh-cn/tools/merge
/en/tools/merge
```

Locale resolution order:

1. URL locale prefix
2. User-selected locale stored in cookie/localStorage
3. `Accept-Language`
4. Optional IP country hint
5. Default locale

Implementation direction:

- Replace `en/zh/es + overrides.ts` with domain-based locale modules.
- Use canonical locale ids such as `en`, `zh-cn`, `ja`, `ko`, `de`, `es`.
- Add a central locale registry with labels, html `lang`, fallback locale, and route prefix.
- Lazy-load locale messages.
- Generate canonical and `hreflang` metadata for SEO pages.
- Update date/number formatting to use locale registry data.
- Make public content blocks locale-aware beyond `zh` and `en`.

Acceptance:

- Direct visits to locale-prefixed URLs render in the correct language.
- Manual language switching changes the URL and persists preference.
- Unknown locale prefixes redirect or normalize predictably.
- Existing E2E tests pass for at least `zh-cn` and `en`.

### Phase 3: Tool Registry v2

Goal: make tools data-driven instead of route-by-route and page-by-page.

Create one registry for:

- Tool id
- Slug per locale if needed
- Category
- Title and description keys
- Route component
- Processing mode: local, cloud, hybrid
- Access requirements: guest, login, Pro
- File types and limits
- SEO metadata
- Related tools
- Feature flag key
- Smoke test coverage tag

Benefits:

- Tools Center, Home, Features, route table, feature flags, SEO pages, and tests all read the same source of truth.
- Adding a tool becomes a controlled workflow instead of editing scattered files.
- Competitor-level tool expansion becomes safer.

Acceptance:

- Existing routes still work.
- Tool list and route metadata are generated from the registry.
- At least one new tool page can be added without touching unrelated navigation code.

### Phase 4: Dedicated Admin Frontend

Goal: make admin operations feel formal and isolate them from the public product.

Recommended timing:

- Start after Phase 1 and while Phase 2 is being designed.
- Do not wait until every external integration is complete.
- Do not split backend services yet.

Recommended structure:

```text
apps/web/       public app
apps/admin/     admin portal for the prepared admin domain
packages/ui/    shared UI primitives
packages/api/   shared API client/types if useful
backend/        existing FastAPI backend
```

Admin domain:

- Use the prepared admin domain for the admin frontend.
- Configure backend CORS to allow the public domain and admin domain explicitly.
- Keep `/api/v1/admin/*` protected by admin auth.
- Add stricter CSP and noindex headers for the admin app.

Admin refactor scope:

- Move Control Room into `apps/admin`.
- Split data fetching into composables or stores by domain:
  - overview
  - feature flags
  - settings/content
  - users
  - jobs
  - payments
  - feedback/errors
  - maintenance/audit
- Keep admin text Chinese-first if that matches operators, but do not mix admin copy into public i18n.

Acceptance:

- Public app no longer contains `/control-room`.
- Admin app builds separately.
- Admin domain can sign in and access `/api/v1/admin/*`.
- Public domain cannot accidentally surface admin UI.

### Phase 5: Production Integration Acceptance

Goal: prove real external integrations.

OAuth:

- Google and GitHub provider credentials exist in server `backend/.env`.
- Provider dashboards use:
  - `{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/google/callback`
  - `{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/github/callback`
- OAuth failures return friendly callback states.
- Account linking/unlinking UI remains optional.

Email:

- Configure real sender/domain.
- Verify password reset email delivery.
- Keep enumeration-safe reset responses.
- Confirm reset links use `FRONTEND_URL`.

Payments:

- Configure provider dashboards to call:
  - `{BACKEND_PUBLIC_URL}/api/v1/payment/webhooks/{provider}`
- Frontend return pages are not entitlement proof.
- Backend provider callbacks, amount/currency checks, and idempotent payment events are the trust boundary.

AI/OCR/Office:

- Configure provider keys.
- Run OCR and Office smoke tests on server.
- Keep large-file and failed-job diagnostics observable from admin.

Acceptance:

- Smoke evidence is recorded in this file after each integration passes.
- No integration is marked production-ready without credential, callback, and smoke evidence.

### Phase 6: Competitor-Level Feature Expansion

Only start after Phases 1-3 are stable.

Recommended order:

1. PDF to Word
2. PDF to Excel
3. PDF to PowerPoint
4. HTML/Webpage to PDF
5. Redact PDF
6. Compare PDFs
7. Translate PDF
8. PDF/A
9. Stronger e-sign workflow
10. Batch processing

Each new tool must include:

- Registry entry
- Public route
- Access model
- Locale keys
- Tool-page tests
- Backend tests if server-side
- Smoke path if cloud-based

## Operational Commands

Server update:

```bash
cd /root/data/docker_data/PDF/pdf-flow
git pull --ff-only v2 main
bash scripts/deploy-main.sh
```

Server status:

```bash
docker compose --env-file backend/.env -f docker-compose.yml ps
curl http://localhost:8000/health
cat .deploy_state/main/current_deployed_commit
```

Full smoke:

```bash
bash scripts/main-smoke-suite.sh
```

Rollback:

```bash
bash scripts/rollback-main.sh
```

Admin bootstrap:

```bash
PDF_FLOW_ADMIN_EMAIL=owner@example.com \
PDF_FLOW_ADMIN_PASSWORD='change-this-strong-password' \
PDF_FLOW_ADMIN_NAME='PDF-Flow Owner' \
bash scripts/init-admin.sh
```

Local verification:

```bash
npm run test:unit:ci
npm run type-check
npm run build
cd backend
pytest tests -q
```

Targeted backend checks:

```bash
cd backend
pytest tests/test_auth.py -q
pytest tests/test_admin.py -q
pytest tests/test_admin_bootstrap.py -q
pytest tests/test_files.py -q
pytest tests/test_payment_domain.py -q
```

## Cleanup Rules

- Do not commit `dist/`, `node_modules/`, `.tmp/`, `.env`, `.deploy_state/`, `.deploy_backups/`, or SSH credentials.
- Do not add new Markdown files unless the information cannot fit in `README.md` or this master document.
- Do not add new PDF tools until the Tool Registry v2 plan is started, unless the change is a small bug fix.
- Do not split backend services before the single-server deployment is stable with real provider callbacks.
- Keep Alembic migrations and tests even if they look old.
- Prefer focused, verified refactors over broad rewrites without tests.

## Next Recommended Work

1. Complete Phase 1 foundation cleanup.
2. Design and implement i18n v2 with locale-prefixed routes.
3. Build Tool Registry v2.
4. Split the admin frontend into a dedicated app for the prepared admin domain.
5. Run production acceptance for OAuth, email, payment callbacks, AI/OCR, and Office conversion.
6. Add competitor-gap tools only after the platform supports adding tools cleanly.
