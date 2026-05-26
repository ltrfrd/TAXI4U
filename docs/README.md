# Taxi4U

Taxi fleet management and ride-request platform for Cochrane, Alberta.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + PostgreSQL |
| Background | ARQ + Redis |
| Maps | Google Maps API |
| Notifications | Firebase FCM |

## Setup

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your values

# 2. Build and start services
make build
make up

# 3. Run migrations
make migrate
```

## Development

```bash
# Hot-reload backend
make dev

# View logs
make logs
make worker-logs

# Open shell in backend container
make shell
```

## Project Structure

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design.

See [docs/ROADMAP.md](docs/ROADMAP.md) for the development plan.
