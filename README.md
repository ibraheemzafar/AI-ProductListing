# AI Product Listing Generator

AI Product Listing Generator is a Turborepo SaaS MVP that turns product images into SEO-ready product listings.

The current demo flow is:

```txt
Upload product images -> Generate AI Assets -> Review listing -> Export
```

The project follows the product and engineering specs in `docs/`, with a Next.js web app, FastAPI API, PostgreSQL, Redis-ready infrastructure, and OpenAI-powered analysis/listing workflows.

## Workspace

```txt
apps/
  web/      Next.js 15, TypeScript, Tailwind CSS
  api/      FastAPI, PostgreSQL, OpenAI integrations
packages/
  ui/       Shared UI primitives
  types/    Shared TypeScript contracts
  prompts/  Prompt registry scaffold
infra/
  postgres/init/  Local schema bootstrap SQL
  docker/         Dockerfiles
docs/             Product, architecture, AI workflow, and standards docs
```

## Prerequisites

- Node.js 22+
- pnpm 9+
- Python 3.12+
- Docker Desktop
- OpenAI API key

## Environment Setup

Copy the environment templates:

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

For local development, use:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_product_listing
REDIS_URL=redis://localhost:6379/0
LOCAL_STORAGE_PATH=storage
PUBLIC_STORAGE_URL=http://localhost:8000/uploads
JWT_SECRET_KEY=replace-with-a-long-random-local-secret
SESSION_COOKIE_NAME=apl_session
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
OPENAI_API_KEY=sk-your-key
OPENAI_VISION_MODEL=gpt-4.1-mini
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1.5
OPENAI_TIMEOUT_SECONDS=30
OPENAI_IMAGE_TIMEOUT_SECONDS=90
AI_RETRY_ATTEMPTS=3
AI_RATE_LIMIT_REQUESTS_PER_MINUTE=10
```

Never commit real secrets. Rotate any key that was committed, pasted, or shared.

## Install

Install JavaScript dependencies:

```bash
pnpm install
```

Create the API virtual environment:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
cd ..\..
```

Start local infrastructure:

```bash
docker compose up postgres redis
```

The first Postgres startup applies SQL files from `infra/postgres/init`.

## Run

Start the full workspace:

```bash
pnpm run dev
```

Useful URLs:

- Web: `http://localhost:3000`
- Login: `http://localhost:3000/login`
- Dashboard: `http://localhost:3000/dashboard`
- Upload: `http://localhost:3000/dashboard/upload`
- Web health page: `http://localhost:3000/health`
- Web health JSON: `http://localhost:3000/api/health`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/api/v1/health`

## Demo Flow

1. Open `http://localhost:3000/login`.
2. Register a demo account or sign in.
3. Open `Dashboard -> Upload`.
4. Upload JPG, PNG, or WEBP product images under 10MB.
5. Click `Generate AI Assets`.
6. Wait for the workflow progress to complete:
   `Upload complete`, `Analyzing product`, `Generating listing`, optional optimization/image steps, and `Finalizing assets`.
7. Open the generated listing from the dashboard.
8. Review the tabbed AI workspace:
   `Overview`, `Listing`, `Images`, `Marketplace`, `Marketing`, `Versions`.
9. Copy listing content or export JSON from the listing detail page.

For a stable demo, keep optional image generation off unless the OpenAI image model is configured and you expect the extra latency.

## Quality Checks

Run web checks:

```bash
pnpm --filter @ai-product-listing/web lint
pnpm --filter @ai-product-listing/web typecheck
pnpm --filter @ai-product-listing/web test
```

Run API checks:

```bash
pnpm --filter @ai-product-listing/api lint
pnpm --filter @ai-product-listing/api typecheck
pnpm --filter @ai-product-listing/api test
```

Run all workspace checks:

```bash
pnpm lint
pnpm typecheck
pnpm build
```

## Launch Readiness Notes

The app includes:

- Protected dashboard routes via session cookie middleware.
- API route protection through `get_current_user`.
- User-scoped listing, upload, export, generated image, and optimization queries.
- Upload validation for file count, extension, MIME type, file size, empty files, path separators, and image signatures.
- OpenAI retry handling, timeouts, structured output validation, and safe user-facing failure messages.
- JSON health endpoints for web and API.
- Polished empty, loading, and error states for the primary dashboard flow.

## Production Checklist

Before deployment:

- Set `ENVIRONMENT` to a non-local value.
- Use a strong `JWT_SECRET_KEY`.
- Set `SESSION_COOKIE_SECURE=true`.
- Use HTTPS origins in `API_CORS_ORIGINS`.
- Configure production `DATABASE_URL` and run migrations/schema setup.
- Configure durable object storage instead of local disk if uploads must persist across deploys.
- Set `PUBLIC_STORAGE_URL` to the deployed asset URL.
- Configure `OPENAI_API_KEY` and model names.
- Confirm API health: `/api/v1/health`.
- Confirm web health: `/api/health` and `/health`.
- Verify register/login/logout.
- Verify image upload validation with invalid file type and oversized file.
- Verify `Generate AI Assets` with a small product image.
- Verify dashboard listing history search/filter.
- Verify listing detail tabs, JSON export, image download/delete if image generation is enabled.
- Check browser console for missing chunks or runtime errors after a clean build.

## Troubleshooting

If browser console shows missing `/_next/static/chunks/...` files, stop duplicate Next dev servers, delete `apps/web/.next`, and restart `pnpm run dev`.

If login works but dashboard redirects back to login, confirm `SESSION_COOKIE_NAME` matches in web and API env files.

If OpenAI calls fail, check `OPENAI_API_KEY`, model access, and API server logs. User-facing messages should remain safe and retryable.

If uploads fail, confirm the API is running, `LOCAL_STORAGE_PATH` is writable, and the image is JPG, PNG, or WEBP under 10MB.

## Security Notes

- Keep `OPENAI_API_KEY` server-side only. Do not expose it through `NEXT_PUBLIC_*`.
- Product images, analysis, listings, exports, image generation, and marketplace routes require authentication.
- Listing and asset repositories scope reads and writes to the authenticated user.
- Do not enable production with development secrets.
