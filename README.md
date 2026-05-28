# changelens — Cloud-Native Change Intelligence Platform

## Context

SREs spend critical minutes during incidents manually correlating "what changed before the outage?" across disparate systems — CI/CD pipelines, Kubernetes config, alerting tools, and rollback logs. This platform ingests change and incident events from multiple sources, normalizes them into a shared schema, and surfaces a unified timeline per service and environment. MVP focuses on ingestion, correlation, and query — no UI, API-first.

**Target dir**: `/Users/sumit.anand/Repositories/personal/changelens`

---

## Tech Stack

| Layer | Choice |
|---|---|
| API | Python 3.12 + FastAPI (async) |
| ORM | SQLAlchemy 2.x (async) |
| DB | PostgreSQL 16 (JSONB for metadata; runs anywhere — cloud-agnostic) |
| Migrations | Alembic |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Task queue | Redis + arq (lightweight async worker for deferred ingestion) |
| Webhook security | HMAC-SHA256 signature verification |
| Observability | OpenTelemetry + Prometheus `/metrics` |
| Logging | structlog (structured JSON) |
| Config | pydantic-settings (12-factor env-vars) |
| Testing | pytest + pytest-asyncio + httpx |
| Container | Docker + Docker Compose (local) |
| K8s packaging | Kustomize (base + dev/prod overlays) |
| CI | GitHub Actions |

Storage is cloud-agnostic: PostgreSQL runs locally, on-prem, or any managed service (RDS, Cloud SQL, Azure DB, Neon). No vendor extensions in MVP. Repository pattern abstracts the DB layer for testability and future swap.

---

## Directory Structure

```
changelens/
├── .github/
│   └── workflows/
│       ├── ci.yml                     # lint, typecheck, test on PR
│       └── docker-publish.yml         # build + push image on main
├── src/
│   └── changelens/
│       ├── main.py                    # FastAPI app factory
│       ├── config.py                  # pydantic-settings
│       ├── api/
│       │   ├── deps.py                # auth + db session deps
│       │   └── v1/
│       │       ├── router.py          # mounts all sub-routers
│       │       ├── events.py          # ingestion + list endpoints
│       │       ├── webhooks.py        # /webhooks/{source} receivers
│       │       ├── timelines.py       # timeline query endpoints
│       │       ├── incidents.py       # incident CRUD
│       │       ├── annotations.py     # manual tags
│       │       ├── search.py          # full-text search
│       │       ├── export.py          # JSON/CSV/Markdown export
│       │       └── auth.py            # token issuance + /me
│       ├── core/
│       │   ├── auth.py                # JWT encode/decode + RBAC
│       │   ├── security.py            # HMAC webhook verification
│       │   └── logging.py             # structlog setup
│       ├── models/                    # SQLAlchemy ORM models
│       │   ├── event.py               # ChangeEvent (immutable, append-only)
│       │   ├── incident.py            # Incident
│       │   ├── annotation.py          # Annotation
│       │   └── user.py                # User + Role
│       ├── schemas/                   # Pydantic request/response schemas
│       │   ├── event.py
│       │   ├── incident.py
│       │   ├── timeline.py
│       │   ├── annotation.py
│       │   └── auth.py
│       ├── ingestion/                 # Pluggable webhook parsers
│       │   ├── base.py                # Abstract IngestionParser
│       │   ├── github_actions.py      # GitHub Actions deployment webhook
│       │   ├── alertmanager.py        # Prometheus Alertmanager
│       │   ├── kubernetes.py          # K8s audit event parser
│       │   └── generic.py             # Passthrough for unknown sources
│       ├── timeline/
│       │   ├── correlator.py          # Event → incident time-window correlation
│       │   ├── query.py               # Timeline query builder (filter, paginate)
│       │   └── export.py              # Serialize to JSON/CSV/Markdown
│       ├── repository/                # Storage abstraction (cloud-agnostic)
│       │   ├── base.py                # Abstract BaseRepository[T]
│       │   ├── event_repo.py
│       │   ├── incident_repo.py
│       │   └── annotation_repo.py
│       └── db/
│           ├── session.py             # Async SQLAlchemy engine + session factory
│           └── migrations/            # Alembic env + versioned migrations
├── tests/
│   ├── conftest.py                    # fixtures: test DB, async client
│   ├── unit/
│   │   ├── test_ingestion/            # parser unit tests per source
│   │   ├── test_timeline/             # correlator + query tests
│   │   └── test_schemas/              # Pydantic validation tests
│   └── integration/
│       ├── test_events_api.py
│       ├── test_webhooks.py
│       ├── test_timeline_api.py
│       └── test_auth.py
├── k8s/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── hpa.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── dev/kustomization.yaml
│       └── prod/kustomization.yaml
├── docker-compose.yml                 # postgres + redis + api
├── docker-compose.override.yml        # dev hot-reload overrides
├── Dockerfile
├── pyproject.toml                     # deps, ruff, mypy, pytest config
├── alembic.ini
├── .env.example
└── README.md
```

---

## Core Data Model

### `change_events` (immutable, append-only)

```
event_id        UUID PK
event_type      ENUM(deployment, config_change, incident, rollback, annotation, generic)
service         TEXT NOT NULL
environment     TEXT NOT NULL
cluster         TEXT
region          TEXT
version         TEXT
actor           TEXT NOT NULL
source_system   ENUM(github_actions, alertmanager, kubernetes, pagerduty, manual, generic)
timestamp       TIMESTAMPTZ NOT NULL  ← indexed
received_at     TIMESTAMPTZ NOT NULL
raw_payload     JSONB
metadata        JSONB
incident_id     UUID FK → incidents (nullable)
checksum        TEXT  ← SHA-256 of raw_payload for integrity
```

### `incidents`
```
incident_id     UUID PK
title           TEXT NOT NULL
service         TEXT NOT NULL
environment     TEXT NOT NULL
started_at      TIMESTAMPTZ
resolved_at     TIMESTAMPTZ
severity        ENUM(critical, high, medium, low)
source_system   TEXT
external_id     TEXT  ← PagerDuty/ServiceNow ID
status          ENUM(open, resolved, investigating)
created_by      UUID FK → users
created_at      TIMESTAMPTZ
```

### `annotations`
```
annotation_id   UUID PK
event_id        UUID FK → change_events (nullable)
incident_id     UUID FK → incidents (nullable)
service         TEXT
environment     TEXT
timestamp       TIMESTAMPTZ  ← point-in-time if no event_id
body            TEXT
author          UUID FK → users
created_at      TIMESTAMPTZ
```

### `users`
```
user_id         UUID PK
email           TEXT UNIQUE
hashed_password TEXT
role            ENUM(admin, operator, viewer, auditor)
is_active       BOOL
created_at      TIMESTAMPTZ
```

---

## API Surface (MVP)

### Ingestion
- `POST /api/v1/events` — generic structured event ingestion
- `POST /api/v1/webhooks/github-actions` — GitHub Actions deployment webhook (HMAC verified)
- `POST /api/v1/webhooks/alertmanager` — Prometheus Alertmanager firing/resolved
- `POST /api/v1/webhooks/kubernetes` — K8s audit events
- `GET  /api/v1/events` — list events (filter: service, env, type, time range, source)

### Timeline
- `GET /api/v1/timeline` — unified timeline (service + env + time window)
- `GET /api/v1/timeline/incident/{incident_id}` — incident-scoped timeline
- `GET /api/v1/timeline/context` — "changes in last N hours before `at`" view

### Incidents
- `POST /api/v1/incidents` — register incident
- `GET  /api/v1/incidents` — list with filters
- `GET  /api/v1/incidents/{id}` — detail + correlated events
- `PATCH /api/v1/incidents/{id}` — update status/severity

### Annotations
- `POST /api/v1/annotations` — create manual note
- `GET  /api/v1/annotations` — list

### Search
- `GET /api/v1/search` — full-text + filter search across events and annotations

### Export
- `GET /api/v1/export/timeline` — export as `?format=json|csv|markdown`

### Auth
- `POST /api/v1/auth/token` — issue JWT (email + password)
- `GET  /api/v1/auth/me` — current user

### Platform
- `GET /healthz` — liveness probe
- `GET /readyz` — readiness probe (checks DB + Redis)
- `GET /metrics` — Prometheus metrics

---

## Build Phases

### Phase 1 — Foundation
- `git init`, `pyproject.toml` (ruff, mypy, pytest), `.env.example`
- FastAPI app factory in `main.py`, `/healthz` endpoint
- `docker-compose.yml` (postgres:16, redis:7, api service)
- `Dockerfile` (multi-stage, non-root user)
- SQLAlchemy async engine + session factory (`db/session.py`)
- Alembic setup + initial migration (empty schema placeholder)
- structlog JSON logging, pydantic-settings config
- GitHub Actions CI: `ruff check`, `mypy`, `pytest`

### Phase 2 — Event Schema + Generic Ingestion
- SQLAlchemy models: `ChangeEvent`, `Incident`, `Annotation`, `User`
- Alembic migration for full schema
- Repository layer: `BaseRepository`, `EventRepository`, `IncidentRepository`, `AnnotationRepository`
- Pydantic schemas for all models
- `POST /api/v1/events` with validation and SHA-256 checksum
- `GET /api/v1/events` with filtering and pagination
- Unit tests for schemas and repository layer

### Phase 3 — Webhook Ingestion Parsers
- Abstract `IngestionParser` base class
- `GitHubActionsParser`: parse `workflow_run` / `deployment_status` payloads → `ChangeEvent`
- `AlertmanagerParser`: parse firing/resolved alerts → `ChangeEvent(event_type=incident)`
- `KubernetesParser`: parse audit events (ConfigMap, Deployment changes) → `ChangeEvent(event_type=config_change)`
- `POST /api/v1/webhooks/{source}` router with HMAC-SHA256 verification middleware
- Unit tests for each parser with fixture payloads

### Phase 4 — Timeline & Correlation
- `timeline/query.py`: query builder — filter by service, env, time range; paginated; sorted by timestamp
- `timeline/correlator.py`: given an incident, find all events within a configurable window (default ±2h)
- `GET /api/v1/timeline`, `GET /api/v1/timeline/incident/{id}`, `GET /api/v1/timeline/context`
- `POST /api/v1/incidents`, `GET /api/v1/incidents`, `GET /api/v1/incidents/{id}`
- `POST /api/v1/annotations`, `GET /api/v1/annotations`
- Integration tests for timeline queries

### Phase 5 — Search, Export, RBAC, Audit
- `GET /api/v1/search`: PostgreSQL full-text search (tsvector on service, actor, metadata)
- `timeline/export.py`: JSON, CSV (via `csv` stdlib), Markdown table
- `GET /api/v1/export/timeline`
- JWT auth: `core/auth.py` (python-jose + passlib), `POST /api/v1/auth/token`, `GET /api/v1/auth/me`
- RBAC dependency (`deps.py`): admin, operator, viewer, auditor gate per endpoint
- Immutable audit log (write-only append to `change_events`; edits create new annotation, never mutate)

### Phase 6 — Observability + Kubernetes
- OpenTelemetry tracing (OTLP exporter, auto-instrumentation for FastAPI + SQLAlchemy)
- `prometheus-fastapi-instrumentator` for `/metrics`
- `GET /readyz` checks DB pool + Redis ping
- Kubernetes manifests: `k8s/base/` (Deployment, Service, ConfigMap, HPA)
- Kustomize overlays: `dev` (1 replica, debug log level), `prod` (3 replicas, resource limits)
- `README.md`: architecture diagram (ASCII), quickstart, webhook integration guide

---

## Verification

1. **Local dev**: `docker compose up` → all services healthy → `GET /healthz` returns 200
2. **Ingestion smoke test**: `curl -X POST /api/v1/events` with a sample payload → event appears in `GET /api/v1/events`
3. **Webhook test**: POST a GitHub Actions `workflow_run` fixture to `/api/v1/webhooks/github-actions` → normalized `ChangeEvent` stored
4. **Timeline test**: create 3 events + 1 incident → `GET /api/v1/timeline/incident/{id}` returns correlated events
5. **Export test**: `GET /api/v1/export/timeline?format=csv` returns valid CSV
6. **Auth test**: unauthenticated request to protected endpoint returns 401; wrong role returns 403
7. **K8s test**: `kubectl apply -k k8s/overlays/dev` → pod reaches `Running`, `/readyz` returns 200
8. **CI**: all `ruff`, `mypy`, `pytest` checks pass in GitHub Actions

---

## Critical Files (post-implementation)

- `src/changelens/main.py` — app factory
- `src/changelens/config.py` — all env-var config
- `src/changelens/models/event.py` — core schema
- `src/changelens/ingestion/base.py` — parser interface (extend for new sources)
- `src/changelens/repository/base.py` — storage abstraction
- `src/changelens/timeline/correlator.py` — correlation engine
- `src/changelens/api/v1/webhooks.py` — webhook routing + HMAC
- `docker-compose.yml` — local dev entrypoint
- `k8s/base/kustomization.yaml` — K8s base
