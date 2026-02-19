# Talent Inbound OS

**Passive Offer Intelligence** — An AI-powered inbound recruiting management system for Senior Engineers.

> Master's Final Project (TFM) — Master en Desarrollo con IA, BIG School
> Author: Cristopher RL
> Date: February 2026

---

## Table of Contents

- [Live Demo](#live-demo)
- [Project Description](#project-description)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [AI Agent Pipeline](#ai-agent-pipeline)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Deployment](#deployment)
- [Development Methodology](#development-methodology)
- [AI-Assisted Development](#ai-assisted-development)
- [Presentation](#presentation)

---

## Live Demo

| Environment | URL |
|-------------|-----|
| **Production** | [https://talent-inbound-os.up.railway.app](https://talent-inbound-os.up.railway.app) |

> To explore the application, register a new account and complete your profile before submitting offers.

---

## Project Description

As a Senior Engineer, you receive dozens of recruiter messages every week — through LinkedIn, email, and freelance platforms. Most are spam or irrelevant. The few that matter get lost in the noise. Tracking conversations, evaluating fit, and drafting professional responses manually is time-consuming and error-prone.

**Talent Inbound OS** solves this problem by acting as an intelligent firewall and executive assistant for inbound recruiting:

1. **Paste** a recruiter message (LinkedIn, Email, freelance platforms)
2. The **AI pipeline** automatically classifies it (spam vs. real offer), extracts structured data (company, role, salary, tech stack, remote model), scores how well it matches your profile, and drafts a diplomatic response
3. **Review** the AI's work, edit the draft if needed, and track the opportunity through its lifecycle

The system enforces a **human-in-the-loop** principle: the AI prepares everything, but the user always has the final say. No message is ever auto-sent.

### Problem Statement

| Without Talent Inbound OS | With Talent Inbound OS |
|---------------------------|------------------------|
| Manually reading every recruiter message | AI classifies and filters spam automatically |
| No structured data — mental notes only | Structured extraction: company, salary, stack, role |
| No way to know if an offer fits your profile | Automated match scoring (0-100) against your preferences |
| Writing responses from scratch every time | AI-drafted responses adapted to context |
| Losing track of conversations, ghosting | Opportunity lifecycle tracking with follow-up alerts |

---

## Key Features

### Authentication & Security
- JWT-based authentication with HTTP-only cookies (access + refresh tokens)
- Password strength validation (min 8 chars, uppercase, lowercase, digit)
- Cross-user data isolation — every query is scoped to the authenticated candidate
- Secure cookie handling for cross-origin deployments (SameSite, Secure flags)

### Candidate Profile
- Professional profile: name, title, skills, salary expectations, work model preferences
- CV upload (PDF/DOCX) with text extraction for future vector-based scoring
- Configurable thresholds for follow-up and ghosting alerts
- Profile completeness gate — must fill required fields before submitting offers

### Offer Ingestion
- Copy-paste recruiter messages from any source (LinkedIn, Email, Freelance, Other)
- Two-action workflow: paste + confirm (frictionless ingestion)
- Duplicate detection — prevents re-processing the same message

### AI Agent Pipeline (6 stages)
- **Guardrail & Sanitizer** — PII cleanup, prompt-injection detection
- **Gatekeeper** — Spam vs. real offer classification (rejects noise)
- **Extractor** — Structured data extraction (company, role, salary, stack, remote, recruiter)
- **Analyst** — Match scoring (0-100) against candidate profile with detailed reasoning
- **Communicator** — Context-aware response drafts (ask for info, accept, politely decline)
- **Stage Detector** — Suggests lifecycle stage transitions based on conversation context

### Opportunity Dashboard
- Filterable by stage (Discovery, Engaging, Interviewing, Negotiating, Offer, Rejected, Ghosted)
- Sortable by date or match score
- Stale opportunity alerts (configurable threshold)
- Pagination with configurable page size
- Archive/restore functionality

### Conversational Cycle
- Review and edit AI-drafted responses before sending
- Confirm when a draft is sent — auto-advances stage from Discovery to Engaging
- Submit follow-up recruiter messages for re-analysis
- The follow-up pipeline preserves context and does not force stage changes

### Opportunity Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DISCOVERY : New offer ingested
    DISCOVERY --> ENGAGING : User confirms draft sent
    ENGAGING --> INTERVIEWING : AI detects interview scheduling
    INTERVIEWING --> NEGOTIATING : AI detects offer discussion
    NEGOTIATING --> OFFER : Formal offer received
    DISCOVERY --> REJECTED : User or AI rejects
    ENGAGING --> REJECTED : User or AI rejects
    INTERVIEWING --> REJECTED : User or AI rejects
    NEGOTIATING --> REJECTED : User or AI rejects
    ENGAGING --> GHOSTED : No response (threshold exceeded)
    INTERVIEWING --> GHOSTED : No response (threshold exceeded)
    NEGOTIATING --> GHOSTED : No response (threshold exceeded)
```

- Stage suggestions via AI (user accepts or dismisses)
- Visual stage progress indicator
- Full interaction history per opportunity

### Real-time Pipeline Feedback
- Server-Sent Events (SSE) for live pipeline progress
- Step-by-step status updates as each agent completes

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core language |
| **FastAPI** | Async REST API framework |
| **SQLAlchemy 2.0** (async) | ORM with asyncpg driver |
| **PostgreSQL 16** | Relational database |
| **Alembic** | Database migrations |
| **Pydantic v2** | Domain models, validation, settings |
| **dependency-injector** | Dependency injection container |
| **LangGraph** | AI agent orchestration (stateful graph) |
| **LangChain Core + Anthropic** | LLM integration (Claude models) |
| **structlog** | Structured logging |
| **bcrypt + python-jose** | Password hashing, JWT tokens |
| **SSE-Starlette** | Server-Sent Events for real-time progress |
| **pypdf + python-docx** | CV text extraction |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 16** (App Router) | React framework with SSR |
| **React 19** | UI library |
| **TypeScript 5** | Type safety |
| **TailwindCSS 4** | Utility-first CSS |
| **pnpm** | Package manager |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Railway** | Cloud deployment (backend + frontend + PostgreSQL) |
| **Docker** | Containerized builds |
| **GitHub** | Version control, CI trigger |

### Development Tools
| Tool | Purpose |
|------|---------|
| **Claude Code** (CLI) | AI copilot for development |
| **Speckit** | Spec-Driven Development methodology tooling |
| **Ruff** | Python linter + formatter |
| **ESLint + Prettier** | TypeScript/JS linting + formatting |
| **pytest** | Testing framework (unit, integration, e2e) |
| **testcontainers** | Integration tests with real PostgreSQL |

---

## Architecture

### High-Level Overview

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js 16 + React 19)"]
        F1[Login / Register]
        F2[Dashboard + Detail]
        F3[Ingest Page]
        F4[Profile Page]
    end

    subgraph Backend["Backend (FastAPI)"]
        API["API Layer (v1 Router)<br/>/auth · /profile · /opportunities · /interactions"]
        APP["Application Layer (Use Cases)<br/>RegisterUser · LoginUser · SubmitInteraction<br/>ConfirmDraftSent · SubmitFollowUp"]
        DOM["Domain Layer (Entities)<br/>User · CandidateProfile · Opportunity<br/>Interaction · DraftResponse · OpportunityStage"]
        INF["Infrastructure Layer (Adapters)<br/>SQLAlchemy Repos · LangGraph Pipeline · AI Agents"]
        DI["DI Container (dependency-injector)"]
    end

    DB[(PostgreSQL 16)]

    Frontend -->|"REST API + SSE<br/>(HTTP-only cookies)"| API
    API --> APP
    APP --> DOM
    DOM --> INF
    DI -.->|wires| API
    DI -.->|wires| APP
    DI -.->|wires| INF
    INF --> DB
```

### Design Principles

- **Modular Monolith** — Organized by business modules (`auth`, `profile`, `ingestion`, `pipeline`, `opportunities`), not technical layers. Each module has its own `domain/`, `application/`, `presentation/`, and `infrastructure/` layers.
- **Clean Architecture** — Dependencies point inward. Domain has no external imports. Infrastructure adapts to domain interfaces.
- **2-Model Separation** — Pydantic models for the domain, SQLAlchemy ORM models for persistence. Explicit mapping between them.
- **Dependency Injection** — All wiring happens in `container.py` using the `dependency-injector` library. No hidden globals.

---

## AI Agent Pipeline

The core differentiator of the project. When a user pastes a recruiter message, it flows through a **LangGraph** stateful graph with 6 sequential agents:

```mermaid
graph TD
    MSG["Raw Recruiter Message"]

    MSG --> G1

    G1["1. Guardrail & Sanitizer<br/>🛡️ Prompt injection detection + PII cleanup"]
    G1 --> G2

    G2["2. Gatekeeper<br/>🚦 Spam vs. real offer classification"]
    G2 -->|Real offer| G3
    G2 -->|Spam / Not an offer| REJ["❌ Rejected"]

    G3["3. Extractor<br/>📋 Company · Role · Salary · Stack · Remote · Recruiter"]
    G3 --> G4

    G4["4. Analyst<br/>📊 Match score (0-100) vs. Candidate Profile"]
    G4 --> G5

    G5["5. Communicator<br/>✉️ Drafts context-aware response"]
    G5 --> G6

    G6["6. Stage Detector<br/>🔄 Suggests lifecycle stage transition"]
    G6 --> DONE["✅ Opportunity ready for review"]

    style REJ fill:#fee2e2,stroke:#ef4444
    style DONE fill:#dcfce7,stroke:#22c55e
```

Each agent is powered by **Claude** (Anthropic) models via LangChain:
- **Fast model** (Claude Haiku 4.5): Guardrail, Gatekeeper, Stage Detector
- **Smart model** (Claude Sonnet 4.5): Extractor, Analyst, Communicator

The pipeline supports two modes:
- **Initial analysis**: Full pipeline (all 6 agents) for a new recruiter message
- **Follow-up analysis**: Skips the Gatekeeper (already validated) and re-evaluates with conversation context

---

## Project Structure

```
talent-inbound-os/
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml                  # Python dependencies & tooling config
│   ├── alembic/                        # Database migrations
│   │   └── versions/                   # 7 migration files
│   ├── src/talent_inbound/
│   │   ├── main.py                     # FastAPI app + startup
│   │   ├── config.py                   # Settings (pydantic-settings)
│   │   ├── container.py                # DI wiring (dependency-injector)
│   │   ├── cli.py                      # Admin CLI (password reset)
│   │   ├── api/v1/router.py            # API router aggregation
│   │   ├── shared/                     # Cross-cutting: middleware, auth, base models
│   │   └── modules/
│   │       ├── auth/                   # Registration, login, JWT, logout
│   │       ├── profile/                # Candidate profile CRUD, CV upload
│   │       ├── ingestion/              # Message ingestion + duplicate detection
│   │       ├── pipeline/               # LangGraph orchestration + 6 AI agents
│   │       │   ├── application/        # RunPipeline, RunFollowUpPipeline use cases
│   │       │   ├── domain/             # PipelineState, PipelineResult
│   │       │   ├── infrastructure/
│   │       │   │   ├── agents/         # guardrail, gatekeeper, extractor,
│   │       │   │   │                   # analyst, communicator, stage_detector
│   │       │   │   ├── prompts/        # .txt prompt templates per agent
│   │       │   │   └── langgraph_pipeline.py  # Graph definition
│   │       │   └── presentation/       # SSE endpoint for real-time progress
│   │       └── opportunities/          # Opportunity CRUD, stages, drafts, stale detection
│   └── tests/                          # 53 test files
│       ├── unit/                       # 130 unit tests
│       ├── integration/                # 9 integration tests (testcontainers)
│       └── e2e/                        # 28 end-to-end API tests
├── frontend/
│   ├── Dockerfile
│   ├── package.json                    # Next.js 16 + React 19 + TailwindCSS 4
│   ├── next.config.ts
│   └── src/
│       ├── app/
│       │   ├── login/page.tsx          # Login page
│       │   ├── register/page.tsx       # Registration page
│       │   ├── dashboard/page.tsx      # Opportunity list + filters + pagination
│       │   ├── dashboard/[id]/page.tsx # Opportunity detail + interactions
│       │   ├── ingest/page.tsx         # Paste recruiter message
│       │   └── profile/page.tsx        # Profile editor + CV upload
│       ├── components/                 # Reusable UI components
│       ├── hooks/                      # Custom hooks (opportunities, pipeline SSE, profile gate)
│       └── lib/api.ts                  # API client with cookie auth
├── specs/001-mvp-platform-core/        # SDD artifacts (spec, plan, tasks, contracts)
├── .specify/                           # Speckit system (constitution, templates)
├── .context/                           # Project governance docs (local only)
└── CLAUDE.md                           # AI copilot instructions
```

**Key numbers:**
- 117 Python source files, 28 TypeScript/TSX files
- 53 test files with 167 tests (130 unit + 9 integration + 28 e2e)
- 7 database migrations
- 6 AI agents with dedicated prompt templates
- 20 commits across 11 days of development

---

## Installation & Setup

### Prerequisites

- **Python 3.11+** with `pip`
- **Node.js 20+** with **pnpm** (`npm install -g pnpm`)
- **PostgreSQL 16** running locally (or via Docker)
- **Anthropic API key** (for Claude models — [get one here](https://console.anthropic.com/))

### 1. Clone the repository

```bash
git clone https://github.com/CristopherRL/talent-inbound-os.git
cd talent-inbound-os
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your values:
#   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/talent_inbound
#   ANTHROPIC_API_KEY=sk-ant-...
#   JWT_SECRET_KEY=<generate with: openssl rand -hex 32>

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn src.talent_inbound.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Frontend setup

```bash
cd frontend

# Install dependencies (use pnpm, NOT npm)
pnpm install

# Start the development server
pnpm dev
```

The frontend runs at `http://127.0.0.1:3000` and the backend API at `http://127.0.0.1:8000`.

> **Note (Windows):** Always use `127.0.0.1` instead of `localhost` to avoid IPv6 resolution issues.

### 4. Running tests

```bash
cd backend

# Unit tests (fast, no external dependencies)
python -m pytest tests/unit -v

# Integration tests (requires Docker for testcontainers)
python -m pytest tests/integration -v

# E2E tests (requires running PostgreSQL)
python -m pytest tests/e2e -v

# All tests with coverage
python -m pytest --cov=src --cov-report=term-missing
```

### 5. Admin utilities

```bash
# Reset a user's password (CLI command)
cd backend
python -m talent_inbound.cli reset-password user@example.com NewPassword123
```

---

## Deployment

The application is deployed on **Railway** with the following services:

```mermaid
graph LR
    USER["User<br/>🌐 Browser"] -->|HTTPS| FE["Frontend<br/>Next.js 16<br/>(Docker)"]
    FE -->|"REST API + SSE<br/>(HTTPS + cookies)"| BE["Backend<br/>FastAPI<br/>(Docker)"]
    BE -->|asyncpg| DB[(PostgreSQL 16<br/>Railway Managed)]
    GH["GitHub<br/>push to main"] -->|auto-deploy| RW["Railway"]
    RW --> FE
    RW --> BE
    RW --> DB
```

| Service | Source | Notes |
|---------|--------|-------|
| **Backend** | `backend/Dockerfile` | Runs Alembic migrations on startup, then uvicorn |
| **Frontend** | `frontend/Dockerfile` | Multi-stage build, Next.js standalone output |
| **PostgreSQL** | Railway managed | Provisioned as a Railway add-on |

### Key Environment Variables

**Backend:**
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Must use `postgresql+asyncpg://` scheme |
| `ANTHROPIC_API_KEY` | Claude API key |
| `JWT_SECRET_KEY` | Secret for JWT signing |
| `CORS_ORIGINS` | Comma-separated allowed origins (exact frontend URL) |
| `ENVIRONMENT` | `production` for secure cookies, `development` for local |

**Frontend:**
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Full backend URL (build-time — requires rebuild on change) |

### Deployment steps

1. Create a Railway project with PostgreSQL
2. Add a backend service pointing to `backend/Dockerfile` — set env vars
3. Add a frontend service pointing to `frontend/Dockerfile` — set `NEXT_PUBLIC_API_URL`
4. Configure CORS on the backend to match the frontend's public URL
5. Railway auto-deploys on every push to `main`

For detailed step-by-step instructions, see `.context/Railway Deployment Guide.md`.

---

## Development Methodology

### Spec-Driven Development (SDD)

This project follows a strict **no code without a spec** methodology, enforced through **Speckit** — a custom tooling system integrated with Claude Code:

```mermaid
graph LR
    S["/speckit.specify<br/>📝 Spec"]
    C["/speckit.clarify<br/>❓ Clarify"]
    P["/speckit.plan<br/>📐 Plan"]
    T["/speckit.tasks<br/>📋 Tasks"]
    A["/speckit.analyze<br/>🔍 Analyze"]
    I["/speckit.implement<br/>⚙️ Implement"]

    S --> C --> P --> T --> A --> I
    A -->|Issues found| S
```

1. **Specify** (`/speckit.specify`): Define the feature in a structured specification — user stories, acceptance criteria, edge cases, security considerations
2. **Clarify** (`/speckit.clarify`): Identify underspecified areas and encode answers back
3. **Plan** (`/speckit.plan`): Generate the implementation plan — data model, API contracts, component design, dependency graph
4. **Tasks** (`/speckit.tasks`): Break down the plan into dependency-ordered, atomic tasks
5. **Analyze** (`/speckit.analyze`): Cross-artifact consistency check (spec ↔ plan ↔ tasks)
6. **Implement** (`/speckit.implement`): Execute tasks one by one with automated quality checks

All SDD artifacts are preserved in `specs/001-mvp-platform-core/`:

| Artifact | Description |
|----------|-------------|
| `spec.md` | Feature specification with 7 user stories |
| `plan.md` | Implementation plan with architectural decisions |
| `tasks.md` | 158 dependency-ordered tasks across 11 phases |
| `data-model.md` | Entity-relationship model |
| `contracts/` | API contract definitions |
| `research.md` | Technical research notes |
| `checklists/` | Quality checklists per phase |
| `quickstart.md` | Quick reference for the spec |

### Project Constitution

A living governance document (`.specify/memory/constitution.md`) with 7 core principles that every design decision must comply with:

1. **Data Privacy First** — PII sanitized before external LLM calls
2. **Data First** — Missing critical data flagged as INCOMPLETE_INFO before scoring
3. **High-Signal, Low-Noise** — Aggressively filter spam; <2% false-positive rate
4. **Human-in-the-Loop** — Never auto-send messages; user always reviews
5. **Frictionless Ingestion** — Copy-paste primary entry (max 2 user actions)
6. **Observability & Safety** — Full traceability of every agent step
7. **Professional Tone** — All generated content reflects Senior/Staff-level standing

---

## AI-Assisted Development

This project was built using **Claude Code** (Anthropic's CLI agent) as an AI copilot throughout the entire development lifecycle — from specification to deployment.

### How Claude Code was used

| Phase | How AI assisted |
|-------|----------------|
| **Specification** | Speckit slash commands driven by Claude Code to generate and refine specs |
| **Architecture** | Design decisions discussed interactively — Clean Architecture, module boundaries, DI patterns |
| **Implementation** | Code generation guided by specs, with human review and iteration on every piece |
| **Testing** | Test scaffolding and edge case identification |
| **Debugging** | Real-time diagnosis of deployment issues (CORS, cookies, Docker) |
| **Documentation** | Context7 MCP for up-to-date library docs; structured knowledge in CLAUDE.md |

### Key AI development artifacts

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project-level instructions for the AI copilot — architecture rules, domain language, conventions |
| `.specify/memory/constitution.md` | Governance principles the AI must follow |
| `.context/Session Tracker.md` | Session continuity — tracks where we left off between conversations |
| `.context/conversation_history/` | Exported conversation logs documenting the development process |
| `specs/001-mvp-platform-core/` | All SDD artifacts generated through AI-assisted workflow |

### Lessons learned

- **Spec-first approach** prevents scope creep and ensures the AI stays focused on what was agreed
- **Constitution as guardrails** keeps AI-generated code aligned with project values (security, privacy, UX)
- **Session tracking** is essential for multi-session AI development — without it, context is lost
- **Context7 MCP** for documentation lookup prevents hallucinated APIs and outdated patterns
- **Human-in-the-loop** applies to AI-assisted development too — every decision was reviewed and understood

---

## Presentation

> Slides: _[TODO: Add link to presentation slides]_

---

## License

MIT

---

## Author

**Cristopher RL**
Master en Desarrollo con IA — BIG School (2026)
