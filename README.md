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
- Docker / Docker Compose

---

# Project Structure

```text
pod-gamma-platform/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── benchmark.py
│   │   └── benchmark_repository.py
│   │
│   └── core/
│       ├── __init__.py
│       └── rate_limiter.py
│
├── database/
│   ├── 003_create_benchmark_aggregate.sql
│   ├── 004_seed_benchmark_aggregate.sql
│   ├── 005_create_benchmark_historical.sql
│   └── 006_seed_benchmark_historical.sql
│
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

If installing dependencies individually:

```cmd
python -m pip install fastapi==0.110.0
python -m pip install uvicorn==0.28.0
python -m pip install redis==5.0.3
python -m pip install pydantic==2.6.4
python -m pip install numpy
python -m pip install asyncpg
```

Verify:

```cmd
python -m pip show fastapi
python -m pip show redis
python -m pip show pydantic
python -m pip show numpy
python -m pip show asyncpg
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

Start the PostgreSQL container:

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

Seeded cohorts include examples such as:

```text
Technology / West / Large
Finance / West / Small
Healthcare / West / Large
```

---

# 7. Start FastAPI

Activate the virtual environment:

```cmd
.venv\Scripts\activate
```

Start the API:

```cmd
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

## Benchmark Percentiles

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

Example test cohort:

```json
{
  "industry": "Finance",
  "region": "West",
  "size_band": "Small"
}
```

This seeded cohort has fewer than 10 peers.

Expected:

```text
HTTP 422
```

with an insufficient-peer error.

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

---

# Historical Benchmark Trends

```http
GET /benchmark/trend/TENANT-001
```

The endpoint provides historical benchmark percentile information for periods such as:

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

Redis stores request counters using time-based keys.

Example:

```text
rate_limit:<client_ip>:<minute>
```

## Test Rate Limiting

Clear Redis counters:

```cmd
docker exec cybreach-redis redis-cli FLUSHDB
```

Send requests to the endpoint protected by the rate limiter.

Expected:

```text
Requests 1–20  → Allowed
Request 21     → HTTP 429
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

# Testing Checklist

Before submitting changes, verify:

```text
[ ] Redis container is running
[ ] PostgreSQL container is running
[ ] FastAPI starts successfully
[ ] Swagger UI opens
[ ] Pydantic validation returns HTTP 422
[ ] Peer group < 10 is rejected
[ ] Peer group >= 10 returns benchmark statistics
[ ] Differential privacy is applied
[ ] Cross-regional comparison works
[ ] Historical trend endpoint works
[ ] Redis rate limiting works
[ ] 21st request returns HTTP 429
```

---

# Compile Check

Run:

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
git commit -m "docs: add API Gateway setup and testing guide"
```

Push:

```cmd
git push origin feature/gamma-api-gateway
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
3. Differential privacy for benchmark percentiles
4. Cross-regional comparison
5. Historical benchmark trends
6. Redis-backed rate limiting
7. Pydantic v2 request validation
8. Docker-based Redis and PostgreSQL services

---

## Branch

```text
feature/gamma-api-gateway
```

## Status

Track 2 API Gateway implementation and testing completed.
