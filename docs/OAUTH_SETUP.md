# OAuth Setup

PDF-Flow supports Google and GitHub sign-in through the backend OAuth routes. This document is an operations checklist, not an implementation history.

## Current Implementation

Backend:

- `GET /api/v1/auth/oauth/{provider}` starts the provider redirect.
- `GET /api/v1/auth/oauth/{provider}/callback` exchanges the provider code, creates or links the user, and redirects to the frontend callback route with tokens.
- `POST /api/v1/auth/oauth/link/{provider}` and its callback exist for account linking, but full product UI for linking/unlinking is not a current acceptance priority.

Frontend:

- `/auth/login` exposes Google and GitHub entry points.
- `/auth/oauth-callback` stores returned tokens, clears unsafe redirect state, and sends users back to an internal destination only.
- Regression coverage lives in `tests/e2e-playwright/oauth-callback.spec.ts` and `tests/e2e-playwright/auth-state.spec.ts`.

## Required Environment

Set these in `backend/.env` on the server or local backend environment:

```bash
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx
GITHUB_CLIENT_ID=xxxxx
GITHUB_CLIENT_SECRET=xxxxx
BACKEND_PUBLIC_URL=https://api.example.com
FRONTEND_URL=https://example.com
ALLOWED_ORIGINS=https://example.com
```

`BACKEND_PUBLIC_URL` and `FRONTEND_URL` should match the public URLs used by provider dashboards and browser redirects. Keep real client secrets out of Git.

## Provider Dashboard URLs

Google authorized redirect URI:

```text
{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/google/callback
```

GitHub authorization callback URL:

```text
{BACKEND_PUBLIC_URL}/api/v1/auth/oauth/github/callback
```

For local development, use:

```text
http://localhost:8000/api/v1/auth/oauth/google/callback
http://localhost:8000/api/v1/auth/oauth/github/callback
```

## Local Verification

1. Start backend and frontend.
2. Open `http://localhost:5173/auth/login`.
3. Click Google or GitHub.
4. Complete provider authorization.
5. Confirm the browser lands on `/auth/oauth-callback` briefly, stores tokens, and redirects only to an internal route.

Automated callback-state checks:

```bash
npx playwright test tests/e2e-playwright/oauth-callback.spec.ts tests/e2e-playwright/auth-state.spec.ts --project=chromium --reporter=line
```

## Production Acceptance

- Provider credentials exist in server `backend/.env`.
- Provider dashboards use the production backend callback URLs.
- `ALLOWED_ORIGINS` includes the production frontend origin.
- Login redirects never preserve external `redirect` URLs.
- OAuth failures return a user-facing callback error instead of a raw provider page.

## Known Follow-Ups

- Add account linking/unlinking UI if the product needs it.
- Move token delivery to a more secure cookie-based flow if the backend/frontend deployment is later reorganized around same-site domains.
