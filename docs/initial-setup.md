# Initial Setup Guide

A complete, step-by-step guide to set up the **AI Product Listing Generator** on a fresh machine.
Follow it top to bottom and you will have the full stack (frontend, backend, database) running
locally without surprises.

> **Two ways to run the project:**
> - [Option A — Docker](#option-a--run-everything-with-docker-fastest): one command, everything in containers.
> - [Option B — Local development](#option-b--local-development-setup): run each app directly for hot-reload.
>
> The database schema is created from two SQL files — see
> [Step 5: Set up the database](#step-5-set-up-the-database). This is required for both options when
> using an existing/native database.

---

## 1. Overview

This is a **pnpm + Turborepo monorepo** with a Next.js frontend and a FastAPI backend.

```txt
apps/
  web/      Next.js 15 + TypeScript + Tailwind CSS (frontend)
  api/      FastAPI + SQLAlchemy (async) + asyncpg (backend)
packages/
  ui/       Shared React UI primitives
  types/    Shared TypeScript contracts
  prompts/  Version-controlled AI prompt registry
infra/
  docker/         Dockerfiles for web and api
  postgres/init/  SQL files that create the database schema
docs/       Product, architecture, and engineering specs (and this guide)
```

| Service  | Local port | Purpose                          |
| -------- | ---------- | -------------------------------- |
| Web      | 3000       | Next.js frontend                 |
| API      | 8000       | FastAPI backend (`/api/v1`)      |
| Postgres | 5432       | Primary datastore                |
| Redis    | 6379       | Reserved for caching / rate work |

---

## 2. Prerequisites

Install these before you start:

| Tool                 | Version | Notes                                                                            |
| -------------------- | ------- | -------------------------------------------------------------------------------- |
| **Node.js**          | 22+     | Required by Next.js 15.                                                           |
| **pnpm**             | 9+      | JS package manager (`pnpm@9.15.0` is pinned). Install: `npm install -g pnpm`.     |
| **Python**           | 3.12+   | **Hard requirement** — the backend uses PEP 695 generics, which fail on 3.11 or lower. |
| **PostgreSQL**       | 14+     | A native install, or the bundled Docker service. (Schema is validated on PG 16.) |
| **Docker + Compose** | recent  | Required for Option A; optional but convenient for Postgres/Redis in Option B.   |

Verify versions:

```bash
node --version      # v22.x or higher
pnpm --version      # 9.x or higher
python3 --version   # 3.12.x or higher
```

### Don't have Python 3.12?

The easiest cross-platform way to install it **without sudo** is [`uv`](https://docs.astral.sh/uv/):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

uv python install 3.12
```

---

## 3. Clone the repository & install JS dependencies

```bash
git clone <repository-url> AI-ProductListing
cd AI-ProductListing
pnpm install
```

`pnpm install` installs dependencies for **all** workspace packages (web, api wrappers, ui, types,
prompts).

---

## Option A — Run everything with Docker (fastest)

This brings up web, API, Postgres, and Redis together. **The Postgres container automatically runs
both schema files** (`001_auth.sql`, `002_product_uploads.sql`) the first time its data volume is
created, so you do not need to apply them manually.

```bash
cp .env.example .env        # then edit .env and set OPENAI_API_KEY (at minimum)
docker compose up --build
```

Once running:

- Web: <http://localhost:3000>
- API health: <http://localhost:8000/api/v1/health>
- Login: <http://localhost:3000/login>

> If you change the SQL init files later, the schema is **not** re-applied automatically. Recreate
> the volume: `docker compose down -v && docker compose up --build`.

To run **only** the infrastructure (then run the apps locally via Option B):

```bash
docker compose up postgres redis
```

---

## Option B — Local development setup

Run Postgres + Redis (Docker or native), then run each app directly.

### Step 1: Start Postgres & Redis

Use Docker for just the infra:

```bash
docker compose up postgres redis
```

…or use a natively installed PostgreSQL and Redis. With a native install you must create the
database and apply the schema yourself — see [Step 5](#step-5-set-up-the-database).

### Step 2: Set up the backend (FastAPI) Python environment

The API requires **Python 3.12**. Create its virtual environment **inside `apps/api`**, named
`.venv` (the package scripts expect this exact name/location).

**Using `uv` (recommended):**

```bash
cd apps/api
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
cd ../..
```

**Using the standard library** (if Python 3.12 is already on your `PATH`):

```bash
cd apps/api
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"      # Windows: .venv\Scripts\pip install -e ".[dev]"
cd ../..
```

### Step 3: Create environment files

There are **three** env files. Copy each from its example, then fill in values:

```bash
cp .env.example .env                        # repo root (used by Docker)
cp apps/api/.env.example apps/api/.env      # read by the API when run locally
cp apps/web/.env.example apps/web/.env.local
```

> **Important:** when you run the API locally with `uvicorn` from `apps/api`, FastAPI loads
> `apps/api/.env` (relative to its working directory) — **not** the root `.env`. Put your local API
> values in `apps/api/.env`.

### Step 4: Configure the key variables

| Variable                   | File          | Example / Notes                                                         |
| -------------------------- | ------------- | ----------------------------------------------------------------------- |
| `DATABASE_URL`             | apps/api/.env | `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_product_listing` — **must** use the `postgresql+asyncpg://` prefix. |
| `OPENAI_API_KEY`           | apps/api/.env | Required for all AI features. Backend-only — never expose via `NEXT_PUBLIC_*`. |
| `API_CORS_ORIGINS`         | apps/api/.env | Comma-separated allowed web origins; must include your web URL (default `http://localhost:3000`). |
| `JWT_SECRET_KEY`           | apps/api/.env | Long random string (32+ chars) for local auth.                          |
| `REDIS_URL`                | apps/api/.env | `redis://localhost:6379/0` locally; `redis://redis:6379/0` in Docker.   |
| `LOCAL_STORAGE_PATH`       | apps/api/.env | Folder for uploaded images (default `storage`).                         |
| `PUBLIC_STORAGE_URL`       | apps/api/.env | Public base URL for stored images (default `http://localhost:8000/uploads`). |
| `NEXT_PUBLIC_API_BASE_URL` | apps/web/.env.local | `http://localhost:8000/api/v1` — the only variable the web app needs.   |

> **Connection-string tip:** URL-encode special characters in the DB password
> (`@` → `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`). Use `localhost` as the host for local runs,
> or the service name `postgres` inside Docker.

### Step 5: Set up the database

> **Skip this step if you used Docker for Postgres** (Option A, or `docker compose up postgres`) —
> the schema is applied automatically on first boot.

The complete schema is defined in **two SQL files**, both located in **`infra/postgres/init/`**:

| Order | File                                  | Creates                                                                                                                                              |
| ----- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | `infra/postgres/init/001_auth.sql`         | `users`                                                                                                                                              |
| 2     | `infra/postgres/init/002_product_uploads.sql` | `products`, `product_images`, `product_analysis_results`, `generated_listings`, `ai_request_logs`, `seo_analysis`, `listing_versions`, `marketplace_optimizations`, `enhanced_images`, `generated_images` |

> There is currently **no migration tool** (no Alembic). The schema is applied by running these two
> files **in order** (`001` before `002`).

**A) Native PostgreSQL** — create the database, then apply both files in order:

```bash
# 1. Create the database (name must match the one in your DATABASE_URL)
createdb -h localhost -U postgres ai_product_listing

# 2. Apply the schema files IN ORDER
psql -h localhost -U postgres -d ai_product_listing -f infra/postgres/init/001_auth.sql
psql -h localhost -U postgres -d ai_product_listing -f infra/postgres/init/002_product_uploads.sql
```

You will be prompted for the `postgres` user's password. If your `DATABASE_URL` uses a different
database name, create that name instead and keep the two consistent.

**B) Postgres running in Docker, but you need to (re)apply the files manually** — for example after
editing them on an existing volume:

```bash
docker compose exec -T postgres psql -U postgres -d ai_product_listing < infra/postgres/init/001_auth.sql
docker compose exec -T postgres psql -U postgres -d ai_product_listing < infra/postgres/init/002_product_uploads.sql
```

**Verify the tables were created:**

```bash
psql -h localhost -U postgres -d ai_product_listing -c "\dt"
```

You should see all 11 tables listed above.

### Step 6: Run the apps

From the repo root, run everything with Turborepo:

```bash
pnpm dev
```

…or run each app in its own terminal:

```bash
# Terminal 1 — API (http://localhost:8000)
pnpm --filter @ai-product-listing/api dev

# Terminal 2 — Web (http://localhost:3000)
pnpm --filter @ai-product-listing/web dev
```

---

## 4. Verify the installation

```bash
curl http://localhost:8000/api/v1/health     # -> {"status":"ok","service":"api"}
```

- Open <http://localhost:3000/login> and register a user.
- Interactive API docs (Swagger UI): <http://localhost:8000/docs>

---

## 5. Useful commands

Run from the repo root:

| Command          | What it does                  |
| ---------------- | ----------------------------- |
| `pnpm dev`       | Run all apps (Turborepo).     |
| `pnpm build`     | Build all packages and apps.  |
| `pnpm lint`      | Lint everything.              |
| `pnpm typecheck` | Type-check everything.        |
| `pnpm format`    | Format with Prettier.         |

API-specific (via filter):

```bash
pnpm --filter @ai-product-listing/api lint        # ruff
pnpm --filter @ai-product-listing/api typecheck   # mypy
pnpm --filter @ai-product-listing/api test        # pytest
```

---

## 6. Troubleshooting

**`SyntaxError` on `class X[T: ...]` / `BaseAgent` when starting the API**
Your virtualenv uses Python < 3.12. The backend uses PEP 695 generics. Recreate `.venv` with Python
3.12 (see [Step 2](#step-2-set-up-the-backend-fastapi-python-environment)).

**`ModuleNotFoundError` for an `app...` module**
The editable install didn't run, or ran in the wrong environment. From `apps/api`, re-run
`uv pip install -e ".[dev]"` (or the `pip` equivalent) with `.venv` active.

**Web shows `Module parse failed: Unexpected character '@'` on `@tailwind`**
Next.js inferred the wrong workspace root (commonly caused by a stray `package-lock.json` in your
home directory) and failed to load the Tailwind/PostCSS config. The repo pins the root via
`outputFileTracingRoot` in `apps/web/next.config.ts`. If it recurs, remove any stray
`~/package-lock.json`, delete `apps/web/.next`, and restart.

**`You are using a non-standard "NODE_ENV" value` / dev server misbehaves**
You have `NODE_ENV=production` exported in your shell. `next dev` must run in development mode.
Remove the export from your shell profile (`~/.bashrc` / `~/.zshrc`), or prefix the command:
`NODE_ENV=development pnpm --filter @ai-product-listing/web dev`.

**`EADDRINUSE: address already in use :::3000` (or `:8000`)**
Another process holds the port. Find and stop it: `ss -ltnp | grep ':3000'` then `kill <pid>`
(or `fuser -k 3000/tcp`).

**API fails with `DATABASE_URL is required` or connection refused**
Ensure Postgres is running and `apps/api/.env` has a valid `DATABASE_URL` using the
`postgresql+asyncpg://` prefix. Confirm the database exists and the schema files were applied
([Step 5](#step-5-set-up-the-database)).

**`relation "users" does not exist` (or another missing table)**
The schema files weren't applied, or only `001` ran. Re-run both SQL files in order against the
correct database.

**Env var change not taking effect**
Both servers read env only at startup. Restart the web server after editing `.env.local`, and
restart the API after editing `apps/api/.env` (the `--reload` watcher reacts only to `.py` changes).

---

## 7. Security notes

- `.env` files are gitignored (only `*.env.example` is committed). **Never commit real secrets** —
  especially `OPENAI_API_KEY` and `JWT_SECRET_KEY`. If a secret is ever committed, rotate it.
- `OPENAI_API_KEY` is read only by the backend and must never be exposed through a `NEXT_PUBLIC_*`
  variable.
- All product, analysis, listing, and export APIs require an authenticated session and are scoped to
  the requesting user.
