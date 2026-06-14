# PDF-Flow Project Master

Last updated: 2026-06-14

This is the internal source of truth for development direction, current progress, architecture decisions, known risks, and next work. Public-facing setup belongs in `README.md`.

## Current Status

- Official repository: `https://github.com/bedlatess/PDF_Flow_v2.git`
- Official remote name: `v2`
- Branch: `main`
- Last verified runtime commit: `0bc64a96d9a45f75fbf4d49dc4e544b5fbec7a68`
- The server also records the active runtime commit at `.deploy_state/main/current_deployed_commit`.
- Server path: `/root/data/docker_data/PDF/pdf-flow`
- Deployment model: single repository, single Docker Compose server
- Runtime services: `frontend`, `backend`, `celery-worker`, `postgres`, `redis`
- Current production endpoints: public frontend `https://pdf.pawn.eu.org`, admin frontend `https://admin.pawn.eu.org`, local public container port `5173`, local admin container port `5174`, backend API port `8000`
- Current stage: platform refactor batch deployed and smoke verified on the server; dedicated admin domain routing is live

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
- Manual user entitlement grants and expiration management
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
- Added and verified the read-only production acceptance workflow on the server:
  - repository head `43f1835`
  - running runtime image still records `77f939199a97634d48f1768bc5e297783942cedb`
  - `https://pdf.pawn.eu.org/` returns the public app shell
  - `https://pdf.pawn.eu.org/en/tools/merge` returns the public app shell
  - `https://pdf.pawn.eu.org/health` returns healthy
  - `https://pdf.pawn.eu.org/api/v1/admin/public-config` returns public config
  - temporary admin URL `http://155.248.195.94:5174/` returns the admin app shell and noindex header
  - no write probe or protected admin API probe was run because production admin credentials were not supplied to the acceptance script
- Configured and verified the dedicated admin domain on 2026-06-13:
  - Cloudflare DNS `admin.pawn.eu.org` resolves to `155.248.195.94`
  - Nginx Proxy Manager proxy host id `25` forwards `admin.pawn.eu.org` to `155.248.195.94:5174`
  - Nginx Proxy Manager reuses certificate id `1`, the existing `*.pawn.eu.org` Let's Encrypt certificate
  - server `.deploy.env` sets `PUBLIC_FRONTEND_HOST=pdf.pawn.eu.org` and `ADMIN_FRONTEND_HOST=admin.pawn.eu.org`
  - server `backend/.env` sets `ADMIN_FRONTEND_URL=https://admin.pawn.eu.org` and includes the admin origin in CORS and allowed hosts
  - deployment `1db2646e714d22723845da06c7d044669f23973f` completed successfully at `2026-06-13 20:04:56`
  - `https://admin.pawn.eu.org/` returns HTTP 200 with the admin app shell and noindex/security headers
  - `https://admin.pawn.eu.org/api/v1/admin/public-config` returns HTTP 200
  - CORS preflight from `https://admin.pawn.eu.org` is allowed for both `https://pdf.pawn.eu.org/api/` and `https://admin.pawn.eu.org/api/`
  - read-only production acceptance passed with `PUBLIC_URL=https://pdf.pawn.eu.org` and `ADMIN_URL=https://admin.pawn.eu.org`
- Created the first production admin account from the trusted server shell on 2026-06-13:
  - admin user id `8`, email `admin@pawn.eu.org`, role `admin`, active and verified
  - bootstrap audit log recorded `bootstrap_admin`
- Verified protected production admin acceptance on 2026-06-13:
  - ran `PUBLIC_URL=https://pdf.pawn.eu.org ADMIN_URL=https://admin.pawn.eu.org RUN_WRITE_PROBE=1 LIVE_ADMIN_EMAIL=admin@pawn.eu.org bash scripts/production-acceptance.sh`
  - public homepage, localized tool route, backend health, public config, admin frontend, and admin access route passed
  - admin login passed
  - protected admin health report passed and returned migration/service data
  - write probe submitted a live feedback report and admin cleanup closed it successfully
  - cleanup audit log recorded `cleanup` for `live_acceptance`
- Ran production integration smoke checks on 2026-06-13:
  - `bash scripts/main-smoke-suite.sh` passed on the server against `http://localhost:8000`
  - health and API docs passed
  - business PDF merge smoke passed with generated test user `smoke-prod-20260613202001@example.com`
  - OCR smoke passed with generated Pro test user `ocr-prod-20260613202001@example.com`; result text contained `OCR SMOKE 123`
  - Office to PDF smoke passed with generated test user `office-prod-20260613202001@example.com`; downloaded result was a valid PDF
  - backend container has Tesseract `5.5.0` and LibreOffice `25.2.3.2`
  - GitHub OAuth is configured and starts the provider flow with HTTP 302 to GitHub
  - Google OAuth remains unconfigured and returns HTTP 503
  - password reset request returns the enumeration-safe HTTP 200 response, but `RESEND_API_KEY` is not configured so real email delivery is not accepted yet
  - `GEMINI_API_KEY` is not configured, so AI PDF analysis is not production-accepted yet
  - payment provider credentials are not configured; `PAYMENT_ENABLED_PROVIDERS` was hotfixed on the server to `[]` so public checkout providers are disabled until real merchant credentials are added
  - Stripe checkout creation now returns HTTP 503 `Stripe payment is not enabled` instead of exposing a broken half-configured checkout path
  - post-hotfix production acceptance passed for public/admin read-only checks
- Fixed payment provider default safety after the production hotfix:
  - backend `Settings` now defaults `PAYMENT_ENABLED_PROVIDERS` to `[]`
  - root and backend Docker Compose files now default `PAYMENT_ENABLED_PROVIDERS` to `[]`
  - payment provider registry order is preserved, but no provider is enabled until explicitly configured
  - default Stripe checkout now returns HTTP 503 instead of starting a half-configured payment flow
  - verified with `pytest backend/tests/test_config.py backend/tests/test_payment_domain.py -q`
  - verified with `pytest backend/tests/test_admin_payment_domain.py -q`
  - verified with `pytest backend/tests/test_admin.py::test_admin_payment_operations_returns_provider_health_and_reconciliation backend/tests/test_admin.py::test_admin_payment_operations_requires_admin -q`
- Implemented OAuth provider visibility control:
  - `/api/v1/admin/public-config` now exposes configured OAuth provider status without exposing secrets
  - login UI hides the entire OAuth section when no providers are configured
  - Google remains hidden unless both Google OAuth values are configured
  - GitHub will be shown after its production client id and secret are present
  - verified with `pytest backend/tests/test_admin.py::test_public_config_exposes_feature_flags backend/tests/test_admin.py::test_public_config_marks_only_configured_oauth_providers -q`
  - verified with `npm run type-check`
- Deployed and verified GitHub OAuth on production:
  - deployment `7d975725d939b4b8e5e093def9441c28bf08c2e7` completed successfully at `2026-06-13 21:24:23`
  - production health returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - `https://pdf.pawn.eu.org/api/v1/admin/public-config` reports Google disabled and GitHub enabled
  - `https://pdf.pawn.eu.org/api/v1/auth/oauth/github` returns HTTP 302 to GitHub with callback `https://pdf.pawn.eu.org/api/v1/auth/oauth/github/callback`
  - `https://pdf.pawn.eu.org/api/v1/auth/oauth/google` returns HTTP 503
  - OAuth session state is now backed by `SessionMiddleware`
- Fixed admin access login flow on production:
  - deployment `e7bb5cb848aa78dd9badac804471948d93326a5f` completed successfully at `2026-06-13 21:55:06`
  - admin access state now renders its own administrator login form instead of linking to a public-app route on the admin domain
  - the access state includes a real return link to the public homepage
  - production admin password for `admin@pawn.eu.org` was rotated with `scripts/init-admin.sh`
  - `https://admin.pawn.eu.org/api/v1/auth/login` returns bearer and refresh tokens for the rotated admin credentials
- Added no-SMTP account recovery support:
  - admins can generate a copyable, one-time password reset link from the Control Room user list
  - generated links store only a token hash in `password_reset_tokens` and do not store or expose temporary plaintext passwords
  - successful reset marks the token used so the same link cannot reset the account again
  - reset-link generation is admin-only, blocked for inactive users, and recorded in admin audit logs without storing the token
  - verified with `pytest backend/tests/test_admin.py::test_admin_can_create_user_password_reset_link backend/tests/test_admin.py::test_admin_password_reset_link_requires_admin_and_active_user backend/tests/test_auth_domain.py::test_auth_domain_password_reset_and_inactive_user_guards -q`
  - verified with `npm run type-check`
- Deployed and verified no-SMTP account recovery on production:
  - deployment `985efb3bb82065baf395c0af626bd661aa61dce3` completed successfully at `2026-06-13 22:14:48`
  - live admin generated a reset link for test user `reset-smoke-20260613221610@example.com`
  - generated link pointed to `https://pdf.pawn.eu.org/zh-cn/auth/reset-password`
  - reset token successfully changed the test user's password and subsequent login returned bearer tokens
  - latest audit log recorded `target_type=password_reset_link`
  - test user cleanup deleted the generated account
- Upgraded password reset links to true one-time tokens:
  - migration `add_password_reset_tokens` creates `password_reset_tokens`
  - reset links now store only SHA-256 token hashes, source, creator, expiry, and `used_at`
  - admin-generated and user-requested reset links are marked used after successful password reset
  - legacy JWT reset tokens remain accepted for backward compatibility
  - verified with `pytest backend/tests/test_admin.py::test_admin_can_create_user_password_reset_link backend/tests/test_admin.py::test_admin_password_reset_link_requires_admin_and_active_user backend/tests/test_auth_domain.py::test_auth_domain_password_reset_and_inactive_user_guards -q`
  - verified with `npm run type-check`
- Deployed and verified one-time reset links on production:
  - deployment `426a890919265af00ce972a90a2df764b53756b5` completed successfully at `2026-06-13 22:45:29`
  - migration ran `add_payment_events -> add_password_reset_tokens`
  - live reset link for `reset-onetime-20260613224612@example.com` returned HTTP 200 on first use and HTTP 400 on second use
  - login after reset returned bearer tokens
  - production `password_reset_tokens` table has a used-token record
  - test user cleanup deleted the generated account
- Implemented manual admin entitlement grants:
  - Control Room user management can set subscription status and end date
  - admins can quickly grant Pro for 30 or 365 days or mark a subscription expired
  - admin user API now returns and updates `subscription_id`, `subscription_status`, and `subscription_end_date`
  - Pro/Enterprise access now respects active/manual/trialing/cancel-at-period-end status and future expiry; expired or canceled users are treated as Free
  - backend feature gates, AI endpoints, advanced PDF endpoints, upload tiering, and usage stats now share the same entitlement rules
  - current user API returns subscription status and end date so the frontend can hide paid cloud features after expiry
  - verified with `pytest backend/tests/test_entitlements.py backend/tests/test_account_domain.py backend/tests/test_admin_users_domain.py backend/tests/test_admin.py -q`
  - verified with `npm run type-check`
  - verified with `npm run build`
- Deployed and verified manual admin entitlement grants on production:
  - deployment `fb34c4ff208f912fdde9d5ab7a3b533b2adf4914` completed successfully at `2026-06-13 23:09:01`
  - deploy script rebuilt public/admin frontend and backend images, ran migrations, and passed health/API-doc smoke checks
  - production runtime records `.deploy_state/main/current_deployed_commit=fb34c4ff208f912fdde9d5ab7a3b533b2adf4914`
  - all Compose services are healthy: `frontend`, `backend`, `celery-worker`, `postgres`, and `redis`
  - live entitlement smoke registered `manual-entitlement-*`, patched it through the admin API to `role=pro`, `subscription_status=manual`, and a future `subscription_end_date`
  - the test user login returned bearer tokens; `/api/v1/auth/me` returned `role=pro` and `subscription_status=manual`
  - `/api/v1/users/me/stats` returned `role=pro` and `quota_limit=-1`
  - the temporary test user was deleted after verification
- Added account and admin entitlement visibility:
  - shared frontend entitlement summary helper now labels Free, Pro, Enterprise, Admin, active/manual/trial/canceling, expired, and canceled states consistently
  - Profile page shows the user's plan, subscription status, and access expiry/expiration summary
  - admin user management shows an entitlement pill and expiry summary above the manual entitlement controls
  - verified with `npm run type-check`
  - verified with `npm run test:unit:ci -- tests/unit/entitlements.test.ts`
  - verified with `npm run build`
  - verified with `npm run build:admin`
- Deployed and verified account/admin entitlement visibility on production:
  - deployment `bad5145bde1d8af23f00862263dd1f74cd0b32f6` completed successfully at `2026-06-14 06:37:32`
  - deploy script rebuilt public/admin frontend artifacts and backend images, ran migrations, and passed health/API-doc smoke checks
  - production runtime records `.deploy_state/main/current_deployed_commit=bad5145bde1d8af23f00862263dd1f74cd0b32f6`
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - `https://pdf.pawn.eu.org/zh-cn/profile` returns HTTP 200
  - `https://admin.pawn.eu.org/` returns HTTP 200
  - all Compose services are healthy: `frontend`, `backend`, `celery-worker`, `postgres`, and `redis`
- Fixed pricing page entitlement consistency:
  - pricing current-plan detection now uses the same frontend entitlement summary as Profile and admin user management
  - expired or canceled Pro/Enterprise accounts are treated as Free on pricing, so users can see the upgrade CTA again
  - verified with `npm run type-check`
  - verified with `npm run test:unit:ci -- tests/unit/entitlements.test.ts`
  - verified with `npm run build`
- Deployed and verified pricing entitlement consistency on production:
  - deployment `1ead8b0262ab643fb1b01a73131dc6e63ffcddb0` completed successfully at `2026-06-14 06:43:04`
  - deploy script rebuilt public/admin frontend artifacts and backend images, ran migrations, and passed health/API-doc smoke checks
  - production runtime records `.deploy_state/main/current_deployed_commit=1ead8b0262ab643fb1b01a73131dc6e63ffcddb0`
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - `https://pdf.pawn.eu.org/zh-cn/pricing` returns HTTP 200
  - `https://admin.pawn.eu.org/` returns HTTP 200
- Deployed Admin v2 Phase 1 information architecture:
  - commit `9a56be4fc21aa739db935df74f32a56a394b8511`
  - rebuilt the admin shell around a formal operations console with top health/revenue/support indicators
  - grouped navigation into Overview, Users and Revenue, Product Configuration, Operations Support, and Security domains
  - split payment setup from payment reconciliation so merchant readiness, required server config, webhook URLs, return URLs, blockers, sandbox runbooks, and go-live checklists have a dedicated `Payment Setup` module
  - simplified `Payment Reconciliation` into orders, events, reconciliation summary, and evidence packet review
  - verified with `npm run type-check`
  - verified with `npm run test:unit:ci -- tests/unit/admin-control-room-utils.test.ts`
  - verified with `npm run build`
  - verified with `npm run build:admin`
  - verified with `npm run test:e2e:admin`
  - browser-verified local admin mock at desktop `1440x1100` and mobile `390x900`: overview, payment setup, and payment reconciliation rendered without document-level horizontal overflow and without browser console errors
  - server `.deploy_state/main/current_deployed_commit` records `9a56be4fc21aa739db935df74f32a56a394b8511`
  - production containers `backend`, `celery-worker`, and `frontend` are healthy after deploy
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - `https://pdf.pawn.eu.org/` returns HTTP 200
  - `https://admin.pawn.eu.org/` returns HTTP 200 with title `PDF-Flow Admin`
  - `https://admin.pawn.eu.org/assets/ControlRoom-DVPqbD5G.js` returns HTTP 200
  - Playwright production unauthenticated admin smoke returned HTTP 200, title `PDF-Flow Admin`, no document-level horizontal overflow at `1440x1000`, and no console/page errors
- Deployed locale override copy migration into baseline locale JSON files:
  - commit `0bc64a96d9a45f75fbf4d49dc4e544b5fbec7a68`
  - `src/locales/en.json`, `src/locales/zh.json`, and `src/locales/es.json` now contain the public copy that previously lived in `src/locales/overrides.ts`
  - filled the missing Chinese `home.toolsTitle` baseline so the homepage no longer exposes the raw `home.toolsTitle` key
  - `src/locales/overrides.ts` is reduced to the compatibility merge helper plus empty per-locale override objects
  - added `scripts/migrate-locale-overrides.mjs` for encoding-safe legacy override migration and post-migration JSON validation
  - added unit coverage in `tests/unit/locale-overrides.test.ts`
  - verified migration parity by comparing pre-migration merged messages from Git against post-migration JSON for `en`, `zh`, and `es`
  - verified with `node scripts/migrate-locale-overrides.mjs`
  - verified with `npm run test:unit:ci -- tests/unit/locale-overrides.test.ts tests/unit/locale-registry.test.ts`
  - verified with `npm run type-check`
  - verified with `npm run test:unit:ci`
  - verified with `npm run build`
  - verified with `npm run build:admin`
  - verified with Playwright locale/public checks: `locale-seo`, `public-shell`, and `public-marketing`
  - verified with `npm run test:e2e:admin`
  - server `.deploy_state/main/current_deployed_commit` records `0bc64a96d9a45f75fbf4d49dc4e544b5fbec7a68`
  - production containers `backend`, `celery-worker`, and `frontend` are healthy after deploy
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - `https://pdf.pawn.eu.org/zh-cn/`, `/en/tools/merge`, and `/es/tools/merge` return HTTP 200
  - `https://admin.pawn.eu.org/` returns HTTP 200 and the active admin bundle returns HTTP 200
  - Playwright production render smoke for `zh`, `en`, `es`, and `admin` returned HTTP 200, no console/page errors, no document-level horizontal overflow at `1366x900`, and no raw `home.toolsTitle`/`home.tools` key exposure
- Added locale rollout guardrails locally:
  - added shared locale fixtures for route metadata and baseline message files
  - `tests/unit/locale-overrides.test.ts` now verifies every supported locale has a message file and recursively covers all English baseline keys
  - filled missing `zh` and `es` baseline keys found by the recursive check
  - `tests/unit/locale-registry.test.ts` now derives route pattern expectations from the shared locale fixture instead of hard-coding `zh-cn|en|es`
  - `tests/e2e-playwright/locale-seo.spec.ts` now derives canonical `hreflang` assertions from the locale registry and verifies localized Merge PDF titles for `zh`, `en`, and `es`
  - verified with `npm run test:unit:ci -- tests/unit/locale-overrides.test.ts tests/unit/locale-registry.test.ts`
  - verified with `npm run type-check`
  - verified with `npm run test:unit:ci`
  - verified with `npm run build`
  - verified with `npm run build:admin`
  - verified with Playwright locale/public checks: `locale-seo`, `public-shell`, and `public-marketing`
  - verified with `npm run test:e2e:admin`
- Ran final production browser acceptance for deployed commit `e8a9d8d9b1d24b71d7a3a93c7ac6661c3bed7cae` on 2026-06-14:
  - server project path verified as `/root/data/docker_data/PDF/pdf-flow`
  - remote `main` HEAD and `.deploy_state/main/current_deployed_commit` both record `e8a9d8d9b1d24b71d7a3a93c7ac6661c3bed7cae`
  - production Compose services `frontend`, `backend`, `celery-worker`, `postgres`, and `redis` are healthy
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - rotated the production `admin@pawn.eu.org` password from the trusted server shell; the password is intentionally not stored in repository documentation
  - Playwright Chromium production acceptance passed for `https://pdf.pawn.eu.org/zh-cn/`, `/zh-cn/tools/merge`, `/en/tools/merge`, `/es/tools/merge`, and `/zh-cn/pricing`
  - authenticated Playwright Chromium acceptance passed for `https://admin.pawn.eu.org/` after login and covered Overview, Users, Payment Setup, Payment Reconciliation, and Maintenance modules
  - verified no browser page errors, no relevant console errors, no document-level horizontal overflow at `1366x900`, and no raw `home.toolsTitle` / `home.tools` / `admin.` / `controlRoom.` key exposure
- Added local server access guardrails:
  - `.gitignore` now ignores real files under `ssh/` while allowing the non-secret `ssh/ssh.example.md` template to be tracked
  - added `ssh/ssh.example.md` with the expected `HOST`, `PORT`, `USER`, `PASSWORD`, and `PROJECT_DIR` fields
  - README deployment notes now state that real server access values belong in local-only `ssh/ssh.md` and must stay out of commits
- Added administrator self-service password rotation locally:
  - backend `POST /api/v1/auth/change-password` requires an authenticated user, verifies the current password, rejects current-password reuse, and requires letters plus numbers
  - admin frontend now has an `Account Security` tab under the Security group with current-password, new-password, and confirmation fields
  - successful password rotation clears local browser tokens and returns the operator to the admin login page with a password-changed notice
  - verified with `pytest backend/tests/test_auth.py backend/tests/test_auth_domain.py -q`
  - verified with `npm run type-check`, `npm run test:unit:ci`, `npm run build`, `npm run build:admin`, and `npm run test:e2e:admin`
- Deployed and verified administrator self-service password rotation on production:
  - commit `340d9099e141c3946c19997b1e444fb5c5903993`
  - server `.deploy_state/main/current_deployed_commit` records `340d9099e141c3946c19997b1e444fb5c5903993`
  - production Compose services `frontend`, `backend`, `celery-worker`, `postgres`, and `redis` are healthy
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - production `POST /api/v1/auth/change-password` was smoke-tested by rotating the admin password to a temporary value and then restoring the known admin password
  - verified the known admin password still logs in and the temporary password is rejected with HTTP 401
  - authenticated Playwright Chromium production check reached `https://admin.pawn.eu.org/`, opened `Account Security`, and found no browser page errors, no relevant console errors, no document-level horizontal overflow at `1366x900`, and no raw i18n key exposure
- Hardened account profile updates locally:
  - removed the legacy password mutation path from `PATCH /api/v1/users/me`
  - profile updates now only apply supported profile fields; password rotation must go through `/api/v1/auth/change-password` or the reset-token flow
  - verified with `pytest backend/tests/test_account_domain.py backend/tests/test_auth.py -q`
  - verified with `npm run type-check`, `npm run build`, and `npm run test:e2e:admin`
- Deployed and verified account password-mutation hardening on production:
  - commit `77d7d8d8e4551fb3e3118a0bf16df20d89f73e69`
  - server `.deploy_state/main/current_deployed_commit` records `77d7d8d8e4551fb3e3118a0bf16df20d89f73e69`
  - production Compose services are healthy after deploy
  - production `/health` returns `{"status":"healthy","version":"2.0.0","environment":"production"}`
  - production `PATCH /api/v1/users/me` with a `password` field returns success for the profile update path but does not change the password
  - verified the known admin password still logs in and the attempted profile-patch password is rejected with HTTP 401
- Implemented Payment Configuration Center Phase 1 locally:
  - added `payment_provider_configs` with encrypted secret storage and admin-safe responses
  - added `PAYMENT_CONFIG_ENCRYPTION_KEY` as the environment-only master key for database-stored payment secrets
  - added admin endpoints for listing, saving, and locally validating managed payment provider configs
  - added `gmpay` as a standalone provider, separate from EPUSDT and other hosted gateways
  - `PaymentService` now prefers enabled, complete database config for GM Pay and falls back to existing environment-driven providers for all legacy providers
  - GM Pay checkout creates a `PaymentOrder`, calls the GM Pay create-transaction endpoint, and returns `payment_url`
  - GM Pay webhook endpoint exists and records accepted callbacks, but it does not mark orders paid or grant Pro until a real webhook sample, signature verification, amount/currency checks, and idempotency checks are completed
  - admin Payment Setup now has a GM Pay configuration form with write-only secret handling, local validation, webhook status, and clearer readiness layout
  - Pricing can expose GM Pay when the backend reports it enabled and configured
  - verified with `pytest backend/tests/test_payment_config_gmpay.py backend/tests/test_payment_domain.py backend/tests/test_admin_payment_domain.py -q`
  - verified with `npm run type-check`
- Completed local GM Pay Phase 1 acceptance on 2026-06-14:
  - local backend used an isolated SQLite database under `.tmp/`, with `PAYMENT_CONFIG_ENCRYPTION_KEY` provided only as a process environment variable
  - admin Payment Setup opened the GM Pay configuration center
  - GM Pay config save, modify, and validate paths passed
  - secret responses showed configured status and tail only; plaintext `secret_key` was not returned
  - saving with an empty secret payload preserved the previously encrypted secret
  - database and admin audit log checks did not contain plaintext payment secrets
  - Pricing exposed GM Pay as the only enabled provider when only GM Pay was configured
  - frontend checkout created a GM Pay `PaymentOrder`, received `payment_url`, and opened the local GM Pay cashier
  - mobile admin layout at 390px had no horizontal document overflow
  - webhook endpoint returned accepted status but left orders pending and did not grant Pro
  - checkout copy now says Pro access is handled only after server-side payment confirmation, not by the frontend page
  - verified with `pytest backend/tests -q`, `npm run type-check`, `npm run test:unit:ci`, `npm run build`, `npm run build:admin`, and `npm run test:e2e:admin`
  - additional targeted checks after the checkout-copy correction: `npm run test:unit:ci -- tests/unit/locale-overrides.test.ts tests/unit/locale-registry.test.ts`, `npm run build`, and `npm run build:admin`
- Deployed Payment Configuration Center Phase 1 to production on 2026-06-14:
  - pushed `main` to remote `v2/main`
  - production `backend/.env` now has `PAYMENT_CONFIG_ENCRYPTION_KEY` set as an environment-only secret; the value was not written to docs, Git, database, or admin UI
  - deployment `2d23339bcff241ce503552ffcc2b59a1b1bd79f2` completed successfully with `bash scripts/deploy-main.sh`
  - migration ran `add_password_reset_tokens -> add_payment_provider_configs`
  - production `.deploy_state/main/current_deployed_commit` records `2d23339`
  - production `/health` returns healthy
  - production Compose services are healthy: `frontend`, `backend`, `celery-worker`, `postgres`, and `redis`
  - Phase 1 smoke used a temporary GM Pay cashier container inside the Docker network and temporary smoke users
  - smoke saved and validated GM Pay config, with secret response showing only configured state and tail `1234`; plaintext smoke secret was not returned
  - `/api/v1/payment/providers` reported GM Pay enabled while smoke config was enabled
  - checkout created a GM Pay order and returned a cashier URL from the temporary GM Pay service
  - backend could open the returned cashier URL with HTTP 200
  - GM Pay webhook endpoint returned HTTP 202 and left the smoke order pending, event ignored/accepted, buyer role free, and buyer subscription unset
  - after smoke, GM Pay was disabled again so public Pricing does not show the temporary provider
  - temporary smoke container and temporary smoke users were removed
  - final production check: `gmpay_enabled=False`, `db_gmpay_enabled=False`, `alembic_version=add_payment_provider_configs`
- Tested real GM Pay merchant config save path on production on 2026-06-14:
  - official GM Pay `api_base_url`, merchant id, currency, token, and network were saved through the admin config API
  - official GM Pay secret was accepted as write-only input and stored encrypted; plaintext was not returned by the API and was not present in `encrypted_secret_json`
  - GM Pay was enabled only briefly during smoke and was disabled again immediately afterward
  - public provider list reported GM Pay enabled while smoke config was enabled, then disabled after cleanup
  - real GM Pay order creation did not pass yet: the gateway returned signature verification failure for the current create-transaction signing contract
  - direct connectivity to `https://pay.pawn.eu.org/payments/gmpay/v1/order/create-transaction` from the backend container works, so the remaining blocker is the exact GM Pay request signature/field contract, not network reachability
  - no real payment was made and no Pro entitlement was granted
  - temporary real-config smoke users were removed
  - production is left safe: `gmpay_enabled=False`, `db_gmpay_enabled=False`, encrypted real GM Pay config retained for later retry
  - next required input before payment sampling: official GM Pay create-transaction signature documentation or a provider-side example of a successful signed request
- Fixed and deployed real GM Pay create-transaction signing on 2026-06-14:
  - direct gateway probe confirmed the real endpoint rejects JSON with `10009 failed to parse request params`
  - direct gateway probe confirmed `application/x-www-form-urlencoded` succeeds when signature is MD5 over all non-empty fields except `signature`, sorted by ASCII key, with the secret appended directly
  - updated the GM Pay adapter to use the real signing contract and form-urlencoded create-transaction requests
  - verified locally with `pytest backend/tests/test_payment_config_gmpay.py backend/tests/test_payment_domain.py -q` and `npm run type-check`
  - deployed commit `957ebf3909ce630211ba39588ab7df21b1e2d143` successfully with `bash scripts/deploy-main.sh`
  - production business API smoke saved official GM Pay config, enabled GM Pay briefly, created a real GM Pay order, and received a real cashier URL from `https://pay.pawn.eu.org/pay/checkout-counter/...`
  - after smoke, GM Pay was disabled again; final checks show `gmpay_enabled=False`, `db_gmpay_enabled=False`, no temporary adapter smoke users, and production `/health` healthy
  - no real payment was made and webhook-based Pro activation remains disabled until a paid callback sample is captured and verified
- Closed the GM Pay order-creation phase on 2026-06-14:
  - current stage is now `order creation link complete; waiting for real payment webhook verification`
  - final create-transaction request format is `application/x-www-form-urlencoded`
  - final signature rule is: include every non-empty request field except `signature`, sort by ASCII key, join as `key=value` with `&`, append the GM Pay secret directly, then MD5 lowercase
  - verified scope: encrypted admin config save, write-only secret display, provider visibility while enabled, real create-transaction call, real `payment_url` return, real GM Pay cashier URL format, production health after deploy
  - unverified scope: real payment completion, webhook method/headers/raw body/signature fields, paid/failed status values, amount/currency/network verification, idempotency, and automatic Pro entitlement grants
  - production remains safe after cleanup: GM Pay disabled, encrypted official config retained, no temporary GM Pay test users, no local unpaid GM Pay test orders/events remaining
  - external GM Pay orders created during unpaid probes were not paid; they should expire naturally unless the GM Pay dashboard exposes a cancellation tool

## Known Code Issues

Fix these before large feature work:

1. Repository metadata in `package.json` previously pointed to placeholder GitHub URLs. Keep it aligned with `PDF_Flow_v2`.
2. The dedicated admin frontend is live at `https://admin.pawn.eu.org` with DNS, TLS through Nginx Proxy Manager, server environment values, CORS, read-only smoke evidence, and protected admin acceptance evidence.
3. Admin UI now has a separate frontend entry, but it still lives in the same repository tree until a future monorepo split is justified.
4. Locale-prefixed routes, browser-language preference, and basic SEO `hreflang` output exist for the current supported locales, but additional locale rollout still needs completion.
5. Public content blocks only normalize `zh*` to `zh` and otherwise fall back to `en`, so future languages need a more formal locale model.
6. Some internal diagnostic codes are still visible in advanced/account/admin-adjacent flows. They are useful for support, but public user-facing copy should stay calm and hide internal detail unless troubleshooting is needed.

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
- Keep backend settings in `backend/.env`; keep Compose/frontend host settings in untracked `.deploy.env`.
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
- Keep the Nginx Proxy Manager host for `admin.pawn.eu.org` forwarding to server port `5174`.
- Keep the real admin domain environment values on the server:
  - `backend/.env`: `ADMIN_FRONTEND_URL=https://admin.pawn.eu.org`
  - `.deploy.env`: `PUBLIC_FRONTEND_HOST=pdf.pawn.eu.org` and `ADMIN_FRONTEND_HOST=admin.pawn.eu.org`
- Re-verify DNS/TLS routing after future proxy changes so the public domain never serves the admin artifact and the admin domain can reach `/api/v1/admin/*`.
- Decide whether the future monorepo split is worth doing after production admin usage is stable.

Acceptance:

- Public app no longer contains `/control-room`.
- Admin app builds separately.
- Admin domain can sign in and access `/api/v1/admin/*`.
- Public domain cannot accidentally surface admin UI.

### Phase 5: Production Integration Acceptance

Goal: prove real external integrations.

OAuth:

- GitHub OAuth is the first provider being enabled for production.
- Google OAuth should remain unconfigured and hidden until its dashboard and credentials are ready.
- Current production status: GitHub client id and secret are present in `backend/.env`; Google values are empty.
- Provider dashboards use:
  - `{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/google/callback`
  - `{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/github/callback`
- Public config exposes only non-secret provider readiness, and the login UI displays only configured providers.
- OAuth failures return friendly callback states.
- Account linking/unlinking UI remains optional.

Email:

- Configure real sender/domain.
- Verify password reset email delivery.
- Keep enumeration-safe reset responses.
- Confirm reset links use `FRONTEND_URL`.
- Current status: enumeration-safe reset response is verified; real delivery is blocked until `RESEND_API_KEY` and sender/domain are configured.

Payments:

- Configure provider dashboards to call:
  - `{BACKEND_PUBLIC_URL}/api/v1/payment/webhooks/{provider}`
- Frontend return pages are not entitlement proof.
- Backend provider callbacks, amount/currency checks, and idempotent payment events are the trust boundary.
- Current production status: payment providers are disabled because merchant credentials are absent.
- Local Phase 1 status: GM Pay can now be configured from the admin backend, encrypted secrets are write-only, Pricing can select GM Pay when configured, and checkout can redirect to the GM Pay cashier.
- GM Pay automatic Pro activation remains blocked until a real webhook sample is available and strict signature, amount, currency, and idempotency verification are implemented.

AI/OCR/Office:

- Configure AI provider keys.
- Run OCR and Office smoke tests on server.
- Keep large-file and failed-job diagnostics observable from admin.
- Current status: OCR and Office smoke tests pass on the server; AI analysis is blocked until `GEMINI_API_KEY` is configured.

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

Server deploy env:

```bash
cat > .deploy.env <<'EOF'
PUBLIC_FRONTEND_HOST=pdf.pawn.eu.org
ADMIN_FRONTEND_HOST=admin.pawn.eu.org
EOF
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

Production acceptance:

```bash
PUBLIC_URL=https://pdf.pawn.eu.org \
ADMIN_URL=https://admin.pawn.eu.org \
bash scripts/production-acceptance.sh
```

Set `RUN_WRITE_PROBE=1` only with `LIVE_ADMIN_EMAIL` and `LIVE_ADMIN_PASSWORD`; the default acceptance path is read-only.

GM Pay Phase 1 production checklist:

```bash
# Generate the payment config master key on the server only.
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

- Add `PAYMENT_CONFIG_ENCRYPTION_KEY=<generated-value>` to server `backend/.env` only. Do not put the value in the database, admin UI, Git, docs, screenshots, audit logs, or chat.
- Keep the existing production URL settings in `backend/.env`: `FRONTEND_URL`, `ADMIN_FRONTEND_URL`, `BACKEND_PUBLIC_URL`, allowed hosts, and CORS origins.
- Existing `PAYMENT_ENABLED_PROVIDERS` and legacy `PAYMENT_GATEWAY_CONFIGS` can remain as they are. GM Pay is DB-managed after admin configuration, and old Stripe/PayPal/Alipay/WeChat fallback behavior remains environment-driven.
- Migration is included in `backend/alembic/versions/add_payment_provider_configs.py`. The normal deploy script runs migrations. If a manual migration is needed, run `cd backend && alembic upgrade head` inside the backend runtime environment.
- Deploy only after pushing the accepted local commits:
  ```bash
  cd /root/data/docker_data/PDF/pdf-flow
  git pull --ff-only v2 main
  bash scripts/deploy-main.sh
  ```
- Confirm services and migration state:
  ```bash
  docker compose --env-file backend/.env -f docker-compose.yml ps
  curl http://localhost:8000/health
  cat .deploy_state/main/current_deployed_commit
  ```
- Verify the admin configuration center at `https://admin.pawn.eu.org`: save GM Pay public fields and secret once, confirm the UI only shows configured status or tail, validate locally, then save again with secret blank and confirm the old secret remains configured.
- Verify public checkout at `https://pdf.pawn.eu.org/zh-cn/pricing`: sign in as a test user, choose GM Pay, create a monthly order, and confirm the returned page opens the GM Pay cashier URL.
- Check logs during smoke:
  ```bash
  docker compose --env-file backend/.env -f docker-compose.yml logs -f backend
  docker compose --env-file backend/.env -f docker-compose.yml logs -f frontend
  ```
- Useful DB tables for evidence when needed: `payment_provider_configs`, `payment_orders`, `payment_events`, and `admin_audit_logs`. Do not print or copy encrypted secret payloads unless debugging locally with care.
- Rollback:
  ```bash
  bash scripts/rollback-main.sh
  ```
  Keep the same `PAYMENT_CONFIG_ENCRYPTION_KEY` across rollback and redeploy. Changing it makes previously stored encrypted payment secrets unreadable.
- Phase 1 production acceptance stops at configure, create order, and open GM Pay cashier. Do not expect automatic Pro activation yet.
- Before Phase 2, collect a real GM Pay webhook sample and implement strict signature verification, amount verification, currency verification, idempotency, and entitlement granting in the backend trust boundary.

Stripe configuration-center Phase 1 local result:

- Scope: Stripe is now managed by the admin payment configuration center first, with legacy `STRIPE_*` environment variables kept as fallback when the DB config is disabled or incomplete.
- New admin fields:
  - Public config: `price_id_monthly`, `price_id_yearly`
  - Write-only encrypted secrets: `secret_key`, `webhook_secret`
- Verified locally:
  - Admin can save, modify, enable, and disable Stripe config through `/api/v1/admin/payment-configs/stripe`.
  - Secrets are encrypted in `payment_provider_configs`, API responses show only configured status plus tail, and blank secret inputs preserve existing encrypted values.
  - Admin audit detail records provider/enabled/changed field names only; no secret plaintext is recorded.
  - PaymentService reads enabled complete Stripe DB config without backend restart, and falls back to legacy env config when DB config is absent.
  - `/api/v1/payment/providers` exposes Stripe as enabled when the DB config is enabled and complete, so Pricing can show/select Stripe.
  - Stripe checkout session creation uses the DB `secret_key` and the configured monthly/yearly Price ID, creates a local pending `PaymentOrder`, and returns the Stripe Checkout URL.
  - Admin Payment Setup now renders Stripe and GM Pay in the same configuration center pattern.
- Not verified in this phase:
  - No real Stripe payment was made.
  - No real Stripe webhook sample was collected.
  - No automatic `paid` marking or Pro entitlement automation was changed for Stripe.
- Local checks:
  - `pytest backend/tests/test_payment_config_stripe.py backend/tests/test_payment_config_gmpay.py -q`
  - `pytest backend/tests/test_payment_domain.py backend/tests/test_admin_payment_domain.py backend/tests/test_admin.py -q`
  - `npm run type-check`
  - `npm run build`
  - `npm run build:admin`

PayPal configuration-center Phase 1 local result:

- Scope: PayPal is now managed by the admin payment configuration center first, with legacy `PAYPAL_*` environment variables kept as fallback when the DB config is disabled or incomplete.
- New admin fields:
  - Public config: `api_base_url`, `client_id`, optional `webhook_id`
  - Write-only encrypted secret: `client_secret`
- Verified locally:
  - Admin can save, modify, enable, and disable PayPal config through `/api/v1/admin/payment-configs/paypal`.
  - `client_secret` is encrypted in `payment_provider_configs`, API responses show only configured status plus tail, and blank secret input preserves the existing encrypted value.
  - Admin audit detail records provider/enabled/changed field names only; no secret plaintext is recorded.
  - PaymentService reads enabled complete PayPal DB config without backend restart, and falls back to legacy env config when DB config is absent.
  - `/api/v1/payment/providers` exposes PayPal as enabled when the DB config is enabled and complete, so Pricing can show/select PayPal.
  - PayPal checkout order creation uses DB `client_id`, encrypted `client_secret`, and `api_base_url`, creates a local pending `PaymentOrder`, and returns the PayPal approval URL.
  - `webhook_id` is stored for later webhook verification work, but it is not required for this phase's create-order acceptance.
  - Admin Payment Setup renders Stripe, PayPal, and GM Pay in the same configuration center pattern.
- Not verified in this phase:
  - No real PayPal payment was made.
  - No real PayPal webhook sample was collected.
  - No automatic `paid` marking or Pro entitlement automation was changed for PayPal.
- Local checks:
  - `pytest backend/tests/test_payment_config_paypal.py backend/tests/test_payment_config_stripe.py backend/tests/test_payment_config_gmpay.py -q`
  - `pytest backend/tests/test_payment_domain.py backend/tests/test_admin_payment_domain.py backend/tests/test_admin.py -q`
  - `npm run type-check`
  - `npm run build`
  - `npm run build:admin`

Payment scope cleanup Phase 1 local result:

- Scope: visible checkout/admin payment scope is now limited to `stripe`, `paypal`, and `gmpay`.
- Retained:
  - Stripe admin-managed config and legacy `STRIPE_*` fallback.
  - PayPal admin-managed config and legacy `PAYPAL_*` fallback.
  - GM Pay admin-managed config and checkout-to-cashier flow.
  - Backend historical compatibility for old provider orders and explicit legacy gateway checkout paths, including `PAYMENT_GATEWAY_CONFIGS.epusdt` fallback.
- Hidden/disabled from visible surfaces:
  - `/api/v1/payment/providers` no longer exposes `epay`, `alipay`, `wechat`, `tokenpay`, `bepusdt`, `epusdt`, or `okpay`, even if they are present in legacy environment variables.
  - Pricing provider selection is typed and rendered for the visible provider set only.
  - Admin payment operations provider cards now follow the same visible set while preserving historical order/event summaries and provider-filtered recent orders.
  - Admin Payment Setup remains limited to Stripe, PayPal, and GM Pay.
- Actually removed in this phase:
  - Deprecated provider keys were removed from frontend `PaymentProviderKey` and QR-provider UI mapping.
  - Default `PAYMENT_PROVIDER_ORDER` values in app config and Docker compose were reduced to `stripe,paypal,gmpay`.
- Not removed yet:
  - Alipay, WeChat Pay, EPay, TokenPay, BEPUSDT, EPUSDT, and OKPay provider/adapter code remains for historical compatibility until the second audit/cleanup phase.
  - Existing webhook/controller compatibility remains untouched.
- Local checks:
  - `pytest backend/tests/test_config.py backend/tests/test_payment_domain.py -q`
  - `pytest backend/tests/test_admin_payment_domain.py backend/tests/test_admin.py -q`
  - `npm run type-check`

Rollback:

```bash
bash scripts/rollback-main.sh
```

Tool workspace Phase 2 local result:

- Scope: migrated structure-similar local tool pages to the shared tool workspace layer without touching payment logic or adding new PDF features.
- Migrated pages:
  - Rotate PDF
  - Split PDF
  - PDF to Image
  - Image to PDF
  - Delete pages
  - Organize pages
  - Crop PDF
  - Page numbers
- Shared UI/state now reused by the migrated pages:
  - `ToolWorkspace`
  - `ToolActionPanel`
  - `ToolResultPanel`
  - `ToolErrorAlert`
  - `useToolFileSelection`
  - `useToolProcessingState`
- Deliberately not touched in this batch:
  - OCR PDF
  - Office to PDF
  - AI PDF Analyzer
  - Sign PDF
  - Fill Form PDF
  - Annotate PDF
- Notes:
  - PDF to Image keeps its page image result grid local to the page.
  - Organize PDF keeps the thumbnail drag-and-drop grid local to the page.
  - Crop PDF keeps its visual crop preview and redaction warning local to the page.
  - Image to PDF now normalizes images through canvas before passing them to jsPDF, fixing PNG CRC failures from tiny/edge-case PNG files.
  - Delete pages E2E locator was scoped to the main tool surface to avoid footer copy collisions.
- Local checks:
  - `npm run type-check`
  - `npm run test:unit:ci`
  - `npm run build`
  - `npm run build:admin`
  - `npx playwright test tests/e2e-playwright/local-pdf-workflows.spec.ts tests/e2e-playwright/advanced-pdf-workflows.spec.ts --project=chromium --reporter=line`
  - `npx playwright test tests/e2e-playwright/merge-pdf.spec.ts tests/e2e-playwright/compress-pdf.spec.ts tests/e2e-playwright/tool-pages-matrix.spec.ts --project=chromium --reporter=line`
- Production acceptance target for this batch: public tool pages render consistently on desktop/mobile and the migrated workflows have no functional regression. Do not start the next special-tool migration batch until this production batch is accepted.

Tool workspace Phase 3 local result:

- Scope: migrated the remaining public tool pages to the shared tool workspace layer before any separate Phase 4 visual polish.
- Low-risk pages migrated in this batch:
  - Watermark PDF
  - Flatten PDF
  - Protect PDF
  - Unlock PDF
  - Repair PDF
  - Extract Text PDF
  - Extract Images PDF
- Special-flow pages migrated in this batch while preserving their page-specific state machines:
  - Office to PDF
  - OCR PDF
  - Sign PDF
  - Fill Form PDF
  - Annotate PDF
  - AI PDF Analyzer
- Shared UI/state reused:
  - `ToolWorkspace`
  - `ToolActionPanel`
  - `ToolResultPanel` where the page already uses modal-style results
  - `ToolErrorAlert` through `ToolWorkspace`
  - `useToolFileSelection` and `useToolProcessingState` where they fit without disrupting special flows
- Deliberately preserved locally in pages:
  - Office/OCR backend job polling and access gates.
  - Sign PDF two-file upload and visual signature placement preview.
  - Fill Form and Annotate step-based configure/process/result flows.
  - AI Analyzer tab-specific actions and result renderers.
  - Extract Text and Extract Images result preview surfaces.
- Not changed:
  - Payment logic.
  - Backend APIs.
  - New PDF features.
  - Automatic Pro/payment entitlement behavior.
- Local checks:
  - `npm run type-check`
  - `npm run test:unit:ci`
  - `npm run build`
  - `npm run build:admin`
  - `npx playwright test tests/e2e-playwright/advanced-cloud-tools.spec.ts tests/e2e-playwright/tool-flow-regression.spec.ts --project=chromium --reporter=line`
  - `npx playwright test tests/e2e-playwright/advanced-pdf-workflows.spec.ts tests/e2e-playwright/local-pdf-workflows.spec.ts tests/e2e-playwright/tool-flow-regression.spec.ts tests/e2e-playwright/cloud-tool-access.spec.ts tests/e2e-playwright/advanced-cloud-tools.spec.ts tests/e2e-playwright/tool-pages-matrix.spec.ts --project=chromium --reporter=line`
- Next target after acceptance: Phase 4 unified UI polish across Home, Tools Center, and tool pages. Do not start backend refactor code before the separate backend audit/design phase is approved.

Tool workspace Phase 3 deployment result:

- Deployed commit `7f8342fcd8fe92cbd8387f2e833522b6aa362f76` on 2026-06-14 with `bash scripts/deploy-main.sh`.
- Server `.deploy_state/main/current_deployed_commit` records `7f8342fcd8fe92cbd8387f2e833522b6aa362f76`.
- Production Compose services are healthy after deploy: backend, celery-worker, frontend, postgres, redis.
- External smoke:
  - `https://pdf.pawn.eu.org/zh-cn/tools/ocr` returns HTTP 200.
  - `https://pdf.pawn.eu.org/zh-cn/tools/watermark` returns HTTP 200.
  - `https://admin.pawn.eu.org/` returns HTTP 200.
- Next approved work: Phase 4 unified frontend UI polish only. Keep payment logic, backend refactor code, and new PDF features out of this phase.

Frontend UI Phase 4 local result:

- Scope: unified frontend visual language across Home, Tools Center, and migrated tool pages without adding PDF features, changing payment logic, or entering backend refactor work.
- Shared UI layer updated:
  - `src/assets/styles/main.css`: cleaned global base styles, restored proper light/dark app surfaces, and added reusable `pf-app-surface`, `pf-panel`, `pf-panel-muted`, `pf-eyebrow`, and `pf-icon-tile` classes.
  - `ToolPageShell`, `ToolHeader`, `ToolWorkspace`, `ToolActionPanel`, `ToolAccessPanel`, `ToolNoticeBar`, and `ToolErrorAlert`: aligned spacing, panel treatment, sticky secondary action column, heading scale, borders, shadows, and state presentation.
  - `DragDropZone`: unified upload area treatment, dashed borders, mobile layout, and dark mode colors.
  - `Modal`/`ToolResultPanel`: tightened result modal sizing, scroll behavior, and light/dark consistency.
- Page-level polish:
  - `Home` and `ToolsCenter` now use the same app surface/panel language as tool pages.
  - Tool cards, filters, stats, and advanced sections have consistent borders, shadows, spacing, and dark mode behavior.
  - Fixed exposed i18n keys by pointing Fill Form and Annotate metadata/page subtitles to existing `.desc` locale keys.
- Local visual smoke:
  - Captured desktop screenshots for Home, Tools Center, Merge, and OCR.
  - Captured mobile screenshots for Annotate and Merge.
  - Checked representative pages for horizontal overflow and raw `tools.*` / `common.*` key exposure; all passed.
- Local checks:
  - `npm run type-check`
  - `npm run test:unit:ci`
  - `npm run build`
  - `npm run build:admin`
  - `npx playwright test tests/e2e-playwright/tool-pages-matrix.spec.ts tests/e2e-playwright/tool-flow-regression.spec.ts --project=chromium --reporter=line`
  - `npx playwright test tests/e2e-playwright/advanced-pdf-workflows.spec.ts tests/e2e-playwright/local-pdf-workflows.spec.ts tests/e2e-playwright/tool-flow-regression.spec.ts tests/e2e-playwright/cloud-tool-access.spec.ts tests/e2e-playwright/advanced-cloud-tools.spec.ts tests/e2e-playwright/tool-pages-matrix.spec.ts --project=chromium --reporter=line`
- Next approved work after this phase is complete: backend structure audit and refactor design only; do not start backend refactor code until that design is approved.

Frontend UI Phase 4 deployment result:

- Deployed commit `fae6ae0965f7a63505ea8218c95d83e4a67dba37` on 2026-06-14 with `bash scripts/deploy-main.sh`.
- Server `.deploy_state/main/current_deployed_commit` records `fae6ae0965f7a63505ea8218c95d83e4a67dba37`.
- Production Compose services are healthy after deploy: backend, celery-worker, frontend, postgres, redis.
- External HTTP smoke:
  - `https://pdf.pawn.eu.org/zh-cn/` returns HTTP 200.
  - `https://pdf.pawn.eu.org/zh-cn/tools` returns HTTP 200.
  - `https://pdf.pawn.eu.org/zh-cn/tools/merge` returns HTTP 200.
  - `https://pdf.pawn.eu.org/zh-cn/tools/ocr` returns HTTP 200 and correctly redirects unauthenticated Pro access into login flow.
  - `https://admin.pawn.eu.org/` returns HTTP 200.
- Production browser smoke:
  - Home, Tools Center, Merge, OCR/login flow, and Admin have no page errors, no horizontal overflow, no raw `tools.*` / `common.*` key exposure, and CSS is loaded.
  - Forced dark-mode CSS check on the Merge tool page applies dark background rules without horizontal overflow or raw key exposure.
- Frontend tool migration and UI polish are now closed for this round. Do not continue small public UI tweaks until a new frontend phase is explicitly opened.

Admin management design result:

- Added `docs/ADMIN_MANAGEMENT_DESIGN.md`.
- Scope: design only, no backend/admin code changes.
- Covers future admin-managed capabilities, menu structure, DB-managed vs env-only config, secret handling, validation/hot-update/audit rules, payment configuration center v2, feature flags/tool availability, plans/pricing, AI/OCR/Office provider configuration, site content, current admin code structure issues, extensibility model, and phased rollout.
- Recommended next implementation batch after approval: admin information-architecture cleanup, then product configuration center / feature flags.

Admin information architecture Phase A local result:

- Scope: admin frontend structure cleanup only. Existing routes, backend APIs, payment behavior, pricing behavior, and public frontend behavior were not changed.
- Introduced admin module descriptors in `src/admin/control-room/modules.ts` with module id, group, label, description, component name, required capability, domain, icon, and optional health/status badge source.
- Kept `src/admin/control-room/tabs.ts` as a compatibility wrapper over the new module descriptors so existing Control Room rendering does not need a risky route/API rewrite.
- Split Control Room wiring into domain files under `src/admin/control-room/domains/`:
  - overview
  - users
  - revenue
  - productConfig
  - operations
  - security
- `useControlRoom()` now returns both the old flat shape and new domain/module objects, so existing tabs keep working while Phase B has clear mount points.
- Cleaned visible mojibake in Control Room module labels/descriptions, destructive action confirmations, copy messages, and generated admin summaries.
- Added lightweight menu status badges sourced from existing overview/operations/payment/diagnostic/maintenance/audit state; these are presentation-only and do not change backend behavior.
- Phase B best mount points:
  - Feature Flags / Tools & Features: `productConfig` domain and Product Config group.
  - Plans & Pricing: `revenue` domain and Customers & Revenue group.
  - Payment Providers v2: `revenue` domain, replacing the current Payment Setup module internals later.
  - AI/OCR/Office providers: Product Config or Operations depending on whether the module controls configuration or runtime health.

Admin Tools & Features Phase B local result:

- Scope: product configuration module only. Payment Providers v2, Plans & Pricing, payment behavior, AI/OCR provider configuration, and new PDF features were not changed.
- Data model:
  - Reused existing `feature_flags`.
  - Added `feature_flags.is_public` with migration `ff_public_visibility`.
  - `enabled` means the feature can be used and is enforced by frontend route guards plus backend API gates.
  - `is_public` means the feature appears in public entry surfaces such as Home, Tools Center, and Footer.
  - This keeps "hidden from public listings" separate from "disabled/unavailable".
- Admin interaction structure:
  - Product Config module label is now `工具与功能`.
  - `FeatureFlagsTab` groups tools by PDF tool category, supports search, shows summary counts, and edits:
    - public display
    - allowed to use
    - login required
    - Pro required
    - maintenance message
  - Saving continues through existing `/api/v1/admin/feature-flags/{key}` and writes admin audit records with changed field names only.
- Frontend gating points:
  - Public config now returns `is_public`.
  - `siteConfigStore.isFeatureVisible()` is the shared public-listing rule: `enabled && is_public`.
  - Home, Tools Center, and Footer use the shared public-listing rule.
  - Tool route guard still uses `enabled`, `requires_login`, and `requires_pro`; it does not block direct routes only because `is_public=false`.
- Backend gating points:
  - `require_feature_access()` remains the shared backend API gate for processing endpoints.
  - Backend gates ignore `is_public` and enforce maintenance mode, enabled/disabled, login requirement, and Pro requirement.
  - Hidden-but-enabled tools remain callable by direct route/API if other access rules allow it.
- Remaining scattered judgments:
  - Header still exposes top-level Tools/Features/Pricing navigation because these are site sections, not individual tool flags.
  - Some tool components still contain local access messaging and upload-state copy; Phase B did not move those into a registry.
  - Future cleanup should centralize per-tool access badges, Pro messaging, and route/list copy after this module has been production-proven.
- Local checks:
  - `pytest tests/test_admin.py tests/test_admin_content_domain.py -q`
  - `npm run type-check`
  - `npm run test:unit:ci`
  - `npx playwright test tests/e2e-playwright/availability-state.spec.ts --project=chromium --reporter=line`
  - `npm run build`
  - `npm run test:e2e:admin`

Admin Tools & Features Phase B production result:

- Deployment:
  - Production deployed commit: `4d0588c1d91a635f563d8b11ea0151d471efa667`.
  - Alembic version on production: `ff_public_visibility`.
  - The initial long migration revision id was shortened because production `alembic_version.version_num` is `varchar(32)`.
- Verification tool:
  - Used `compress_pdf` because it appears in Home, Tools Center, Footer, has a direct route, and has a backend API gate at `/api/v1/files/compress`.
- Production verification matrix:
  - `enabled=true`, `is_public=true`: Home, Tools Center, Footer, and direct route show the tool; API reached business logic and returned `404 File not found` for the fake file id, proving the feature gate allowed the request.
  - `enabled=true`, `is_public=false`: Home, Tools Center, and Footer hide the tool; direct route still opens; API still reached business logic and returned `404 File not found`. This confirms `is_public` only controls public entry visibility.
  - `enabled=false`: public entries hide the tool; direct route redirects to the feature-disabled state with the maintenance message; API returns `503`.
  - `requires_login=true`: public entries remain visible when public; anonymous direct route redirects to login; API returns `401`.
  - `requires_pro=true`: public entries remain visible when public; anonymous/free direct route redirects to pricing; API returns `403`.
- Audit:
  - Feature flag saves wrote `admin_audit_logs` entries with `changed_fields=...`.
  - Audit details recorded changed field names only.
- Restore:
  - `compress_pdf` was restored after verification to `enabled=true`, `is_public=true`, `requires_login=false`, `requires_pro=false`, `maintenance_message=null`.
  - Production label/description for `compress_pdf` were restored to normal Chinese text after verification cleanup.
- Scope guard:
  - No Plans & Pricing work was started.
  - No Payment Providers v2 work was started.
  - Payment behavior was not changed.

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

1. Set `PAYMENT_CONFIG_ENCRYPTION_KEY` on production, enter GM Pay merchant config in Admin `Payment Setup`, and run the checkout-to-cashier smoke test.
2. Collect a real GM Pay webhook sample, then implement strict webhook verification, amount/currency checks, idempotency checks, and only then enable automatic Pro activation.
3. Configure Gemini credentials when the AI quota/account is ready and rerun AI feature smoke tests.
4. Decide when to expose additional locales such as `ja`, `ko`, and `de`; do not expose them until baseline translations exist.
5. Add competitor-gap tools only after the platform refactor remains stable under production traffic.
6. Decide whether to split the admin frontend into its own repository after the dedicated admin domain is live and daily operation is stable.
