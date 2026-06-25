# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI-powered SaaS that generates SEO-optimized product listings from uploaded product images.
**pnpm + Turborepo monorepo**: a Next.js 15 frontend (`apps/web`) and a FastAPI backend
(`apps/api`), with shared packages (`packages/ui`, `packages/types`, `packages/prompts`).

`AGENTS.md` mandates spec-driven development: read the relevant specs in `docs/` (vision,
product-spec, mvp-scope, architecture, engineering-principles, code-standards, system-boundaries)
before implementing a feature. Note that `AGENTS.md`'s "do not implement" list (e.g. marketplace
optimization, multi-agent) is **stale** — those features now exist in `app/features/` and
`app/agents/`.

## Commands

Run from the repo root unless noted. The API package scripts shell out to `apps/api/.venv`, so that
virtualenv must exist first (see `docs/initial-setup.md`).

| Task | Command |
| --- | --- |
| Run everything (web + api) | `pnpm dev` |
| Run one app | `pnpm --filter @ai-product-listing/web dev` / `... /api dev` |
| Lint / typecheck / build all | `pnpm lint` · `pnpm typecheck` · `pnpm build` |
| API lint (ruff) / types (mypy) / tests (pytest) | `pnpm --filter @ai-product-listing/api {lint,typecheck,test}` |
| Web tests | `pnpm --filter @ai-product-listing/web test` |

**Single backend test:** from `apps/api`, `.venv/bin/python -m pytest tests/path_test.py::test_name`.

**Python 3.12 is a hard requirement** — the backend uses PEP 695 generic syntax (e.g.
`class BaseAgent[InputT: BaseModel, OutputT: BaseModel]`) which is a `SyntaxError` on 3.11 and
below. Create the venv with `uv venv --python 3.12 .venv && uv pip install -e ".[dev]"` inside
`apps/api`.

## Backend architecture (`apps/api`)

**Feature-sliced clean architecture.** Each slice in `app/features/<feature>/` follows the same
layering, and this is the pattern to mirror when adding features:

- `router.py` — thin FastAPI controllers; only DI + delegation, no business logic.
- `services.py` — business logic; the source of truth.
- `repositories.py` — data access via async SQLAlchemy.
- `dependencies.py` — FastAPI DI wiring that assembles a service from its repository (built with an
  `AsyncSession`) and any shared providers.
- `models.py` (ORM), `schemas.py` (Pydantic I/O), `prompts.py`, `openai_client.py`.

`app/api/v1/router.py` aggregates every feature router under the `/api/v1` prefix.

**Cross-cutting infrastructure:**
- `app/core/` — `config.py` (pydantic-settings `Settings`), `security.py`, `rate_limit.py`
  (`enforce_ai_rate_limit`, applied as a router dependency on AI endpoints), `errors.py` (`AppError`
  base) and `error_middleware.py` (centralized handlers + request logging), `logging.py`.
- `app/infrastructure/database.py` — async engine + `async_sessionmaker`, the declarative `Base`,
  and the `get_database_session` DI generator. Sessions are injected, never created in services.
- `app/shared/storage/` — `StorageProvider` Protocol with a `LocalStorageProvider` implementation;
  injected via `get_storage_provider`. Local files live under `LOCAL_STORAGE_PATH` and are served at
  `/uploads` (public base = `PUBLIC_STORAGE_URL`). `AWS_REGION`/`AWS_S3_BUCKET` settings exist but no
  S3 provider is implemented yet.

**Agents (`app/agents/`):** `BaseAgent[InputT, OutputT]` is a generic ABC wrapping a service-backed
`run()` with timing, structured logging, error capture into `WorkflowState`, and execution
recording. Agents can also run as OpenAI Agents SDK tools via `execute_with_openai_agents_sdk()` —
but the application **service remains the source of truth**; the SDK agent merely delegates to it.

**Request flow:** controller `Depends(get_<x>_service)` → service holds repository + providers →
authenticated via `get_current_user`; AI routes additionally gated by `enforce_ai_rate_limit`. AI
workflows validate structured JSON before persistence and log latency/model/token usage to
`ai_request_logs`.

## Frontend architecture (`apps/web`)

Next.js 15 **App Router**. Routes in `app/` (`login`, `dashboard/upload`, `dashboard/listings`).
`middleware.ts` guards `/dashboard/*` by checking the `apl_session` cookie and redirecting to
`/login`. API calls go through `lib/api`; UI primitives in `components/ui`. `next.config.ts`
`transpilePackages` the shared `ui`/`types` packages and pins `outputFileTracingRoot` to the repo
root (a stray `~/package-lock.json` otherwise misleads Next's root detection and breaks
Tailwind/PostCSS). The only env var the web app needs is `NEXT_PUBLIC_API_BASE_URL`.

## Database

**No migration tool (no Alembic).** The schema is defined by two SQL files in
`infra/postgres/init/`, applied **in order**: `001_auth.sql` (users) then
`002_product_uploads.sql` (all other tables). Docker's Postgres runs them automatically on first
volume creation; for a native DB apply them manually (see `docs/initial-setup.md`). ORM models in
the codebase are not authoritative for schema creation — keep models and these SQL files in sync.

`DATABASE_URL` **must** use the async driver prefix `postgresql+asyncpg://`.

## Environment & gotchas

- **Three env files:** root `.env` (Docker), `apps/api/.env`, `apps/web/.env.local`. Running the API
  locally with `uvicorn` from `apps/api` loads `apps/api/.env` (CWD-relative) — **not** the root
  `.env`. `OPENAI_API_KEY` is backend-only; never expose via `NEXT_PUBLIC_*`.
- Both servers read env only at startup — restart after changing env files. The API's `--reload`
  reacts only to `.py` changes.
- `next dev` must not run with `NODE_ENV=production` in the shell, or CSS/dev behavior breaks.

See `docs/initial-setup.md` for full machine setup and troubleshooting.
