# Learning Space — Phase 1 Learning Tracker

A Next.js App Router / TypeScript frontend and a FastAPI / SQLAlchemy backend. PostgreSQL stores business records and certificate metadata; private S3-compatible storage holds certificate files. Manual authentication uses Argon2id, JWT access cookies, rotating opaque refresh tokens and session-bound CSRF tokens.

The UI uses `#4F2D7F`, `#DEDAD6` and `#FFFFFF`. Every page has its own `frontend/app/**/page.tsx`. There is no single `app.js` and no external authentication provider.

## Scope

Manager: employees, courses, ordered learning tracks, assignments, corrections, certificates, team dashboards, capability signals and audit history.

Employee: personal dashboard, learning list/history, permitted progress updates, completion and certificate uploads/downloads.

**No Phase 2 functionality is implemented.** No LMS integration, CSV/Excel processing, staging or import reports.

## Quick start with Docker

Prerequisites: Docker Engine/Desktop with Compose. Node 22+ and Python 3.11+ are needed only for native development.

1. Run `python scripts/init_dev.py` to create `.env` with independent random secrets (existing files are preserved). Alternatively copy `.env.example` and replace every secret. Use URL-safe secrets for the database connection URL. Never commit `.env`.
2. Run from the repository root:

```sh
docker compose up -d --build
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python -m app.scripts.create_manager
```

The bootstrap command interactively requests name, email and a password of at least 12 characters. It hashes the password and refuses to run if a manager already exists. **No default login is created.**

Open `http://localhost:3000`. Development OpenAPI documentation: `http://localhost:8000/api/docs`. MinIO console: `http://localhost:9001`, using the storage credentials you configured.

The development stack includes PostgreSQL, Redis (shared authentication rate limiting), MinIO and private bucket initialization. MinIO server and client images are built from pinned official Go source versions in `docker/object-storage/Dockerfile`; they do not depend on the unavailable `minio/minio` or `minio/mc` Docker Hub images. The first build downloads Go dependencies and can take several minutes. This emulator is for local development; production should use a maintained S3-compatible service. API processes do not create tables automatically; apply migrations explicitly. Docker volumes preserve records and evidence.

Stop with `docker compose down`. Removing volumes would erase development records and evidence; ordinary shutdown keeps them.

### Docker startup troubleshooting on Windows

If a pull reports `minio/minio` or `minio/mc` access denied, use the current Compose file: both storage services now build from official source instead of pulling those images. Retry `docker compose up -d --build`.

If Docker reports `read-only file system` under `/var/lib/desktop-containerd` or `/var/lib/docker`, check free space on the Windows drive holding Docker's disk image. Free space or move the disk image using Docker Desktop's supported Settings > Resources > Advanced > Disk image location control, then restart Docker Desktop and retry. Do not move its live virtual disk manually or reset/delete volumes to fix this; volumes hold application data. Allow several GB for image layers and source builds.

Run `docker compose ps -a` after startup. Apply migrations and run manager bootstrap only once the backend is running. An `Exited (0)` storage-init container is expected: it creates the private bucket and finishes.

If a frontend build reports missing `.next/standalone` or `.next/static`, inspect the build output: `npm ci` and `next build` should produce normal installation/compilation logs. A disk-full failure can leave corrupted local image files. The frontend uses `node:22-bookworm-slim` and verifies build artifacts before copying them to the runtime image. Rebuild with `docker compose build --pull frontend`; do not remove application volumes as part of image recovery.

## Native development

Start backing services:

```sh
docker compose up -d --build postgres redis minio storage-init
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
```

Edit `backend/.env`: match the root database and storage secrets, set a random JWT secret and retain the local endpoints. Run these from `backend`:

```powershell
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe -m app.scripts.create_manager
../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

In a second terminal, from `frontend`:

```powershell
npm.cmd ci
npm.cmd run dev
```

On macOS/Linux use `.venv/bin/python`, and `npm` instead of `npm.cmd`. Do not run a native API on port 8000 while the Docker API occupies it.

For development without object storage, set `STORAGE_BACKEND=local`, `STORAGE_ROOT=.storage`. This adapter writes files outside PostgreSQL and serves them only through authorized downloads. Production requires S3. SQLite is used for unit tests only; PostgreSQL is the deployment database.

## Verification commands

From `backend`:

```powershell
../.venv/Scripts/python.exe -m pytest
../.venv/Scripts/python.exe -m alembic check
```

From `frontend`:

```powershell
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
```

PostgreSQL integration verification (isolated temporary database required):

```sh
docker compose exec backend python -m pytest
docker compose exec backend python -m alembic check
```

The ordinary pytest suite uses isolated SQLite databases; it validates application behavior but does not prove PostgreSQL concurrency behavior. See `docs/verification.md` for PostgreSQL-specific checks and manual browser workflows.

Browser tests start isolated API/frontend servers on ports 8100/3100, generate random test credentials and use a new test database under `backend/.browser-tests`. They never seed the configured business database. Install Chromium with `npx playwright install chromium` before the first browser run, or use an installed Edge browser with `$env:PLAYWRIGHT_CHANNEL='msedge'` on Windows. The harness requires the root `.venv` with backend dependencies.

## Repository map

```text
backend/app/api/routes/       HTTP contracts and dependencies
backend/app/services/         Business rules, authorization, transactions, audit
backend/app/repositories/     Database lookup and paginated queries
backend/app/models/           SQLAlchemy constraints and entities
backend/app/schemas/          Pydantic request validation
backend/app/storage/          S3 and development storage adapters
backend/app/core/             Settings, password/token security, rate limits
backend/alembic/              Versioned schema migrations
backend/tests/                Workflow and authorization tests
frontend/app/                 Separate route files and protected layouts
frontend/components/          Feature screens and reusable UI
frontend/services/api.ts      Central API client and serialized token refresh
frontend/lib/server-auth.ts   Server-side protected-route session checks
docs/                         Architecture, API, security, verification
```

## Production configuration

This repository supplies a development Compose stack, not an unattended production deployment. Before deployment:

- Set `APP_ENV=production`, `COOKIE_SECURE=true`, `PUBLIC_ORIGIN=https://your-host` and strong secrets through your secret manager.
- Serve Next.js and `/api` under one HTTPS origin; restrict API and backing services to private networking. Preserve `Origin` and cookie headers through proxies. Apply a request-body limit of 11 MiB at the edge.
- Use a non-superuser database runtime role with no schema-alter privileges and no audit update/delete privileges; use a separate migration role. The migration adds an audit append-only trigger.
- Configure a private object bucket and a scoped object-storage identity. Prefer cloud workload credentials in production over static keys.
- Provision shared Redis, database/object backups, retention rules, health monitoring and TLS termination. Pin infrastructure images to approved digests for deployment.
- Adjust the frontend CSP to use nonce-based scripts and remove development `unsafe-eval` when deploying behind your selected ingress. The included policy blocks objects, framing, off-origin forms and connections but retains Next.js-compatible inline scripts.
- Run PostgreSQL integration/concurrency tests and browser verification in your target environment. PDF signature validation is not a malware scanner; enable your organization’s object scanning/quarantine if its policy requires it.

See `docs/security.md` for controls and operational limitations. Authentication and authorization are always enforced by FastAPI.
