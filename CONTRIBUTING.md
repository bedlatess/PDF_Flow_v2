# Contributing to PDF-Flow

Thank you for your interest in contributing to PDF-Flow.

## Development Setup

### Prerequisites

- Node.js 22
- Python 3.11
- Docker and Docker Compose for backend services

### Frontend Setup

```bash
npm install
npm run dev
npm run test:unit
npm run build
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

## Official Repository

The active project repository is:

```text
https://github.com/bedlatess/PDF_Flow_v2.git
```

In this workspace, the official remote is named `v2`.

```bash
git remote -v
git pull --ff-only v2 main
```

If an older checkout still uses `origin` for `PDF_Flow_v2`, rename it once:

```bash
git remote rename origin v2
```

## Code Style

### Frontend

- Use TypeScript and Vue 3 Composition API patterns.
- Keep UI changes consistent with the existing component and copy style.
- Run `npm run type-check`, `npm run build`, and relevant tests before submitting changes.

### Backend

- Use type hints and clear FastAPI/Pydantic boundaries.
- Keep service, domain, and route responsibilities separated.
- Run targeted pytest coverage for touched areas.

## Commit Messages

Use concise conventional-style commit messages:

```text
feat: add new PDF tool
fix: resolve file upload timeout
docs: update deployment runbook
refactor: simplify auth service
test: add coverage for merge PDF
chore: update dependencies
```

## Pull Request Process

1. Create a focused branch from `main`.
2. Make the change with matching tests or verification notes.
3. Run the relevant frontend and backend checks.
4. Commit with a clear message.
5. Open the pull request against `bedlatess/PDF_Flow_v2`.

## Testing

Frontend:

```bash
npm run test:unit:ci
npm run type-check
npm run build
```

Backend:

```bash
cd backend
pytest tests -q
```

## Documentation

- Update `README.md` for user-facing setup or deployment changes.
- Update `docs/PROJECT_MASTER.md` for current project state changes.
- Update the relevant runbook under `docs/` when operations steps change.

## Questions

- Open an issue: https://github.com/bedlatess/PDF_Flow_v2/issues
- Start a discussion: https://github.com/bedlatess/PDF_Flow_v2/discussions
