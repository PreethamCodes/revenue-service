# revenue-service

Revenue portal and SOAP 1.2 certificate service.

## Simulated provider backend

Copy .env.example to .env and supply a department-scoped DATABASE_URL (postgresql+psycopg://...) and REVENUE_USER, REVENUE_PASSWORD. Use synthetic data only. Use TLS for any connection outside isolated local development. See the versioned contract under contracts for the exact response shape.

From this folder, after preparing and seeding its database:

```powershell
python -m pip install -r requirements-test.txt
docker build -t revenue-backend .
docker run --rm --env-file .env -p 127.0.0.1:8001:8001 revenue-backend
```

Use a database address reachable from the container. GET /health tests a read from the department schema and returns 503 when unavailable. The separate department frontend is in frontend/. For native development set the same variables in the shell, then run `python -m uvicorn app:app --port 8001 --no-access-log`. Run `python -m pytest tests` against a seeded synthetic database. Tests exercise a real refused connection for the outage case. Structured request logs omit request bodies, query strings, identifiers and credentials.

## Database

Install requirements-db.txt in a local virtual environment. Set MIGRATION_DATABASE_URL to a confirmed PostgreSQL SQLAlchemy URL (postgresql+psycopg://...) supplied through the environment. From this directory run `alembic upgrade head` and `alembic current`. Apply db/seed.sql only to a synthetic environment with psql. Runtime credentials must be scoped to the revenue schema. The migration identity needs schema creation and role administration privileges.

## Department portal

The independent Next.js/TypeScript portal runs on port 3001. From frontend/, copy .env.example to .env.local. Set BACKEND_URL to the reachable Phase 2 provider (native default in the template: http://localhost:8001), populate its service credentials, and set PORTAL_DEMO_ACCESS=enabled for a local read-only synthetic demo. This explicit operator switch grants demo visitors lookup access. It is unsuitable as staff identity authentication.

```powershell
npm ci
npm run dev
```

Alternatively, from frontend/ run `docker build -t revenue-portal .`, then `docker run --rm --env-file .env.local -p 127.0.0.1:3001:3001 revenue-portal`. Configure a container-reachable BACKEND_URL in that environment. For Docker Desktop with a host-exposed provider use http://host.docker.internal:8001. GET /health checks portal liveness. A successful lookup verifies the provider path. Do not put service credentials in NEXT_PUBLIC variables. The portal has no database or signing credentials.
