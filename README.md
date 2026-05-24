# AI Product Listing Generator

Turborepo scaffold for an AI-powered SaaS platform that generates SEO-oriented product listings from product images.

The repository follows the project docs in `docs/`:

- API-first development
- Clean Architecture and SOLID principles
- Feature-based frontend and backend structure
- Version-controlled prompt package
- Docker-ready local infrastructure

Authentication, product uploads, AI product image analysis, and AI listing generation are
implemented for the MVP. Dashboard history, listing detail, and JSON export are also available.

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
- `LOCAL_STORAGE_PATH`
- `PUBLIC_STORAGE_URL`
- `JWT_SECRET_KEY`
- `SESSION_COOKIE_NAME`
- `OPENAI_API_KEY`
- `OPENAI_VISION_MODEL`
- `OPENAI_TEXT_MODEL`
- `OPENAI_TIMEOUT_SECONDS`
- `AI_RETRY_ATTEMPTS`
- `AI_RATE_LIMIT_REQUESTS_PER_MINUTE`
- `AWS_REGION`
- `AWS_S3_BUCKET`

For local authentication, configure the API URL and a long JWT secret:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
JWT_SECRET_KEY=replace-with-a-long-random-local-secret
LOCAL_STORAGE_PATH=storage
PUBLIC_STORAGE_URL=http://localhost:8000/uploads
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_VISION_MODEL=gpt-4.1-mini
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=30
AI_RETRY_ATTEMPTS=3
AI_RATE_LIMIT_REQUESTS_PER_MINUTE=10
```

The backend hashes passwords, persists users in PostgreSQL, and sets an HTTP-only JWT session
cookie named by `SESSION_COOKIE_NAME`.
The analysis workflow sends uploaded image bytes to OpenAI Vision with a version-controlled prompt
from `docs/prompts/product-analysis.md`. The listing workflow uses saved analysis attributes with
`docs/prompts/listing-generator.md`. Both workflows validate structured JSON, store results in
PostgreSQL, and record AI request logs with latency, model, success state, and token usage when
OpenAI returns it.
AI endpoints are protected by per-user rate limiting and return safe error messages for validation,
rate-limit, provider, and persistence failures.

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

For local infrastructure without rebuilding the app containers:

```bash
docker compose up postgres redis
```

If your local Postgres volume already exists, apply schema updates manually:

```bash
docker compose exec postgres psql -U postgres -d ai_product_listing -f /docker-entrypoint-initdb.d/001_auth.sql
docker compose exec postgres psql -U postgres -d ai_product_listing -f /docker-entrypoint-initdb.d/002_product_uploads.sql
```

Visit:

- Login: `http://localhost:3000/login`
- Protected dashboard: `http://localhost:3000/dashboard`
- Product image upload: `http://localhost:3000/dashboard/upload`
- API session check: `http://localhost:8000/api/v1/auth/me`
- API health check: `http://localhost:8000/api/v1/health`

## MVP Demo Flow

1. Start Postgres/Redis and both apps.
2. Register or log in at `http://localhost:3000/login`.
3. Open `http://localhost:3000/dashboard/upload`.
4. Upload a JPG, PNG, or WEBP product image under 10MB.
5. Click **Analyze Product** and review extracted attributes.
6. Click **Generate Listing** and review the generated copy.
7. Open `http://localhost:3000/dashboard` to see listing history.
8. Open a listing detail page, copy individual fields, use **Copy All**, or **Download JSON**.

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

Web checks:

```bash
pnpm --filter @ai-product-listing/web lint
pnpm --filter @ai-product-listing/web typecheck
pnpm --filter @ai-product-listing/web test
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
create the auth `users` table, and `infra/postgres/init/002_product_uploads.sql` to create
`products`, `product_images`, `product_analysis_results`, `generated_listings`, and
`ai_request_logs`.

If you previously ran the Google-auth scaffold, recreate the local Postgres volume so the `users`
table is rebuilt with `password_hash` instead of `google_subject`.

For an existing local Postgres database, run both SQL files manually. The upload API stores local
files in `LOCAL_STORAGE_PATH` and returns image URLs using `PUBLIC_STORAGE_URL`.

## Security Notes

- `OPENAI_API_KEY` is read only by the FastAPI service and must not be exposed through
  `NEXT_PUBLIC_*` variables.
- Product image, analysis, listing, and export APIs require an authenticated session.
- Listing history, detail, and export queries are scoped to the authenticated user's records.
- Uploads validate filename, declared MIME type, size, extension, and basic image file signature.
