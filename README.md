# AI Product Listing Generator

Turborepo scaffold for an AI-powered SaaS platform that generates SEO-oriented product listings from product images.

The repository follows the project docs in `docs/`:

- API-first development
- Clean Architecture and SOLID principles
- Feature-based frontend and backend structure
- Version-controlled prompt package
- Docker-ready local infrastructure

Authentication is implemented for the MVP. Product uploads and AI generation are not implemented
yet.

## Workspace Layout

```txt
apps/
  web/      Next.js 15, TypeScript, Tailwind CSS, Shadcn-ready UI
  api/      FastAPI application scaffold with Turborepo wrapper scripts
packages/
  ui/       Shared UI primitives
  types/    Shared TypeScript contracts
  prompts/  Prompt registry scaffold
infra/
  docker/   Dockerfiles for deployable services
docs/       Product, architecture, and engineering specifications
```

## Prerequisites

- Node.js 22+
- pnpm 9+
- Python 3.12+
- Docker and Docker Compose

## Environment Setup

Create a local environment file:

```bash
cp .env.example .env
```

Set service-specific values before implementing connected workflows:

- `NEXT_PUBLIC_API_BASE_URL`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `SESSION_COOKIE_NAME`
- `OPENAI_API_KEY`
- `AWS_REGION`
- `AWS_S3_BUCKET`

For local authentication, configure the API URL and a long JWT secret:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
JWT_SECRET_KEY=replace-with-a-long-random-local-secret
```

The backend hashes passwords, persists users in PostgreSQL, and sets an HTTP-only JWT session
cookie named by `SESSION_COOKIE_NAME`.

## Install Dependencies

```bash
pnpm install
```

For the API:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Development

Run all Turborepo tasks:

```bash
pnpm dev
```

Run individual apps:

```bash
pnpm --filter @ai-product-listing/web dev
pnpm --filter @ai-product-listing/api dev
```

Visit:

- Login: `http://localhost:3000/login`
- Protected dashboard: `http://localhost:3000/dashboard`
- API session check: `http://localhost:8000/api/v1/auth/me`

## Quality Checks

```bash
pnpm lint
pnpm typecheck
pnpm build
```

API checks:

```bash
pnpm --filter @ai-product-listing/api lint
pnpm --filter @ai-product-listing/api typecheck
pnpm --filter @ai-product-listing/api test
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Web: `http://localhost:3000`
- API: `http://localhost:8000/api/v1/health`
- Login: `http://localhost:3000/login`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

The Docker PostgreSQL service runs `infra/postgres/init/001_auth.sql` on first database creation to
create the auth `users` table.

If you previously ran the Google-auth scaffold, recreate the local Postgres volume so the `users`
table is rebuilt with `password_hash` instead of `google_subject`.
