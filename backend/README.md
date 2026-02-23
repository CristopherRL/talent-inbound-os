# Talent Inbound OS -- Backend

**AI-powered inbound recruiting management system for Senior Engineers.**

Talent Inbound OS acts as an intelligent firewall and executive assistant: the user pastes recruiter messages (LinkedIn, Email, freelance platforms), and the system classifies, extracts structured data, scores fit against a configurable candidate profile, drafts diplomatic responses, and tracks opportunity lifecycle to prevent ghosting.

---

## Table of Contents

1. [Backend Overview](#1-backend-overview)
2. [Architecture](#2-architecture)
3. [AI Agent System](#3-ai-agent-system)
4. [API Reference](#4-api-reference)
5. [Database Schema](#5-database-schema)
6. [Testing](#6-testing)
7. [Configuration](#7-configuration)
8. [Getting Started](#8-getting-started)

---

## 1. Backend Overview

| Layer            | Technology                                    |
|------------------|-----------------------------------------------|
| Language         | Python 3.11+                                  |
| Web Framework    | FastAPI (0.115+)                              |
| ORM              | SQLAlchemy 2.0 async (asyncpg driver)         |
| AI Orchestration | LangGraph (0.2+) with LangChain Core          |
| Validation       | Pydantic v2 (2.10+)                           |
| Auth             | python-jose (JWT) + bcrypt                    |
| DI Container     | dependency-injector (4.45+)                   |
| Logging          | structlog                                     |
| Migrations       | Alembic                                       |
| Task Queue       | Arq (Redis-backed, optional for MVP)          |
| Observability    | LangSmith (production), Phoenix (development) |

The backend follows a **Modular Monolith** architecture with **Clean Architecture** layering. Each business module is self-contained with its own domain, application, infrastructure, and presentation layers. Cross-cutting concerns (database sessions, middleware, shared enums) live in a `shared/` package.

Dependency injection is managed centrally through a single `container.py` file using the `dependency-injector` library, wiring together all repositories, use cases, and agents.

---

## 2. Architecture

### Source Layout

```
backend/
  alembic/                    # Database migrations
    versions/                 # Migration scripts
  src/
    talent_inbound/
      api/v1/                 # API version routing
      modules/
        auth/                 # Authentication & authorization
        profile/              # Candidate profile management
        ingestion/            # Message ingestion
        pipeline/             # AI agent orchestration
          prompts/            # LLM prompt templates (.txt)
          infrastructure/
            agents/           # Individual AI agents
            graphs.py         # LangGraph state machine
            model_router.py   # LLM tier routing (FAST/SMART)
            sse.py            # Server-Sent Events for real-time progress
        opportunities/        # Opportunity lifecycle management
        chat/                 # Conversational chat (MVP 2)
      shared/
        domain/               # Base entities, enums, value objects, events
        application/          # Shared application-layer abstractions
        infrastructure/       # Database sessions, middleware, logging, event bus
      config.py               # Centralized settings (pydantic-settings)
      container.py            # Dependency injection container
      main.py                 # FastAPI app factory
      cli.py                  # CLI commands (e.g., password reset)
      worker.py               # Arq worker configuration
  tests/
    unit/                     # Fast, isolated unit tests
    integration/              # Database-backed tests (testcontainers)
    e2e/                      # Full HTTP round-trip tests
  uploads/                    # CV file uploads (local storage)
  pyproject.toml              # Project metadata, dependencies, tool config
  Dockerfile                  # Production container image
  alembic.ini                 # Alembic configuration
  pytest.ini                  # pytest configuration
```

### Module Structure

Each module under `modules/` follows a consistent Clean Architecture layout:

```
module_name/
  domain/                     # Entities (Pydantic BaseModel), abstract repositories, exceptions
  application/                # Use cases (business logic orchestration)
  presentation/               # FastAPI routers, request/response schemas
  infrastructure/             # ORM models (SQLAlchemy), repository implementations, agents
```

**Key design rules:**
- Domain entities are **Pydantic BaseModel** instances (not dataclasses).
- ORM models are **SQLAlchemy DeclarativeBase** classes, separate from domain entities.
- Repositories are defined as abstract base classes in `domain/` and implemented in `infrastructure/`.
- Use cases depend only on abstractions (repository interfaces), never on concrete implementations.

### Module Responsibilities

| Module          | Purpose                                                                                     |
|-----------------|---------------------------------------------------------------------------------------------|
| `auth`          | JWT-based authentication: register, login, refresh, logout. HTTP-only secure cookies. bcrypt password hashing. |
| `profile`       | Candidate profile CRUD. CV upload with PDF/DOCX text extraction. AI-powered skill extraction from CV content. |
| `ingestion`     | Message ingestion endpoint. Duplicate detection (same content + source within time window).  |
| `pipeline`      | LangGraph orchestration of 7 AI agents. SSE real-time progress streaming. Model routing between FAST and SMART LLM tiers. |
| `opportunities` | Opportunity CRUD. Draft response management. Stage lifecycle transitions. Stale opportunity detection. Follow-up message processing. |
| `chat`          | Conversational chat with AI orchestrator (MVP 2, LangGraph + tool-use).                     |
| `shared`        | Base models, CORS/session middleware, domain enums, database session management, event bus.  |

---

## 3. AI Agent System

The AI pipeline is orchestrated by **LangGraph** as a directed state graph. Each agent is a node that receives the pipeline state, performs its work, and returns updated state. A central **ModelRouter** maps each agent to the appropriate LLM tier (FAST or SMART).

### LLM Tiers

| Agent              | Tier  | Default Model               |
|--------------------|-------|-----------------------------|
| Guardrail          | FAST  | Claude Haiku 4.5            |
| Gatekeeper         | FAST  | Claude Haiku 4.5            |
| Extractor          | SMART | Claude Sonnet 4.5           |
| Language Detector  | FAST  | Claude Haiku 4.5            |
| Analyst            | SMART | Claude Sonnet 4.5           |
| Communicator       | SMART | Claude Sonnet 4.5           |
| Stage Detector     | FAST  | Claude Haiku 4.5            |

Models are configurable via `LLM_FAST_MODEL` and `LLM_SMART_MODEL` environment variables. The provider (`anthropic` or `openai`) is set via `LLM_PROVIDER`.

### Mode 1: Initial Pipeline (Full Ingestion)

When a recruiter message is submitted, it passes through the full agent pipeline:

```
guardrail --> gatekeeper --> extractor --> language_detector --> analyst --> communicator --> stage_detector --> END
                |                              |
          (injection detected)           (missing required fields)
                |                              |
               END                        Skips analyst/communicator,
                |                         still runs stage_detector
          (spam / not an offer)
                |
               END
```

**Agent details:**

- **Guardrail**: Two-layer defense system. First layer applies regex heuristics to detect prompt injection patterns. Second layer uses a FAST-tier LLM for deeper analysis. Also performs PII sanitization (phone numbers, email addresses, SSNs, physical addresses). If prompt injection is detected, the pipeline halts immediately.

- **Gatekeeper**: FAST-tier LLM classifies the message as `REAL_OFFER`, `SPAM`, or `NOT_AN_OFFER`. Non-offers stop the pipeline and the interaction is marked accordingly.

- **Extractor**: SMART-tier LLM extracts structured data fields: company name, role title, salary range, tech stack, work model (remote/hybrid/onsite), and recruiter information (name, type). Includes a hallucination check to verify extracted data against the source text. Reports `missing_fields` for any required fields that could not be extracted (configurable via `EXTRACTION_REQUIRED_FIELDS`).

- **Language Detector**: FAST-tier LLM detects the language of the recruiter message (`en` or `es`). The detected language is persisted on the opportunity and used by the Communicator to generate drafts in the correct language. This agent always runs, even when required fields are missing.

- **Analyst**: SMART-tier LLM scores the match (0--100) between the opportunity and the candidate profile. Considers skill overlap, work model preference, and salary expectations. Uses configurable scoring weights. Only runs when all required extraction fields are present.

- **Communicator**: SMART-tier LLM drafts a context-aware response based on the match score, detected language, and opportunity data. Falls back to template-based generation when no LLM is available.

- **Stage Detector**: FAST-tier LLM suggests a lifecycle stage transition based on conversation content. Includes a bilingual (English/Spanish) keyword heuristic as a fallback when LLM analysis is inconclusive.

### Mode 2: On-Demand Draft Generation

Users can request additional AI-generated drafts at any time:

```
POST /api/v1/opportunities/{id}/drafts
```

This invokes the **Communicator** agent directly (not the full pipeline). Features:
- User can override the language (`en`/`es`) or rely on auto-detection from `opportunity.detected_language`.
- `additional_context` provided by the user passes through the **Guardrail** agent before reaching the LLM (raises `ValueError` if injection is detected).
- Supports three response types: `REQUEST_INFO`, `EXPRESS_INTEREST`, `DECLINE`.

### Mode 3: Follow-Up Pipeline

When the user submits a follow-up message for an existing opportunity:

```
POST /api/v1/opportunities/{id}/follow-ups
```

The follow-up pipeline is the same as the initial pipeline but with two differences:
1. **Gatekeeper is skipped** -- the opportunity is already classified as a real offer.
2. **Stage Detector only suggests** -- it does not force stage transitions. The suggested stage is recorded but the current stage is preserved unless the user explicitly changes it.

The follow-up pipeline uses the full conversation history (all messages in the interaction chain) to provide better context to each agent.

### Guardrail Coverage

All user-provided text inputs are protected by the Guardrail agent:

| Input Path                          | Protection Behavior                                |
|-------------------------------------|----------------------------------------------------|
| Pipeline ingestion (raw messages)   | Full guardrail check; halts pipeline on injection   |
| Draft `additional_context`          | Guardrail check; raises `ValueError` on injection   |
| CV text extraction                  | Guardrail check; returns empty skill list on injection |

### LLM Response Robustness

All agents follow a defensive parsing pattern for LLM responses:
1. Attempt direct `json.loads()` parsing.
2. Fall back to regex extraction (LLMs sometimes wrap JSON in markdown code blocks).
3. Fall back to heuristic analysis (never hardcode a default on parse failure).
4. All LLM response paths include `structlog` logging for observability.

---

## 4. API Reference

When running locally, full interactive API documentation is available at:

```
http://127.0.0.1:8000/docs       # Swagger UI
http://127.0.0.1:8000/redoc      # ReDoc
```

### Endpoint Summary

#### Authentication

| Method | Endpoint                     | Description                          |
|--------|------------------------------|--------------------------------------|
| POST   | `/api/v1/auth/register`      | Create a new account                 |
| POST   | `/api/v1/auth/login`         | Login (sets HTTP-only cookies)       |
| POST   | `/api/v1/auth/refresh`       | Refresh the access token             |
| POST   | `/api/v1/auth/logout`        | Clear authentication cookies         |

#### Profile

| Method | Endpoint                              | Description                             |
|--------|---------------------------------------|-----------------------------------------|
| GET    | `/api/v1/profile/me`                  | Get current candidate profile           |
| PUT    | `/api/v1/profile/me`                  | Update candidate profile                |
| POST   | `/api/v1/profile/me/cv`               | Upload CV (PDF or DOCX)                 |
| POST   | `/api/v1/profile/me/cv/extract-skills`| AI-powered skill extraction from CV     |

#### Ingestion

| Method | Endpoint                     | Description                          |
|--------|------------------------------|--------------------------------------|
| POST   | `/api/v1/ingestion/messages` | Submit a recruiter message           |

#### Opportunities

| Method | Endpoint                                              | Description                             |
|--------|-------------------------------------------------------|-----------------------------------------|
| GET    | `/api/v1/opportunities`                               | List opportunities (filterable by stage, sortable) |
| GET    | `/api/v1/opportunities/{id}`                          | Get opportunity detail with full timeline |
| POST   | `/api/v1/opportunities/{id}/drafts`                   | Generate an AI draft response           |
| PUT    | `/api/v1/opportunities/{id}/drafts/{draft_id}`        | Edit a draft response                   |
| POST   | `/api/v1/opportunities/{id}/drafts/{draft_id}/send`   | Mark a draft as sent                    |
| POST   | `/api/v1/opportunities/{id}/follow-ups`               | Submit a follow-up message              |
| PUT    | `/api/v1/opportunities/{id}/stage`                    | Manually change the opportunity stage   |
| GET    | `/api/v1/opportunities/stale`                         | Get stale opportunity alerts            |

#### Pipeline

| Method | Endpoint                                       | Description                           |
|--------|-------------------------------------------------|---------------------------------------|
| GET    | `/api/v1/pipeline/progress/{interaction_id}`   | SSE stream for real-time pipeline progress |

All endpoints (except auth) require authentication via HTTP-only cookies set during login. Cross-user data isolation is enforced at every endpoint -- a user can only access their own data.

---

## 5. Database Schema

The database is **PostgreSQL 16** with the **pgvector** extension for vector similarity search. Schema changes are managed through **Alembic** migrations.

### Tables

| Table                 | Purpose                                                                                          |
|-----------------------|--------------------------------------------------------------------------------------------------|
| `users`               | Authentication credentials: email (unique), hashed password (bcrypt), timestamps.                |
| `candidate_profiles`  | Candidate data: skills (array), preferences, minimum salary, preferred work model, CV extracted text, associated user foreign key. |
| `interactions`        | Raw ingested messages: source (`LINKEDIN`, `EMAIL`, `FREELANCE_PLATFORM`, `OTHER`), type (`INITIAL`, `FOLLOW_UP`, `CANDIDATE_RESPONSE`), raw content, processing status, linked opportunity. |
| `opportunities`       | Structured vacancy data: company, role, salary range, tech stack, work model, recruiter info, `match_score` (0--100), `detected_language` (`en`/`es`), current `stage` (DISCOVERY, ENGAGING, INTERVIEWING, NEGOTIATING, OFFER, REJECTED, DECLINED, GHOSTED), classification, missing fields, candidate foreign key. |
| `draft_responses`     | AI-generated drafts: `response_type` (`REQUEST_INFO`, `EXPRESS_INTEREST`, `DECLINE`), `generated_content`, `edited_content` (user modifications), `is_final`, `is_sent`, linked opportunity. Confirming a DECLINE draft as sent auto-advances the opportunity to the DECLINED stage. |
| `stage_transitions`   | Stage change audit trail: `from_stage`, `to_stage`, `triggered_by` (`SYSTEM`, `USER`, `CHAT`), `is_unusual` flag, timestamp, linked opportunity. Auto-transitions include DISCOVERY→ENGAGING (first response sent) and any active stage→DECLINED (decline response sent). |

### Migrations

All migration scripts are stored in `alembic/versions/`. To apply pending migrations:

```bash
alembic upgrade head
```

To generate a new migration after model changes:

```bash
alembic revision --autogenerate -m "description of change"
```

---

## 6. Testing

The test suite uses **pytest** with custom markers to separate test categories.

### Test Categories

| Category      | Marker          | Directory              | Description                                                    |
|---------------|-----------------|------------------------|----------------------------------------------------------------|
| Unit          | `@pytest.mark.unit`        | `tests/unit/`          | Fast, isolated tests with mocked dependencies. No database required. |
| Integration   | `@pytest.mark.integration` | `tests/integration/`   | Database-backed tests using **testcontainers** (spins up a real PostgreSQL instance in Docker). |
| End-to-End    | `@pytest.mark.e2e`        | `tests/e2e/`           | Full HTTP round-trip tests against the running FastAPI application. |

### Current Coverage

- **214 total tests**: 170+ unit, 6 integration (testcontainers), 28 end-to-end
- **Coverage target**: 80% minimum (configured in `pyproject.toml`)

### Running Tests

```bash
# Run all tests
pytest

# Run by category
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run with coverage report
pytest --cov=src/talent_inbound --cov-report=term-missing

# Run a specific module's tests
pytest tests/unit/pipeline/
```

### Test Tooling

- **pytest-asyncio**: Async test support for SQLAlchemy and FastAPI async endpoints.
- **httpx**: Async HTTP client for e2e tests.
- **factory-boy**: Test data factories for consistent, readable test setup.
- **testcontainers**: Docker-based PostgreSQL instances for integration tests.

---

## 7. Configuration

All configuration is managed through environment variables, loaded via **pydantic-settings** in `src/talent_inbound/config.py`. A `.env` file in the backend root is automatically loaded.

### Environment Variables

#### Database

| Variable        | Default                                                           | Description                      |
|-----------------|-------------------------------------------------------------------|----------------------------------|
| `DATABASE_URL`  | `postgresql+asyncpg://talent:talent_dev@localhost:5432/talent_inbound` | Async PostgreSQL connection string. Must use `postgresql+asyncpg://` scheme. |
| `REDIS_URL`     | `redis://localhost:6379`                                          | Redis connection (for Arq task queue, optional for MVP). |

#### Authentication

| Variable                            | Default                                | Description                             |
|-------------------------------------|----------------------------------------|-----------------------------------------|
| `JWT_SECRET_KEY`                    | `change-me-generate-with-openssl-rand-hex-32` | Secret for signing JWT tokens. **Must be changed in production.** |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`   | `30`                                   | Access token TTL in minutes.            |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS`     | `7`                                    | Refresh token TTL in days.              |

#### LLM Configuration

| Variable            | Default                         | Description                                       |
|---------------------|---------------------------------|---------------------------------------------------|
| `ANTHROPIC_API_KEY` | (empty)                         | Anthropic API key for Claude models.              |
| `OPENAI_API_KEY`    | (empty)                         | OpenAI API key (alternative provider).            |
| `LLM_PROVIDER`      | `anthropic`                     | LLM provider: `anthropic` or `openai`.            |
| `LLM_FAST_MODEL`    | `claude-haiku-4-5-20251001`     | Model used for FAST-tier agents.                  |
| `LLM_SMART_MODEL`   | `claude-sonnet-4-5-20250929`    | Model used for SMART-tier agents.                 |

#### Observability

| Variable                | Default                | Description                                |
|-------------------------|------------------------|--------------------------------------------|
| `LANGCHAIN_TRACING_V2`  | `false`                | Enable LangSmith tracing.                  |
| `LANGCHAIN_API_KEY`     | (empty)                | LangSmith API key.                         |
| `LANGCHAIN_PROJECT`     | `talent-inbound-os`    | LangSmith project name.                    |
| `LOG_LEVEL`             | `INFO`                 | Application log level.                     |

#### Application

| Variable                      | Default                                      | Description                                           |
|-------------------------------|----------------------------------------------|-------------------------------------------------------|
| `ENVIRONMENT`                 | `development`                                | `development` or `production`. Controls cookie security flags. |
| `CORS_ORIGINS`                | `http://localhost:3000,http://127.0.0.1:3000`| Comma-separated allowed CORS origins.                 |
| `UPLOAD_DIR`                  | `backend/uploads`                            | Directory for CV file uploads.                        |
| `MAX_MESSAGE_LENGTH`          | `50000`                                      | Maximum character length for ingested messages.       |
| `EXTRACTION_REQUIRED_FIELDS`  | `["salary_range", "tech_stack", "role_title"]`| Fields required for a complete extraction.           |

#### Scoring (Analyst Agent)

| Variable                        | Default | Description                                            |
|---------------------------------|---------|--------------------------------------------------------|
| `SCORING_BASE`                  | `50`    | Base match score.                                      |
| `SCORING_SKILLS_WEIGHT`         | `30`    | Max points for skill overlap.                          |
| `SCORING_WORK_MODEL_MATCH`      | `10`    | Bonus for matching work model preference.              |
| `SCORING_WORK_MODEL_MISMATCH`   | `-5`    | Penalty for mismatched work model.                     |
| `SCORING_SALARY_MEETS_MIN`      | `10`    | Bonus when salary meets minimum.                       |
| `SCORING_SALARY_BELOW_MIN`      | `-10`   | Penalty when salary is below minimum.                  |
| `SCORING_THRESHOLD_HIGH`        | `70`    | Score threshold for "high match" classification.       |
| `SCORING_THRESHOLD_MEDIUM`      | `40`    | Score threshold for "medium match" classification.     |

#### Chat (MVP 2)

| Variable            | Default                  | Description                            |
|---------------------|--------------------------|----------------------------------------|
| `CHAT_DAILY_LIMIT`  | `50`                     | Maximum chat messages per user per day.|
| `EMBEDDING_MODEL`   | `text-embedding-3-small` | Embedding model for vector search.     |

---

## 8. Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 16 with the `pgvector` extension
- Docker (for integration tests with testcontainers)
- An Anthropic API key (or OpenAI API key)

### Local Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Create a .env file from the configuration reference above
# At minimum, set: DATABASE_URL, JWT_SECRET_KEY, ANTHROPIC_API_KEY

# 5. Run database migrations
alembic upgrade head

# 6. Start the development server
uvicorn talent_inbound.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000` with Swagger docs at `http://127.0.0.1:8000/docs`.

### Docker (Production)

```bash
docker build -t talent-inbound-backend .
docker run -p 8000:8000 --env-file .env talent-inbound-backend
```

The production Dockerfile runs Alembic migrations on startup before launching uvicorn.

### CLI Commands

```bash
# Reset a user's password
python -m talent_inbound.cli reset-password
```

---

## License

AGPL v3 — See [LICENSE](../LICENSE) for details. For commercial use, contact [cristopher.rojas.lepe@gmail.com].
