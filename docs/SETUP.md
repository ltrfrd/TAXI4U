# SETUP — Local Development Environment

This document covers everything needed to run the backend locally on Windows.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12 | Use python.org installer |
| Docker Desktop | Latest | For PostgreSQL and Redis |
| Git | Latest | — |
| VS Code | Latest | Recommended editor |

---

## Stack (Local)

| Component | How It Runs Locally |
|---|---|
| PostgreSQL 16 | Docker container |
| Redis 7 | Docker container |
| FastAPI app | Local venv via uvicorn |
| ARQ worker | Local venv |

---

## First-Time Setup

### 1 — Clone the repo

```bash
git clone https://github.com/your-repo/taxi4u.git
cd taxi4u
```

### 2 — Start Docker services

From the project root (where `docker-compose.yml` lives):

```bash
docker-compose up -d db redis
```

This starts PostgreSQL and Redis only. The FastAPI app and ARQ worker run locally in your venv — not in Docker — so code changes take effect immediately without rebuilding.

Verify they're running:

```bash
docker-compose ps
```

Both `db` and `redis` should show `running`.

### 3 — Create the virtual environment

```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### 5 — Configure environment variables

Copy the example env file:

```bash
copy .env.example .env
```

Edit `.env` and fill in the required values:

```env
# Database — matches docker-compose.yml
DATABASE_URL=postgresql://taxi4u:taxi4u@localhost:5432/taxi4u

# Redis — matches docker-compose.yml
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Google Maps
GOOGLE_MAPS_API_KEY=your-key-here

# Firebase FCM
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# Environment
ENVIRONMENT=development
```

### 6 — Apply database migrations

```bash
alembic upgrade head
```

### 7 — Seed the database

```bash
python scripts/seed_all.py
```

This seeds:
- 26 Cochrane zones
- Fare matrix
- Calgary Airport special route ($90 fixed)
- Default admin account

### 8 — Create your admin user

```bash
python scripts/create_admin.py
```

Follow the prompts to set the admin email and password.

---

## Running the App

Open two terminals, both with the venv activated (`venv\Scripts\activate`).

**Terminal 1 — FastAPI app:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`--reload` restarts the server automatically when you save a file.

**Terminal 2 — ARQ worker:**

```bash
arq app.background.worker.WorkerSettings
```

The worker must be running for:
- Auto-assignment retries
- Standby charge timer
- Scheduled trip flagging

---

## Verifying the Setup

Once both terminals are running:

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health (if implemented)

Log in via `POST /auth/login` with your admin credentials to confirm the full stack is working.

---

## Connecting pgAdmin to Docker PostgreSQL

If you want a visual database browser:

1. Open pgAdmin
2. Add a new server with these settings:
   - Host: `localhost`
   - Port: `5432`
   - Database: `taxi4u`
   - Username: `taxi4u`
   - Password: `taxi4u`

---

## Daily Workflow

```bash
# Start Docker services (if not already running)
docker-compose up -d db redis

# Activate venv
cd backend
venv\Scripts\activate

# Start app (Terminal 1)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start worker (Terminal 2)
arq app.background.worker.WorkerSettings
```

---

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Single file
pytest tests/unit/services/test_trip_service.py

# Verbose output
pytest -v
```

Tests use a separate test database. Make sure the test database is configured in your `.env` or test config before running integration tests.

---

## Stopping the Environment

```bash
# Stop Docker services
docker-compose down

# Stop FastAPI and ARQ — Ctrl+C in each terminal
```

To stop Docker and wipe the database volume (full reset):

```bash
docker-compose down -v
```

---

## Resetting the Dev Database

```bash
python scripts/reset_dev_db.py
```

This drops and recreates the database, applies all migrations, and re-runs seeds. Use when the local DB gets into a bad state.

---

## Troubleshooting

**`psql` not recognized** — PostgreSQL CLI is not in your PATH. Use pgAdmin for database inspection instead, or connect via Docker:

```bash
docker-compose exec db psql -U taxi4u -d taxi4u
```

**Port 5432 already in use** — Your local PostgreSQL installation is running on the same port as the Docker container. Stop your local PostgreSQL service via Windows Services, or change the Docker port in `docker-compose.yml` to `5433:5432` and update `DATABASE_URL` accordingly.

**Redis connection refused** — Docker Desktop may not be running. Start Docker Desktop, then:

```bash
docker-compose up -d redis
```

**ARQ worker not processing jobs** — Confirm Redis is running and `REDIS_URL` in `.env` matches the Docker Redis port.
