# CyBreach Pod Gamma Platform — API Gateway

## Overview

CyBreach Pod Gamma Platform is a cybersecurity benchmarking and analytics platform.

This branch contains the **API Gateway / Track 2** implementation.

### Track 2 responsibilities

- Benchmark API endpoints
- Differential privacy for benchmark statistics
- Minimum peer-group enforcement
- Cross-regional benchmark comparison
- Historical benchmark trends
- Redis-backed API rate limiting
- PostgreSQL-backed benchmark data
- Pydantic v2 request validation
- Automated benchmark integration testing

---

# Technology Stack

- Python
- FastAPI
- Uvicorn
- Pydantic v2
- PostgreSQL
- Redis
- NumPy
- asyncpg
- HTTPX
- Pytest
- Docker / Docker Compose

---

# Project Structure

```text
pod-gamma-platform/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── benchmark.py
│   │   └── benchmark_repository.py
│   └── core/
│       ├── __init__.py
│       └── rate_limiter.py
├── database/
│   ├── 003_create_benchmark_aggregate.sql
│   ├── 004_seed_benchmark_aggregate.sql
│   ├── 005_create_benchmark_historical.sql
│   └── 006_seed_benchmark_historical.sql
├── tests/
│   └── test_benchmark.py
├── requirements.txt
├── README.md
└── docker-compose.yml
```

---

# Prerequisites

Install:

- Python 3.10+
- Docker Desktop
- Git

Verify:

```cmd
python --version
docker --version
git --version
```

---

# 1. Clone the Repository

```cmd
git clone <YOUR_REPOSITORY_URL>
cd pod-gamma-platform
git checkout feature/gamma-api-gateway
```

---

# 2. Create Python Virtual Environment

```cmd
python -m venv .venv
```

Activate on Windows CMD:

```cmd
.venv\Scripts\activate
```

---

# 3. Install Python Dependencies

```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Main dependencies:

```text
fastapi==0.110.0
uvicorn==0.28.0
redis==5.0.3
pydantic==2.6.4
numpy
httpx==0.27.2
pytest==9.1.1
```

If installing individually:

```cmd
python -m pip install fastapi==0.110.0
python -m pip install uvicorn==0.28.0
python -m pip install redis==5.0.3
python -m pip install pydantic==2.6.4
python -m pip install numpy
python -m pip install asyncpg
python -m pip install httpx==0.27.2
python -m pip install pytest==9.1.1
```

Verify:

```cmd
python -m pip show fastapi
python -m pip show redis
python -m pip show pydantic
python -m pip show numpy
python -m pip show asyncpg
python -m pip show httpx
python -m pip show pytest
```

---

# 4. Start Redis

If the container does not already exist:

```cmd
docker run -d --name cybreach-redis -p 6379:6379 redis:7
```

If it already exists:

```cmd
docker start cybreach-redis
```

Check:

```cmd
docker ps
```

Test Redis:

```cmd
docker exec cybreach-redis redis-cli ping
```

Expected:

```text
PONG
```

---

# 5. Start PostgreSQL

```cmd
docker start cybreach-postgres
```

Verify:

```cmd
docker ps
```

PostgreSQL should be available on:

```text
localhost:5432
```

The database contains the benchmark aggregate and historical benchmark tables.

---

# 6. Database Tables

## Benchmark Aggregate

The benchmark aggregate contains:

```text
industry
region
size_band
peer_count
peer_25th
peer_median
peer_75th
```

Seeded cohorts include:

```text
Technology / West / Large
Finance / West / Small
Healthcare / West / Large
```

---

# 7. Start FastAPI

```cmd
.venv\Scripts\activate
uvicorn app.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

---

# 8. Swagger API Documentation

Open:

```text
http://127.0.0.1:8000/docs
```

Swagger UI can be used to test the API endpoints.

---

# API Endpoints

## Health Check

```http
GET /health
```

Expected:

```json
{
  "status": "ok"
}
```

---

# Benchmark Percentiles

```http
POST /benchmark
```

Example request:

```json
{
  "industry": "Technology",
  "region": "West",
  "size_band": "Large"
}
```

The API retrieves benchmark data from the database.

---

# Minimum Peer-Group Enforcement

The anonymity threshold is:

```text
10 peers
```

Benchmark cohorts with fewer than 10 peers are blocked to enforce the minimum privacy threshold.

Example test cohort:

```json
{
  "industry": "Finance",
  "region": "West",
  "size_band": "Small"
}
```

This seeded cohort has fewer than 10 peers.

For the benchmark comparison privacy guardrail, the expected response is:

```text
HTTP 403
```

with:

```json
{
  "detail": "insufficient peers"
}
```

A cohort with at least 10 peers can continue to the benchmark comparison logic.

---

# Differential Privacy

For cohorts meeting the minimum peer threshold, benchmark percentiles are protected using the **Laplace mechanism**.

The benchmark response provides:

- p25
- median / p50
- p75

Repeated requests may return different percentile values because privacy noise is applied.

---

# Cross-Regional Comparison

```http
POST /benchmark/compare
```

Example:

```json
{
  "industry": "Technology",
  "region": "West",
  "size_band": "Large"
}
```

The endpoint provides:

- Regional peer count
- Regional median
- Global peer count
- Global median
- Median difference

Example:

```text
Regional median = 76.4
Global median   = 72.0

Difference = 4.4
```

## Privacy Threshold

If the regional cohort has fewer than 10 peers:

```text
HTTP 403
```

Example response:

```json
{
  "detail": "insufficient peers"
}
```

The same privacy threshold is applied when the global benchmark cohort does not meet the minimum peer requirement.

The OpenAPI documentation also exposes the `403` response for this endpoint.

---

# Historical Benchmark Trends

```http
GET /benchmark/trend/TENANT-001
```

The endpoint provides historical benchmark percentile information for:

```text
30 days
60 days
90 days
```

Example response:

```json
[
  {
    "days": 30,
    "p25": 60.2,
    "median": 71.4,
    "p75": 82.1
  },
  {
    "days": 60,
    "p25": 58.3,
    "median": 69.5,
    "p75": 80.7
  },
  {
    "days": 90,
    "p25": 55.8,
    "median": 67.2,
    "p75": 78.9
  }
]
```

---

# Redis Rate Limiting

The API Gateway uses Redis for request rate limiting.

Configured limit:

```text
20 requests per minute
```

Redis stores request counters using time-based keys:

```text
rate_limit:<client_ip>:<minute>
```

## Test Rate Limiting

Clear Redis counters:

```cmd
docker exec cybreach-redis redis-cli FLUSHDB
```

Expected:

```text
Requests 1-20  → Allowed
Request 21      → HTTP 429
```

Expected error:

```json
{
  "detail": "Rate limit exceeded. Maximum 20 requests per minute."
}
```

---

# Pydantic Validation

FastAPI uses Pydantic v2 for request validation.

Invalid request payloads return:

```text
HTTP 422
```

Example invalid request:

```json
{
  "industry": "",
  "region": "West",
  "size_band": "Large"
}
```

The response follows FastAPI's standard validation error schema.

---

# Automated Integration Tests

Track 2 includes automated integration tests for the benchmark comparison endpoint.

Tests are located at:

```text
tests/test_benchmark.py
```

Run benchmark tests:

```cmd
python -m pytest tests\test_benchmark.py -v
```

The tests verify:

- Cohorts with fewer than 10 peers return HTTP 403
- Valid cohorts with at least 10 peers return HTTP 200

Expected:

```text
tests/test_benchmark.py::test_benchmark_compare_insufficient_peers PASSED
tests/test_benchmark.py::test_benchmark_compare_valid_cohort PASSED

2 passed
```

Run the complete test suite:

```cmd
python -m pytest -v
```

Expected:

```text
2 passed
```

The HTTPX/Starlette TestClient combination may display a deprecation warning. This warning does not indicate a test failure.

---

# Testing Checklist

Before submitting changes, verify:

```text
[ ] Redis container is running
[ ] PostgreSQL container is running
[ ] FastAPI starts successfully
[ ] Swagger UI opens
[ ] Pydantic validation returns HTTP 422
[ ] Peer group < 10 is rejected with HTTP 403
[ ] Peer group >= 10 returns benchmark statistics
[ ] Differential privacy is applied
[ ] Cross-regional comparison works
[ ] /benchmark/compare returns HTTP 403 for insufficient peers
[ ] /benchmark/compare returns HTTP 200 for valid cohorts
[ ] Historical trend endpoint works
[ ] Redis rate limiting works
[ ] 21st request returns HTTP 429
[ ] Automated benchmark tests pass
```

---

# Compile Check

```cmd
python -m compileall app
```

There should be no Python compilation errors.

---

# Git Workflow

Check changes:

```cmd
git status
```

Review changes:

```cmd
git diff
```

Add files:

```cmd
git add .
```

Commit:

```cmd
git commit -m "fix: return 403 for insufficient benchmark peers"
```

Push to the team repository:

```cmd
git push team-main feature/gamma-api-gateway
```

---

# Environment Variables

For local development, when required:

```text
REDIS_HOST=localhost
REDIS_PORT=6379
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cybreach
```

When running FastAPI inside Docker Compose, Redis and PostgreSQL hostnames should use their Docker service names.

---

# Troubleshooting

## Redis connection error

```cmd
docker ps
docker exec cybreach-redis redis-cli ping
```

Expected:

```text
PONG
```

## NumPy not found

```cmd
python -m pip install numpy
python -m pip show numpy
```

## FastAPI does not start

```cmd
python -m compileall app
uvicorn app.main:app --reload
```

## TestClient compatibility error

If `TestClient` reports an error involving the `app` argument:

```cmd
python -m pip show httpx
```

Expected:

```text
Version: 0.27.2
```

If required:

```cmd
python -m pip install httpx==0.27.2
```

Then:

```cmd
python -m pytest -v
```

## Port 6379 already in use

```cmd
docker ps
docker start cybreach-redis
```

## Port 8000 already in use

```cmd
uvicorn app.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001/docs
```

---

# Track 2 Summary

This branch provides the API Gateway functionality required for the benchmark platform:

1. PostgreSQL-backed benchmark data
2. Minimum peer-group enforcement
3. HTTP 403 privacy suppression for insufficient benchmark cohorts
4. Differential privacy for benchmark percentiles
5. Cross-regional comparison
6. Historical benchmark trends
7. Redis-backed rate limiting
8. Pydantic v2 request validation
9. Automated benchmark integration tests
10. Docker-based Redis and PostgreSQL services

---

## Branch

```text
feature/gamma-api-gateway
```

## Status

Track 2 API Gateway implementation, privacy enforcement, documentation, and automated testing completed.
