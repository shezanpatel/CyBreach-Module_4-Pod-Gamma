# Redis Leaderboard Backend

Containerized Redis-backed leaderboard service using FastAPI, Redis 7, and PostgreSQL 16.

## Features

- Redis-backed leaderboard operations
- FastAPI REST API
- Tenant and consent validation
- Improvement rankings
- PostgreSQL leaderboard snapshots
- Historical tenant anonymization
- Docker Compose deployment
- Health checks
- Pytest test suite

## Requirements

- Git
- Docker Desktop
- Docker Compose
- Python 3.13+

Check installation:

```powershell
git --version
docker --version
docker compose version
python --version
```

## Clone

```powershell
git clone https://github.com/shezanpatel/CyBreach-Module_4-Pod-Gamma.git
cd CyBreach-Module_4-Pod-Gamma
git checkout feature/gamma-redis-core
```

## Project Structure

```text
app/
  api/leaderboard.py
  models/schemas.py
  services/improvement_service.py
  tenant_contract.py
  main.py
database/
  001_sanitize_leaderboard_snapshot.sql
  002_create_leaderboard_snapshot.sql
  redis.conf
tests/
Dockerfile
docker-compose.yml
.env.example
requirements.txt
README.md
```

## Environment Setup

Create the local environment file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Example configuration:

```env
APP_NAME=Redis Leaderboard Engine
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password_here
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5.0
REDIS_SOCKET_CONNECT_TIMEOUT=5.0
REDIS_LEADERBOARD_KEY=leaderboard:global

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=leaderboard
POSTGRES_USER=leaderboard_user
POSTGRES_PASSWORD=your_postgres_password_here

API_KEY=your_api_key_here
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_PER_MINUTE=20
```

Never commit `.env`. Keep real passwords and API keys out of `.env.example`.

## Docker Setup

Start all services:

```powershell
docker compose up -d
```

Build and start:

```powershell
docker compose up -d --build
```

Services:

| Service | Container | Port |
|---|---|---:|
| Redis | redis-leaderboard-redis | 6379 |
| PostgreSQL | gamma-postgres | 5432 |
| FastAPI | redis-leaderboard-api | 8000 |

Check containers:

```powershell
docker ps
```

View logs:

```powershell
docker compose logs -f fastapi
docker compose logs -f redis
docker compose logs -f postgres
```

Stop containers without deleting data:

```powershell
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete Redis and PostgreSQL data.

## FastAPI

API base URL:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

Health check:

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
```

Expected response:

```json
{"status":"healthy","redis":"connected","app":"running"}
```

Alternatively:

```powershell
curl.exe http://localhost:8000/health
```

## Redis Verification

```powershell
docker exec -it redis-leaderboard-redis redis-cli -a "YOUR_REDIS_PASSWORD" ping
```

Expected:

```text
PONG
```

Redis configuration is stored in:

```text
database/redis.conf
```

## PostgreSQL Verification

Connect:

```powershell
docker exec -it gamma-postgres psql -U leaderboard_user -d leaderboard
```

Check connection:

```powershell
docker exec -it gamma-postgres psql -U leaderboard_user -d leaderboard -c "SELECT current_database(), current_user, version();"
```

Check schema:

```powershell
docker exec -it gamma-postgres psql -U leaderboard_user -d leaderboard -c "\d leaderboard_snapshot"
```

The snapshot table contains:

- snapshot_id
- tenant_id
- dimension
- dimension_value
- score
- delta
- rank
- snapshot_date

## Database Scripts

Create the snapshot table using:

```text
database/002_create_leaderboard_snapshot.sql
```

The operational anonymization script is:

```text
database/001_sanitize_leaderboard_snapshot.sql
```

Example anonymization:

```sql
BEGIN;

UPDATE leaderboard_snapshot
SET tenant_id = 'ANON-' || substr(md5(tenant_id), 1, 16)
WHERE tenant_id = 'CORP-001';

COMMIT;
```

The anonymization preserves historical ranking fields.

## Local Python Setup

Docker is recommended. For local execution:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start FastAPI:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

For local execution use:

```env
REDIS_HOST=localhost
POSTGRES_HOST=localhost
```

Inside Docker Compose, use:

```env
REDIS_HOST=redis
POSTGRES_HOST=postgres
```

## Tests

Run all tests:

```powershell
python -m pytest -q
```

Run a specific test file:

```powershell
python -m pytest tests/test_improvement.py -v
```

## Functional Verification

```powershell
docker ps
docker compose config
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
docker exec -it gamma-postgres psql -U leaderboard_user -d leaderboard -c "SELECT current_database(), current_user;"
python -m pytest -q
```

The expected test result is all tests passing.

## Troubleshooting

### Redis healthcheck fails

```powershell
docker compose logs redis
docker compose restart redis
```

Confirm that the password in `.env` and `database/redis.conf` is consistent.

### PostgreSQL is not ready

```powershell
docker compose logs postgres
docker compose restart postgres
```

### Port conflict

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :6379
netstat -ano | findstr :5432
```

### FastAPI cannot connect to services

Inside Docker, use service names `redis` and `postgres`, not `localhost`.

### PowerShell curl warning

Use:

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
```

or:

```powershell
curl.exe http://localhost:8000/health
```

## Git Workflow

```powershell
git status
git add README.md
git commit -m "docs: update docker and environment setup"
git push team-main feature/gamma-redis-core
```

Do not stage `.env`.

## Production Notes

Before production:

- Replace all development passwords.
- Remove hard-coded secrets from Compose files.
- Use Docker secrets or a secret manager.
- Restrict Redis and PostgreSQL network access.
- Enable HTTPS/TLS.
- Configure production CORS.
- Use strong API keys.
- Add backups, monitoring, and centralized logging.

## License

Developed as part of the CyBreach Module 4 Pod Gamma project.
