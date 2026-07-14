# Redis Leaderboard Backend

## Overview

This module implements the Redis backend for the CyBreach Leaderboard service.

It is responsible for all Redis-related operations including:

- Redis connection management
- Connection pooling
- Leaderboard business logic
- Redis Sorted Set (ZSET) operations
- Performance benchmarking
- Logging
- Redis configuration
- Unit testing

The API layer is intentionally kept independent so that it can be integrated by the API team.

---

# Project Structure

```
redis-backend/
│
├── app/
│   ├── db/
│   │   └── redis_client.py
│   │
│   ├── services/
│   │   └── leaderboard_service.py
│   │
│   ├── utils/
│   │   ├── benchmark.py
│   │   └── logger.py
│   │
│   ├── models/
│   ├── api/
│   ├── config.py
│   ├── exceptions.py
│   └── main.py
│
├── database/
│   ├── redis.conf
│   └── verify_leaderboard.py
│
├── docs/
│   ├── integration_guide.md
│   └── redis_module.md
│
├── tests/
│
├── docker-compose.yml
├── requirements.txt
└── Dockerfile
```

---

# Features

## Redis Connection Pool

- Singleton Redis client
- Connection pooling
- Automatic retries
- Redis authentication support
- Health checks
- Structured logging

---

## Leaderboard Operations

Implemented using Redis Sorted Sets (ZSET).

Supported operations:

- Set player score
- Increment player score
- Retrieve leaderboard
- Retrieve player rank
- Delete player
- Reset leaderboard

---

## Performance Improvements

Implemented:

- Redis Connection Pool
- Redis Pipelines
- Bulk insertion
- Batch deletion
- Username validation
- Performance benchmarking
- Latency measurement
- Structured logging

---

# Security

The following security features have already been implemented in this module:

- Redis password authentication
- Environment variable configuration
- Username validation
- Input validation
- Structured logging

The following API security features are temporarily disabled because the API layer is under development:

- API Key Authentication
- Rate Limiting
- Security Headers

These features will be re-enabled once the API module is integrated.

---

# Environment Variables

Example:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password

APP_ENV=development
LOG_LEVEL=INFO
```

---

# Running

Install dependencies

```bash
pip install -r requirements.txt
```

Start Redis

```bash
docker compose up -d
```

Run the application

```bash
uvicorn app.main:app --reload
```

Run tests

```bash
pytest
```

---

# Documentation

Additional documentation is available in:

- docs/redis_module.md
- docs/integration_guide.md

---

# Integration Notes

The API team should use the existing service layer.

Available methods:

```python
LeaderboardService.set_score()

LeaderboardService.increment_score()

LeaderboardService.get_top_players()

LeaderboardService.get_rank()

LeaderboardService.delete_user()

LeaderboardService.reset_leaderboard()
```

No changes are required to the service layer.

The API should simply call these methods.

---

# Future Improvements

- API Key Authentication
- Rate Limiting
- JWT Authentication
- Redis Sentinel Support
- Redis Cluster Support
- Prometheus Metrics
- Grafana Dashboard

---

# Author

Pradyumna Pandav

Redis Backend Module

CyBreach – Module 4 – Pod Gamma