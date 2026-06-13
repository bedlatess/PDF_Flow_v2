# PDF-Flow Project Master

Last updated: 2026-06-13

This is the internal source of truth for development direction, current progress, architecture decisions, known risks, and next work. Public-facing setup belongs in `README.md`.

## Current Status

- Official repository: `https://github.com/bedlatess/PDF_Flow_v2.git`
- Official remote name: `v2`
- Branch: `main`
- Last verified runtime commit: `77f939199a97634d48f1768bc5e297783942cedb`
- The server also records the active runtime commit at `.deploy_state/main/current_deployed_commit`.
- Server path: `/root/data/docker_data/PDF/pdf-flow`
- Deployment model: single repository, single Docker Compose server
- Runtime services: `frontend`, `backend`, `celery-worker`, `postgres`, `redis`
- Current production endpoints: public frontend `https://pdf.pawn.eu.org`, local public container port `5173`, temporary admin container port `5174`, backend API port `8000`
- Current stage: platform refactor batch deployed and smoke verified on the server; prepared admin domain routing is still pending

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

- Dedicated admin frontend entry for the Control Room
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
- Admin UI has a dedicated frontend entry under `src/admin` and reuses admin views/components from the main source tree while the project remains a single app repository.
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
- Verified server health after deploying Phase 1 foundation cleanup:
  - commit `96fa34dbe85b87107848295b5b900359dc67836a`
  - `backend` healthy
  - `celery-worker` healthy
  - `postgres` healthy
  - `redis` healthy
  - `/health` returns production healthy
  - frontend home returns HTTP 200
- Verified server health after deploying `c10f65d`:
  - `frontend` healthy
  - `backend` healthy
  - `celery-worker` healthy
  - `postgres` healthy
  - `redis` healthy
  - `/health` returns production healthy
  - frontend home returns HTTP 200
- Platform refactor push batch includes Phase 2 i18n v2, Phase 2b i18n SEO, Phase 3 Tool Registry v2, Phase 4 dedicated admin frontend, Phase 4b Control Room extraction, Phase 4c admin API extraction, Phase 4d public API extraction, and Phase 4e admin production-serving boundary. This batch passed `npm run type-check`, `npm run test:unit:ci`, `npm run build`, `npm run build:admin`, `npm run test:e2e:admin`, public shell E2E, locale SEO E2E, and targeted tool/availability Playwright checks locally.
- Verified server health after deploying `77f939199a97634d48f1768bc5e297783942cedb` on 2026-06-13:
  - `frontend` healthy
  - `backend` healthy
  - `celery-worker` healthy
  - `postgres` healthy
  - `redis` healthy
  - `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - public frontend `http://localhost:5173/` returns HTTP 200
  - admin frontend `http://localhost:5174/` returns HTTP 200 with noindex/security headers
  - public domain `https://pdf.pawn.eu.org/` returns HTTP 200
  - localized route `https://pdf.pawn.eu.org/en/tools/merge` returns HTTP 200

## Known Code Issues

Fix these before large feature work:

1. Repository metadata in `package.json` previously pointed to placeholder GitHub URLs. Keep it aligned with `PDF_Flow_v2`.
2. `src/locales/overrides.ts` is too large and acts as an uncontrolled patch layer over JSON locale files.
3. The dedicated admin frontend now has Docker/Nginx/backend CORS wiring and temporary server access on port `5174`, but the prepared real admin domain still needs DNS, TLS, server environment values, and smoke evidence.
4. Admin UI now has a separate frontend entry, but it still lives in the same repository tree until a future monorepo split is justified.
5. Locale-prefixed routes, browser-language preference, and basic SEO `hreflang` output exist for the current supported locales, but additional locale rollout and deeper locale-file cleanup still need completion.
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

Current local progress:

- Added a locale registry for supported locale ids, route prefixes, html `lang`, aliases, and content-block fallback mapping.
- Added locale-prefixed public routes for `/zh-cn`, `/en`, and `/es`.
- Legacy unprefixed paths now normalize to the preferred locale prefix.
- Header language switching keeps the current page and swaps the URL prefix.
- Core public navigation, pricing/payment redirects, feature access redirects, and account/payment status pages now preserve the active locale prefix.
- Rebuilt clean baseline locale JSON files with stable tool title/description keys so route titles do not expose raw i18n keys.
- Added unit coverage for locale normalization and path rewriting.
- Cleaned the locale registry labels and added per-locale `hreflang` metadata.
- Added route-driven `document.title`, meta description, Open Graph basics, canonical URL, alternate `hreflang`, and `x-default` output.
- Tool detail routes now carry registry `descriptionKey` metadata so tool pages can generate useful descriptions.
- Added unit coverage for browser language resolution and SEO head-link generation.

Still to finish in this phase:

- Decide when to expose additional locales such as `ja`, `ko`, and `de`; do not expose them until baseline translations exist.
- Split the large `src/locales/overrides.ts` patch layer into domain locale modules with an encoding-safe migration script. A naive text split exposed historical mojibake/unterminated-string risk, so this must be handled as its own cleanup step.
- Update Playwright route fixtures to assert locale-prefixed canonical paths directly.

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

Current local progress:

- Expanded `src/data/pdfTools.ts` from a display list into the tool registry source of truth.
- Each tool now records id, slug, route name, title and description keys, route component loader, category, processing mode, access model, feature flag key, Pro hint, icon, accent, featured flag, and smoke-test tag.
- Tool detail routes are generated from the registry via `toolRoutes`; existing public paths and route names are preserved.
- Removed the 23 hand-written tool detail route records from `src/router/index.ts`.
- Removed duplicate feature availability enforcement from `ToolPageShell`; route-level feature availability is handled by the global router guard.
- Footer recommended tools now read from the registry instead of duplicating labels, paths, and feature keys.
- Added `tests/unit/pdf-tools-registry.test.ts` to lock uniqueness, metadata validity, route generation, lookup helpers, and footer tool references.
- Updated availability E2E expectations for locale-prefixed canonical not-found paths.

Registry now covers:

- Tool id
- Slug
- Route name
- Category
- Title and description keys
- Route component
- Processing mode: local, cloud, ai
- Access requirements: guest, login, Pro
- Feature flag key
- Smoke test coverage tag

Still to finish in this phase:

- Add accepted file types, output types, size/page limits, and batch support metadata.
- Add SEO title/description keys and canonical/hreflang metadata once Phase 2 SEO work starts.
- Add related-tool metadata for tool detail pages.
- Move E2E tool-page matrix cases to read from a shared registry fixture or generated test data.
- Add admin feature flag seeding/validation against the same registry.

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

Current local progress:

- Added `admin.html` as a separate admin entry document with noindex metadata and admin-specific mount point.
- Added `src/admin/main.ts`, `src/admin/router.ts`, `src/admin/AdminApp.vue`, and `src/admin/AdminAccessState.vue`.
- The admin app runs at its own root route and reuses the existing `ControlRoom.vue` while keeping the build boundary separate.
- Public app routing no longer includes `/control-room`.
- Public `App.vue` no longer has control-room-specific maintenance or feedback-widget exceptions.
- Added `vite.admin.config.ts` with `dist-admin` output so public and admin builds do not overwrite each other.
- Added `dev:admin`, `build:admin`, `preview:admin`, and `test:e2e:admin` scripts.
- Added `playwright.admin.config.ts`; admin E2E now runs against the admin entry instead of the public app.
- Added `tests/unit/admin-router-boundary.test.ts` to lock that the admin app is rooted separately and does not expose `/control-room`.
- Added `src/admin/control-room/types.ts`, `tabs.ts`, `formatters.ts`, `summaries.ts`, `context.ts`, `clipboard.ts`, `actions.ts`, `actions-meta.ts`, `actions-settings.ts`, `actions-users.ts`, `actions-jobs.ts`, `actions-payments.ts`, `actions-feedback.ts`, `actions-maintenance.ts`, `actions-diagnostics.ts`, and `useControlRoom.ts`.
- Reduced `src/views/admin/ControlRoom.vue` to a page composition layer that imports tab metadata, admin tab components, and the Control Room composable.
- Reduced `src/admin/control-room/useControlRoom.ts` to a composition facade over state, clipboard helpers, formatting utilities, and admin actions.
- Reduced `src/admin/control-room/actions.ts` to a domain action aggregator; user, job, payment, feedback, maintenance, diagnostics, settings/content, and meta loading actions now live in separate files.
- Added `src/admin/api/types.ts`, `src/admin/api/client.ts`, and `src/admin/api/index.ts` as the admin-facing API module.
- Moved the shared Axios instance and token refresh interceptors to `src/services/http.ts`.
- Updated admin components, Control Room modules, and admin utility tests to import admin types/client from `@/admin/api`.
- Kept `adminAPI` and admin type compatibility exports in `src/services/api.ts` so older imports continue to work while the admin app migrates.
- Split public API clients by domain under `src/services/api/*`.
- Reduced `src/services/api.ts` to a compatibility aggregation module that re-exports public APIs, admin compatibility exports, and the default shared `apiClient`.
- Updated `Dockerfile.frontend` to build both public `dist/` and admin `dist-admin/` artifacts into the production Nginx image.
- Updated `nginx.conf` to serve the public app and admin app from separate roots, route by `PUBLIC_FRONTEND_HOST` and `ADMIN_FRONTEND_HOST`, expose the admin app on local port `5174`, and add admin noindex/security headers.
- Added backend `ADMIN_FRONTEND_URL` configuration and `CORS_ALLOWED_ORIGINS` so the public and admin HTTPS origins are both trusted without duplicating them manually in every environment.
- Updated root and backend Compose files plus `backend/.env.example` for local admin URL defaults.
- Added backend config tests for the public/admin CORS merge behavior.
- Restored key admin success and confirmation copy as clean UTF-8 Chinese while leaving unrelated historical admin template copy for a later text cleanup pass.
- Added `tests/unit/admin-control-room-utils.test.ts` for admin formatting, summary, and tab utility coverage.

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
- Production environment should set:
  - `PUBLIC_FRONTEND_HOST` to the public frontend host.
  - `ADMIN_FRONTEND_HOST` to the prepared admin frontend host.
  - `FRONTEND_URL` to the public HTTPS origin.
  - `ADMIN_FRONTEND_URL` to the admin HTTPS origin.

Admin refactor scope:

- Move Control Room into `apps/admin` when the repository is ready for a monorepo layout. The current local step is an entrypoint/build split inside the existing tree.
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

Still to finish in this phase:

- Move admin API clients/types into an admin-facing module or shared package before a full monorepo split.
- Push/deploy the local serving boundary and set the real prepared admin domain environment values on the server.
- Verify real DNS/TLS routing so the public domain never serves the admin artifact and the admin domain can reach `/api/v1/admin/*`.
- Decide whether the future monorepo split is worth doing after production admin usage is stable.

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

1. Configure the prepared admin domain with DNS, TLS, `ADMIN_FRONTEND_URL`, and `ADMIN_FRONTEND_HOST`.
2. Run production acceptance for OAuth, email, payment callbacks, AI/OCR, and Office conversion.
3. Split `src/locales/overrides.ts` with an encoding-safe migration script and add missing baseline translations before exposing more locales.
4. Add competitor-gap tools only after the platform refactor remains stable under production traffic.
5. Decide whether to split the admin frontend into its own repository after the dedicated admin domain is live and daily operation is stable.
