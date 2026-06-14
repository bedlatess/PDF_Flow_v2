# PDF-Flow Admin Management Design

Date: 2026-06-14

## Scope

This design covers the next admin-management phase after the public tool workspace migration and UI polish. It is a design document only. Do not implement backend refactor code from this document until the plan is accepted.

Non-goals for the next implementation batch:

- No public tool UI micro-polish.
- No payment entitlement automation without verified webhook samples.
- No backend task-model refactor before a separate backend design is approved.
- No storage of master secrets in the database or admin UI.

## Product Principle

The admin console should become the operating system for PDF-Flow. Operators should manage product availability, commercial configuration, provider readiness, content, and operational policy without editing server files for normal business changes.

The server environment remains the trust root. Anything that unlocks database secrets, signs platform identity, or controls infrastructure access must stay env-only.

## Target Admin Capabilities

The admin console should eventually manage these areas:

1. Operations overview
   - Service health
   - Recent jobs
   - Error summary
   - Payment readiness
   - Open feedback and support risk

2. Users and entitlements
   - User status
   - Role and plan override
   - Manual Pro/Enterprise grant
   - Password reset link generation until email is fully available
   - Test-user cleanup

3. Payment configuration center
   - Stripe
   - PayPal
   - GM Pay
   - Provider enable/disable
   - Secret write-only fields
   - Local validation and readiness checklist
   - Webhook sample status and go-live gates

4. Plans and pricing
   - Plan list
   - Billing interval
   - Display price
   - Provider price mapping
   - Public pricing visibility
   - Internal plan limits

5. Feature flags and tool availability
   - Tool enabled/disabled
   - Login required
   - Pro required
   - Maintenance message
   - Rollout status
   - Public visibility state

6. Provider configuration
   - AI provider settings
   - OCR provider settings
   - Office conversion provider settings
   - Provider priority/fallback rules
   - Connectivity validation
   - Usage limits and cost guardrails

7. Site content and display configuration
   - Homepage copy blocks
   - Tool-center display blocks
   - Public support/contact text
   - Locale-aware content blocks
   - SEO-safe public metadata later

8. System policy
   - File retention policy
   - Max upload sizes
   - Per-plan usage limits
   - Rate-limit profiles
   - Maintenance mode
   - Public config cache TTL

9. Audit and diagnostics
   - Admin action logs
   - Secret-field change events without values
   - Config version history
   - Provider validation logs
   - Payment reconciliation evidence

## Proposed Admin Menu Structure

The current Control Room should move toward clearer product/operations domains:

| Group | Module | Purpose |
| --- | --- | --- |
| Overview | Dashboard | Health, payment readiness, user/job/support summary |
| Customers | Users | Accounts, bans, roles, reset links, manual entitlements |
| Revenue | Plans & Pricing | Plans, limits, price display, provider price mapping |
| Revenue | Payment Providers | Stripe, PayPal, GM Pay configuration and readiness |
| Revenue | Payment Reconciliation | Orders, events, webhook samples, evidence packets |
| Product | Tools & Feature Flags | Tool availability, login/Pro gates, maintenance copy |
| Product | Site Content | Public copy/content blocks and localized display settings |
| Providers | AI Providers | Model provider, API connectivity, usage/cost guardrails |
| Providers | OCR Providers | OCR engine/provider config and health |
| Providers | Office Providers | Office conversion config and health |
| System | Policies | Retention, upload limits, rate profiles, maintenance mode |
| System | Jobs | Task status and failed job inspection |
| System | Errors & Diagnostics | API errors, diagnostic bundle, support correlation |
| Security | Admin Security | Admin password/session controls |
| Security | Audit Log | Config, user, payment, and maintenance action logs |

The first UI pass can keep the existing Control Room shell, but the tab model should move from one flat list into module descriptors with route-like module ids. This avoids a single mega component becoming the permanent admin architecture.

## Configuration Ownership

### Database-managed configuration

These should be database-backed because operators need to change them without a deploy:

- Payment provider public config:
  - Enabled state
  - Display name
  - API base URL
  - Merchant/account id
  - Currency/token/network where applicable
  - Sandbox/live mode flag
  - Provider-specific non-secret options

- Payment provider encrypted secrets:
  - Stripe secret key
  - Stripe webhook secret
  - PayPal client secret
  - GM Pay secret key
  - Other provider credentials only when encryption key is available

- Feature flags:
  - Enabled
  - Requires login
  - Requires Pro
  - Maintenance message
  - Public display state

- Plans and pricing:
  - Plan names
  - Public price display
  - Billing interval
  - Feature/usage limits
  - Provider price ids and product ids
  - Plan visibility

- Provider runtime options:
  - AI provider choice
  - AI model names
  - OCR provider/engine selection
  - Office conversion provider selection
  - Timeout/attempt settings within safe bounds
  - Enabled state and provider priority

- Site content:
  - Public content blocks
  - Locale-specific homepage/tool-center copy
  - Support/contact copy

- System policies:
  - File retention days
  - User-facing maintenance mode
  - Upload-size policy per tool or plan
  - Rate-limit profile names

### Env-only configuration

These must not be stored in the database, exposed in admin UI, or committed to git:

- `SECRET_KEY`
- JWT signing keys or equivalent auth signing secrets
- `PAYMENT_CONFIG_ENCRYPTION_KEY`
- Database URL and database credentials
- Redis URL/password when sensitive
- SMTP password or mail-provider API secret if mail is infrastructure-level
- OAuth client secrets if not yet migrated into an encrypted provider-config model
- Cloud storage root credentials
- Server SSH credentials
- Any root encryption key that protects other stored secrets
- Sentry or observability DSN only if it can leak sensitive project identity or write tokens

Rule: if losing this value exposes all other secrets, allows infrastructure access, or prevents decrypting stored secrets, it is env-only.

## Secret Handling Rules

Sensitive admin-managed provider fields must follow the payment-config center model:

- Write-only in UI.
- Never returned by API.
- Show only:
  - Not configured
  - Configured
  - Configured, tail `xxxx` when a safe tail can be derived
- Empty secret on save means keep existing secret.
- Explicit clear requires a separate confirm action.
- Audit logs record field names changed, not values.
- Validation logs must never include raw secret, private key, token, certificate, or full Authorization header.
- Production must refuse secret read/write if `PAYMENT_CONFIG_ENCRYPTION_KEY` is missing.

## Validation, Hot Update, and Audit

Every admin-managed config should declare:

- Required fields
- Secret fields
- Public fields
- Restart requirement
- Validation type
- Public exposure level
- Audit event type

Validation levels:

1. Static validation
   - Required fields
   - URL format
   - Currency/network enum
   - Local signature generation

2. Connectivity validation
   - Provider API reachable
   - Credentials accepted if supported without creating chargeable resources
   - No real payment, OCR, AI job, or user-visible side effect

3. Readiness validation
   - Webhook URL configured
   - Return URLs match current public domain
   - Required env-only keys present
   - Provider-specific go-live checklist completed

Hot update rules:

- Provider enable/disable should apply immediately after save.
- Pricing/provider visibility should apply without backend restart.
- Feature flags should apply on the next API/public-config fetch.
- Long-running workers may cache heavy provider clients, but must reload config per job or on short TTL.
- If a setting requires restart, admin UI must label it clearly and prevent misleading "live" status.

Audit rules:

- Record admin id, action, target type, target key, changed field names, status, timestamp, and request id.
- Do not log secrets or full tokens.
- For system-risk changes, record old/new high-level state, such as `enabled: false -> true`.
- Payment provider go-live changes require a stronger confirmation and audit event.

## Payment Configuration Center Future Shape

Keep `payment_provider_configs` as the unified provider-config table for Stripe, PayPal, and GM Pay.

Recommended provider model:

- Provider registry defines:
  - `provider_key`
  - display name
  - supported modes: one-time, subscription
  - supported currencies
  - required public fields
  - required secret fields
  - optional fields
  - validation adapter
  - checkout adapter
  - webhook adapter status

- Admin UI renders from registry metadata.
- Backend saves into provider config store with encrypted secret field handling.
- PaymentService continues DB-first and env fallback where already supported.
- `epusdt` remains backend fallback compatibility only unless re-approved for UI.

Payment go-live gates:

- Config complete
- Local validation passed
- Connectivity validation passed
- Provider enabled
- Checkout/session creation verified
- Webhook sample captured
- Signature verification implemented
- Amount, currency, idempotency checks implemented
- Entitlement automation explicitly enabled

Do not allow "success page grants Pro" as a production entitlement path.

## Feature Flags and Tool Availability

Feature flags should become the canonical control for:

- Public tool visibility
- Login requirement
- Pro requirement
- Maintenance lock
- Tool category/display metadata later

Avoid scattering tool availability rules across `pdfTools.ts`, backend feature-gate code, and ad hoc frontend checks. The target shape:

- `pdfTools.ts` remains compile-time routing metadata.
- Admin-managed feature flags control runtime availability.
- Public config endpoint returns only safe runtime visibility/gating data.
- Backend checks the same flag for protected APIs.
- Audit logs record all flag changes.

## Plans and Pricing

Move commercial plan facts into a managed model, but do it carefully:

Phase target fields:

- Plan key: `free`, `pro_monthly`, `pro_yearly`, `enterprise`
- Display name
- Public visibility
- Price amount/currency/interval
- Feature limits
- Provider price mappings:
  - Stripe price id
  - PayPal plan/product id
  - GM Pay amount/currency/token/network
- Checkout enabled per provider

Env fallback remains for existing deployed payment values until each provider is fully migrated.

## AI, OCR, and Office Provider Configuration

These should use a generalized provider-config pattern, but not the same table as payment unless the schema is intentionally generic.

Recommended table later:

- `service_provider_configs`
  - `service_key`: `ai`, `ocr`, `office`
  - `provider_key`: `openai`, `local_tesseract`, `libreoffice`, etc.
  - `enabled`
  - `priority`
  - `public_config`
  - `encrypted_secret_config`
  - `validation_status`
  - `updated_by`
  - timestamps

The admin UI can share rendering primitives with payment provider setup, but adapters must stay separate. Payment, AI, OCR, and Office have different validation, risk, and runtime behavior.

Env-only remains required for master secrets and infrastructure credentials.

## Site Content and Display Config

The existing content-block and site-setting model can evolve into:

- Site identity
- Homepage copy
- Tool-center copy
- Support copy
- Public status banners
- Localized blocks

Rules:

- Public content can be stored in DB and returned through public config.
- Rich content needs sanitization and preview.
- Changes should be audit logged.
- Content should support draft/published later, but first phase can stay direct-publish.

## Current Admin Code Structure Issues

1. Control Room is still too centralized
   - `src/views/admin/ControlRoom.vue` imports every tab and wires a large composable output into one page.
   - This works now but will become a bottleneck as providers and modules grow.

2. Tab descriptors are display-first, not domain-first
   - `tabs.ts` is a flat list with mixed groups.
   - It does not define permissions, route ids, required API scopes, or module ownership.

3. Action/context composables are broad
   - `useControlRoom` exposes many unrelated domains at once.
   - Payment actions, user actions, maintenance actions, and diagnostics share one context surface.

4. Backend admin endpoint is a broad controller
   - `backend/app/api/v1/endpoints/admin.py` exposes many unrelated concerns.
   - Domain helpers exist, but controller routing is still too dense.

5. Configuration models are inconsistent by domain
   - Feature flags, site settings, content blocks, and payment provider configs each have different shape and semantics.
   - There is no common metadata contract for validation, secret handling, restart requirement, public exposure, or audit behavior.

6. Text/i18n quality is uneven
   - Some admin labels appear mojibake in source.
   - This makes admin harder to operate and test reliably.

7. Provider expansion risks becoming ad hoc
   - Payment has started moving toward provider adapters.
   - AI/OCR/Office provider configuration does not yet have the same admin-managed model.

## Extensibility Model

Add a new provider or admin-managed service by adding:

1. Registry entry
   - Provider key
   - Display metadata
   - Fields and secret flags
   - Validation rules
   - Runtime adapter

2. Config storage
   - Public config JSON
   - Encrypted secret config JSON
   - Enabled state
   - Validation status

3. Adapter
   - Validate
   - Build runtime client
   - Create job/order/session where applicable
   - Parse callback/event where applicable

4. Admin module
   - Uses shared config editor components
   - Does not know secret values
   - Calls generic save/validate endpoints scoped by service/provider

5. Audit entry
   - Field names changed
   - Validation status changed
   - Enabled state changed

This keeps new providers from turning into a chain of special-case if/else blocks.

## Phased Implementation Plan

### Phase A: Admin information architecture cleanup

Goal: make the current admin console easier to extend before adding more config modules.

- Introduce admin module descriptors:
  - id
  - group
  - label
  - description
  - component
  - required capability
  - health badge source
- Keep existing routes and APIs.
- Split Control Room wiring by domain-level composables:
  - overview
  - users
  - revenue
  - product config
  - operations
  - security
- Fix admin mojibake labels.

### Phase B: Product configuration center

Goal: centralize feature flags, tools, and site display controls.

- Expand Feature Flags module into Tools & Features.
- Add better flag grouping by tool category.
- Add public visibility preview.
- Add maintenance-message preview.
- Audit all changes.
- Keep existing feature flag table.

### Phase C: Plans and pricing management

Goal: stop hardcoding commercial plan display and provider price mapping.

- Add plan/pricing model.
- Admin UI edits plan display and provider mappings.
- Public pricing reads DB-first with fallback.
- Payment checkout resolves plan/provider mapping from DB-first source.
- Audit changes.

### Phase D: Payment provider center v2

Goal: make payment configuration center fully registry-driven for Stripe, PayPal, and GM Pay.

- Keep `payment_provider_configs`.
- Add provider metadata registry.
- Render admin forms from field metadata.
- Add validation status history.
- Keep secrets write-only and encrypted.
- Keep webhook entitlement automation disabled until strict provider-specific sample validation exists.

### Phase E: Service provider configuration

Goal: support AI/OCR/Office providers without env-file edits for normal provider switching.

- Add `service_provider_configs`.
- Add AI/OCR/Office admin modules.
- Add connectivity validation without chargeable or destructive actions.
- Add worker config reload behavior.

### Phase F: System policy and audit maturity

Goal: make operations safer.

- Add policy center for retention, upload limits, rate profiles, and maintenance mode.
- Add config version history.
- Add stronger confirmations for risky changes.
- Add audit filters and export.

## First Module Recommendation

Start with Phase A, then Phase B.

Reason:

- The admin UI structure is already showing centralization pressure.
- Feature flags and tool availability are safer than pricing/payment to refactor first.
- The same module descriptor and config editor patterns will be reused by pricing, payment, and provider modules.
- This avoids adding another important admin feature into the current broad Control Room shape.

Recommended first implementation batch:

1. Admin module descriptor refactor.
2. Fix admin source labels/mojibake in navigation/header.
3. Split Control Room state/actions into clearer domain composables without changing backend behavior.
4. Improve Feature Flags module grouping and tool-control presentation.
5. Add audit clarity for feature flag changes if missing.

Acceptance:

- Admin functions behave as before.
- No payment behavior changes.
- No public tool behavior changes except admin-managed feature flag display if explicitly changed.
- Admin menu is clearer and ready for Plans/Providers modules.
- Tests/build pass.
