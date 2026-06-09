# PDF-Flow NPM Domain Deployment Design

Date: 2026-06-09
Status: Draft approved in chat, awaiting final user confirmation before implementation

## Goal

Make PDF-Flow accessible in both of these ways at the same time:

1. Domain access through Nginx Proxy Manager using `pdf.pawn.eu.org`
2. Direct fallback access through `http://<server-ip>:5173`

Keep backend API docs reachable through `http://<server-ip>:8000/api/docs` during the current testing phase.

## Constraints

- Single server
- Docker and Docker Compose only on server
- User wants domain access and IP+port access to coexist
- Nginx Proxy Manager will be the public reverse proxy entry, but is not fully configured yet
- Current repo already contains a frontend nginx container and backend FastAPI container
- Current frontend container is misconfigured in Compose: image is built as nginx static site, but Compose starts it with `npm run dev`

## Recommended Approach

Use one frontend delivery model for both domain and IP access:

- `Nginx Proxy Manager -> frontend container (nginx) -> backend container`
- direct `http://<server-ip>:5173 -> frontend container (nginx) -> backend container`

The frontend must no longer call a hard-coded backend origin such as `http://localhost:8000`.
Instead, frontend requests should use same-origin relative paths:

- `/api/v1/...`
- `/health`
- `/api/docs`
- websocket paths under `/api/v1/ws/...`

This keeps domain access and IP access on the same request model and avoids split behavior.

## Architecture

### External access

1. `https://pdf.pawn.eu.org`
   - handled by Nginx Proxy Manager
   - proxied to server port `5173`
   - frontend nginx serves the SPA
   - frontend nginx proxies API and websocket requests to backend container

2. `http://<server-ip>:5173`
   - direct fallback access
   - same frontend nginx behavior as domain access

3. `http://<server-ip>:8000/api/docs`
   - backend direct access kept during testing
   - useful for API inspection and debugging

### Internal container routing

- frontend nginx proxies:
  - `/api/` -> `http://backend:8000/api/`
  - `/health` -> `http://backend:8000/health`
  - websocket upgrades -> `http://backend:8000`

## Required Repository Changes

### 1. `docker-compose.yml`

- Keep backend public port `8000:8000`
- Keep frontend public port mapping, but map host `5173` to container `80`
- Remove the frontend `command: npm run dev -- --host 0.0.0.0`
- Stop injecting `VITE_API_URL=http://localhost:8000` into frontend runtime
- Ensure frontend runs as the nginx image defined by `Dockerfile.frontend`

Expected end state:

- frontend is a production-style static container
- direct IP access and domain access hit the same container behavior

### 2. `nginx.conf`

Need to support:

- SPA routing
- reverse proxy for backend API
- reverse proxy for health endpoint
- websocket upgrade headers
- CSP `connect-src` that does not break same-origin API calls

Expected behavior:

- browser loaded from `pdf.pawn.eu.org` can call `/api/...`
- browser loaded from `server-ip:5173` can also call `/api/...`

### 3. `src/services/api.ts`

Change API base resolution to prefer same-origin relative paths by default.

Recommended behavior:

- If `VITE_API_URL` is provided, use it
- Otherwise use `''` so requests go to same host

This makes both of these work:

- `https://pdf.pawn.eu.org`
- `http://<server-ip>:5173`

without any extra rebuild just to switch origins.

### 4. Backend environment defaults and docs

Prepare deployment docs and example env guidance for:

- `FRONTEND_URL=https://pdf.pawn.eu.org`
- `ALLOWED_ORIGINS` including:
  - `https://pdf.pawn.eu.org`
  - `http://pdf.pawn.eu.org`
  - `http://<server-ip>:5173`
- `OAUTH_REDIRECT_URL` guidance aligned with domain deployment

For the current stage, backend direct port `8000` remains exposed.

## Nginx Proxy Manager Configuration

Target configuration after repo changes:

- Domain: `pdf.pawn.eu.org`
- Scheme to upstream: `http`
- Forward hostname / IP: server IP or docker host
- Forward port: `5173`

Recommended NPM options:

- Enable websocket support
- Enable SSL after basic HTTP path is validated
- Force SSL only after HTTPS access is confirmed healthy

NPM should proxy to the frontend only.
Do not expose backend directly through NPM for the main user-facing site in this phase.

## Error Handling Expectations

### Frontend unavailable

- If frontend container fails, `docker compose ps` should show `frontend` unhealthy or exited
- direct symptom: `pdf.pawn.eu.org` and `server-ip:5173` both fail
- backend docs on `8000` may still remain available

### Backend unavailable

- frontend can still load shell assets
- API calls under `/api` or `/health` fail through nginx proxy
- this isolates frontend serving from backend API failure

### NPM unavailable

- direct IP fallback at `http://<server-ip>:5173` should still work

## Testing Plan

### Server-side verification

1. `docker compose up -d --build frontend backend`
2. `docker compose ps`
3. `curl http://localhost:5173`
4. `curl http://localhost:5173/health`
5. `curl http://localhost:8000/health`

### Browser verification

1. Open `http://<server-ip>:5173`
2. Open `https://pdf.pawn.eu.org` after NPM setup
3. Verify login/register
4. Verify PDF merge upload/download
5. Verify OCR
6. Verify Office to PDF
7. Verify error messages for failed inputs

## Rollout Order

1. Fix repo configuration
2. Update deployment docs
3. Push to `main`
4. Server pulls `main`
5. Rebuild frontend and backend
6. Validate IP fallback first
7. Configure NPM to point `pdf.pawn.eu.org` to port `5173`
8. Validate domain access
9. Record results in `PROJECT_MASTER.md`

## Non-Goals

- No full migration to hidden backend-only private networking in this step
- No removal of backend public `8000` during this testing phase
- No split-domain setup like `app.domain` + `api.domain` in this step

## Resume Point After Implementation

After the config change is deployed, the next session should resume from:

1. validating `http://<server-ip>:5173`
2. configuring NPM host for `pdf.pawn.eu.org`
3. validating domain access
4. recording any real browser-side regressions
