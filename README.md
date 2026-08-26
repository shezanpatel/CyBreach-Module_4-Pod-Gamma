# Redis Leaderboard Backend — Pod Gamma

## Overview

This branch contains the **Redis Leaderboard Backend** for the CyBreach Module 4 Pod Gamma project.

The backend is responsible for Redis-based leaderboard storage and operations, including:

- Redis connection management
- Connection pooling
- Redis Sorted Set (ZSET) leaderboard operations
- Player score management
- Player ranking
- Improvement-based ranking
- Tenant/consent contract handling
- Input validation
- Database snapshot/migration support
- Automated testing
- Structured logging and performance-oriented operations

The backend is designed to be consumed by the API layer rather than tightly coupling Redis implementation details to the API.

---

# What I Implemented

The `feature/gamma-redis-core` branch contains the Redis backend work completed for this module.

### Core Redis functionality

The backend provides:

- Redis client and connection management
- Redis authentication through environment variables
- Connection pooling
- Leaderboard storage using Redis Sorted Sets (`ZSET`)
- Score insertion and updates
- Score increment operations
- Leaderboard retrieval
- Player rank retrieval
- Player deletion
- Leaderboard reset

### Improvement ranking

An improvement-ranking service was added through:

```text
app/services/improvement_service.py
```

This provides functionality for calculating and retrieving leaderboard improvement information rather than relying only on absolute leaderboard scores.

### Tenant contract / consent

Tenant-related contract handling was added through:

```text
app/tenant_contract.py
```

This provides the contract layer required for tenant-specific behavior and consent handling.

### Database changes

Two database SQL scripts were added:

```text
database/001_sanitize_leaderboard_snapshot.sql
database/002_create_leaderboard_snapshot.sql
```

These provide database-side support for leaderboard snapshot handling.

### Testing

Additional improvement-ranking tests were added:

```text
tests/test_improvement.py
```

The current test suite passes successfully.

---

# Project Structure

```text
pod-gamma-platform/
│
├── app/
│   ├── api/
│   │   └── leaderboard.py
│   ├── db/
│   │   └── redis_client.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── leaderboard_service.py
│   │   └── improvement_service.py
│   ├── utils/
│   │   ├── benchmark.py
│   │   └── logger.py
│   ├── tenant_contract.py
│   ├── config.py
│   ├── exceptions.py
│   └── main.py
│
├── database/
│   ├── 001_sanitize_leaderboard_snapshot.sql
│   └── 002_create_leaderboard_snapshot.sql
│
├── tests/
│   ├── test_leaderboard.py
│   ├── test_improvement.py
│   └── ...
│
├── docs/
│   ├── integration_guide.md
│   └── redis_module.md
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

---

# Architecture

```text
             API Layer
                 │
                 ▼
        ┌──────────────────┐
        │ Leaderboard API  │
        │ leaderboard.py   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Service Layer    │
        │                  │
        │ Leaderboard      │
        │ Improvement      │
        └────────┬─────────┘
                 │
          ┌──────┴──────┐
          ▼             ▼
      Redis ZSET     Tenant Contract
          │
          ▼
    Leaderboard Data
```

The API layer does not need to directly implement Redis commands. It can call the service layer.

---

# Redis Leaderboard

The leaderboard uses a Redis **Sorted Set (`ZSET`)**.

Conceptually:

```text
leaderboard:global

player_1 → 150
player_2 → 125
player_3 → 100
```

The Redis score determines the player's position in the leaderboard.

The service layer supports:

```text
LeaderboardService.set_score()
LeaderboardService.increment_score()
LeaderboardService.get_top_players()
LeaderboardService.get_rank()
LeaderboardService.delete_user()
LeaderboardService.reset_leaderboard()
```

---

# Improvement Ranking

In addition to absolute leaderboard scores, the backend contains an improvement-ranking service.

Implementation:

```text
app/services/improvement_service.py
```

The purpose is to allow the application to distinguish between current performance and improvement over time, rather than treating leaderboard position as the only measure of progress.

---

# Tenant Contract and Consent

Tenant-specific behavior is separated into:

```text
app/tenant_contract.py
```

This provides a contract layer for handling tenant-related requirements and consent information.

The goal is to keep tenant-specific rules separate from the underlying Redis implementation.

---

# Database Migrations

The branch contains:

### 001 — Sanitize leaderboard snapshot

```text
database/001_sanitize_leaderboard_snapshot.sql
```

### 002 — Create leaderboard snapshot

```text
database/002_create_leaderboard_snapshot.sql
```

Apply these according to the database setup used by the complete Pod Gamma deployment.

---

# Configuration

Create a local `.env` file based on `.env.example`.

Example:

```env
APP_NAME=Redis Leaderboard Engine
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
REDIS_SOCKET_TIMEOUT=5.0
REDIS_SOCKET_CONNECT_TIMEOUT=5.0
REDIS_MAX_CONNECTIONS=50
REDIS_LEADERBOARD_KEY=leaderboard:global

API_KEY=your_api_key
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_PER_MINUTE=20
```

**Do not commit `.env` or real credentials to Git.**

---

# Running the Project

## 1. Clone the repository

```powershell
git clone https://github.com/shezanpatel/CyBreach-Module_4-Pod-Gamma.git
cd CyBreach-Module_4-Pod-Gamma
git checkout feature/gamma-redis-core
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

---

# Start Redis

Start the Docker services:

```powershell
docker compose up -d
```

Check the containers:

```powershell
docker compose ps
```

---

# Configure Environment Variables

For local PowerShell development:

```powershell
$env:API_KEY="dev-test-api-key"
$env:REDIS_PASSWORD="StrongRedisPassword123!"
```

Verify:

```powershell
echo $env:API_KEY
echo $env:REDIS_PASSWORD
```

For persistent local configuration, use `.env`.

---

# Run the Application

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Application:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

# Run Tests

Run the complete test suite:

```powershell
python -m pytest -q
```

Current verification:

```text
37 passed
1 warning
```

The warning is a Starlette/httpx test-client deprecation warning and does not currently cause test failure.

---

# Testing Workflow

After making changes:

```powershell
python -m pytest -q
git status
git diff --cached --check
```

The working tree should be clean after committing.

---

# Git Branch

The Redis backend implementation is maintained on:

```text
feature/gamma-redis-core
```

The branch contains the Redis backend work and the tenant/improvement-ranking implementation.

It can later be merged into the team's main integration branch when the other Pod Gamma components are ready.

---

# Integration With the API Team

The API layer should use the service layer rather than directly accessing Redis.

The service layer exposes:

```text
LeaderboardService.set_score()
LeaderboardService.increment_score()
LeaderboardService.get_top_players()
LeaderboardService.get_rank()
LeaderboardService.delete_user()
LeaderboardService.reset_leaderboard()
```

Integration flow:

```text
HTTP Request
     │
     ▼
API Endpoint
     │
     ▼
Service Layer
     │
     ▼
Redis Client
     │
     ▼
Redis
```

This keeps the API and Redis implementation separated.

---

# Security

Implemented security-related functionality includes:

- Redis password authentication
- Environment-based configuration
- Input validation
- Username validation
- Structured logging
- Tenant/consent contract handling

Secrets such as `REDIS_PASSWORD` and `API_KEY` should never be committed to Git.

The `.gitignore` excludes:

```text
.env
.env.*
```

while allowing:

```text
.env.example
```

to be committed.

---

# Performance

The Redis backend includes:

- Connection pooling
- Redis pipelines
- Bulk operations
- Batch deletion
- Redis Sorted Sets
- Performance benchmarking
- Latency measurement
- Structured logging

Redis Sorted Sets provide a natural data structure for leaderboard-style ranking.

---

# Verification

The implementation was verified locally using:

```powershell
python -m pytest -q
```

Result:

```text
37 passed
1 warning
```

Git verification:

```powershell
git status
```

Result:

```text
nothing to commit, working tree clean
```

Implementation commit:

```text
ea952d8 feat: implement tenant consent and improvement rankings
```

---

# Current Status

## Completed

- [x] Redis connection management
- [x] Redis connection pooling
- [x] Redis authentication configuration
- [x] Leaderboard ZSET implementation
- [x] Score management
- [x] Ranking operations
- [x] Player deletion
- [x] Leaderboard reset
- [x] Input validation
- [x] Performance-oriented Redis operations
- [x] Improvement-ranking service
- [x] Tenant contract / consent layer
- [x] Leaderboard snapshot SQL migrations
- [x] Automated tests
- [x] `.gitignore` / secret protection
- [x] Branch pushed to team repository

## Pending Integration

- API gateway integration
- Final authentication integration
- Final rate-limiting integration
- Cross-module integration testing
- Final deployment configuration

---

# Future Improvements

Potential future improvements include:

- Redis Sentinel
- Redis Cluster
- Prometheus metrics
- Grafana monitoring
- More comprehensive integration tests
- Production-grade authentication
- Distributed rate limiting
- CI/CD test automation

---

# Demonstration

Recommended demonstration flow:

### 1. Start Redis

```powershell
docker compose up -d
docker compose ps
```

### 2. Start the application

```powershell
python -m uvicorn app.main:app --reload
```

### 3. Open API documentation

```text
http://localhost:8000/docs
```

### 4. Demonstrate leaderboard operations

Show:

```text
Set score
   ↓
Increment score
   ↓
Retrieve leaderboard
   ↓
Retrieve player rank
```

### 5. Run automated tests

```powershell
python -m pytest -q
```

Expected result from the current implementation:

```text
37 passed
```

### 6. Explain the architecture

```text
API
 ↓
Leaderboard Service
 ↓
Redis Client
 ↓
Redis ZSET
```

This demonstrates both the implementation and its integration boundary with the rest of Pod Gamma.

---

# Author

**Pradyumna Pandav**

Redis Backend Module  
CyBreach – Module 4 – Pod Gamma
