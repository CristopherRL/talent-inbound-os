# Talent Inbound OS -- Frontend

The frontend for **Talent Inbound OS**, an AI-powered inbound recruiting management system designed for Senior Engineers. It provides a web interface for ingesting recruiter messages, reviewing AI-analyzed opportunities, managing draft responses, and tracking the full lifecycle of each offer.

---

## Table of Contents

1. [Frontend Overview](#1-frontend-overview)
2. [User Workflows](#2-user-workflows)
3. [Project Structure](#3-project-structure)
4. [Component Library](#4-component-library)
5. [Development](#5-development)

---

## 1. Frontend Overview

| Layer            | Technology                                  |
| ---------------- | ------------------------------------------- |
| Framework        | Next.js 16 (App Router)                     |
| UI Library       | React 19                                    |
| Language         | TypeScript 5                                |
| Styling          | TailwindCSS 4                               |
| Component System | shadcn/ui (Radix primitives + Tailwind)     |
| Charts           | Recharts 3                                  |
| Icons            | Lucide React                                |
| Package Manager  | **pnpm** (do NOT use npm)                   |
| Authentication   | Cookie-based (HTTP-only cookies set by backend) |

Key architectural decisions:

- **App Router** -- all pages live under `src/app/` and use React Server Components where possible.
- **Cookie-based auth** -- the backend sets HTTP-only JWT cookies on login. The frontend sends `credentials: "include"` on every fetch. There is no client-side token storage.
- **Proxy (middleware)** -- Next.js 16 renamed middleware to `proxy.ts`. It handles route protection by checking for the `access_token` cookie in local development. In cross-domain production deployments, auth falls back to server-side validation on each API call.
- **SSE for real-time progress** -- the ingestion pipeline streams `agent_progress` and `pipeline_complete` events over Server-Sent Events.

---

## 2. User Workflows

### Registration and Login

1. Navigate to `/register` -- create an account with email and password. Password requirements: minimum 8 characters, at least one uppercase letter, one lowercase letter, and one digit.
2. Navigate to `/login` -- enter credentials. On success the backend sets HTTP-only cookies (`access_token` and `refresh_token`).
3. Sessions persist via automatic cookie refresh. There is no manual token management on the client side.
4. If a session expires (401 response on a non-auth endpoint), the API client automatically redirects the user to `/login`.

### Profile Setup (required before submitting offers)

1. Navigate to `/profile`.
2. Fill in all required fields: display name, professional title, skills, minimum salary, preferred currency, work model, preferred locations, and target industries.
3. Upload a CV (PDF or DOCX). The backend extracts the text content and stores it.
4. Click **"Extract Skills from CV"** -- the AI analyzes the CV text and suggests skills as interactive chips.
5. Skills can be added manually via the "+" button or removed by clicking the "X" on each chip. Changes are auto-saved to the backend.
6. The profile must be complete before the system allows offer submission. The `use-profile-gate` hook enforces this gate across protected pages.

### Submitting a New Offer

1. Navigate to `/ingest` (New Offer page).
2. Select the message source: LinkedIn, Email, Freelance Platform, or Other.
3. Paste the recruiter's message into the text area.
4. Click **"Submit"** to trigger the AI pipeline.
5. A real-time SSE progress indicator shows each agent completing its step: Guardrail, Gatekeeper, Extractor, Language Detector, Analyst, Communicator, and Stage Detector.
6. On completion, the user is redirected to the newly created opportunity's detail page.
7. If the same message was already submitted, duplicate detection returns an error and links to the existing opportunity.

### Understanding the Opportunity Card (Dashboard)

The dashboard (`/dashboard`) displays all opportunities as cards. Each card shows:

- **Company name and role title** -- extracted by the AI pipeline.
- **Match score** (0-100) with color coding: green for scores above 70, yellow for 40-70, and red below 40. These thresholds are configurable via `NEXT_PUBLIC_SCORING_THRESHOLD_HIGH` and `NEXT_PUBLIC_SCORING_THRESHOLD_MEDIUM` environment variables.
- **Current stage badge** -- one of DISCOVERY, ENGAGING, INTERVIEWING, NEGOTIATING, OFFER, REJECTED, or GHOSTED.
- **Tech stack chips** -- the technologies mentioned in the offer.
- **Missing fields warning** -- displayed when critical data could not be extracted (salary, role, tech stack).
- **Time since creation** -- relative timestamp.

Cards are filterable by stage and sortable by date or score.

### Opportunity Detail Page

The detail page (`/dashboard/[id]`) provides a comprehensive view:

- **Extracted data** -- salary range, work model (remote/hybrid/onsite), recruiter information, tech stack, client company, and location.
- **Match score with reasoning** -- the numeric score plus a text explanation of how it was calculated (salary fit, stack overlap, work model, location).
- **Stage progress indicator** -- a visual step bar showing the current position in the lifecycle.
- **Interaction timeline** -- chronological list of all recruiter messages, candidate responses, and stage transitions.
- **Stage suggestion banner** -- when the AI suggests a stage change (e.g., detecting interview scheduling language), a banner and modal appear for the user to accept or dismiss.
- **Actions** -- change stage manually, archive or unarchive, and delete the opportunity.

### Draft Response Generation

1. In the opportunity detail page, the **"Draft Responses"** section is available.
2. Select a response type: Express Interest, Request Info, or Decline.
3. Select the language: Auto-detect (uses the pipeline-detected language), English, or Spanish.
4. Optionally provide additional instructions (e.g., "mention my experience with Azure" or "ask about remote flexibility").
5. Click **"Generate Draft"** -- the AI creates a context-aware response considering the full conversation history, extracted data, and the candidate profile.
6. The draft appears as an editable card. The user can modify the text freely.
7. Mark a draft as **"Final"** to indicate it is the chosen version. Non-final drafts are hidden when a final sibling exists.
8. Click **"Confirm Sent"** to record that the response was sent. This action:
   - Records a `CANDIDATE_RESPONSE` interaction in the timeline.
   - Auto-advances the stage from DISCOVERY to ENGAGING (if this is the first confirmed response).
   - Switches the view to an "Awaiting Recruiter Reply" state with a follow-up form.

### Language Detection

- During ingestion, the AI pipeline automatically detects the recruiter's language (English or Spanish).
- The detected language is stored on the opportunity record.
- When generating a draft with "Auto-detect" selected, the system uses the stored language to produce a response in the same language as the recruiter.
- The user can override this and force English or Spanish regardless of detection.
- For older opportunities where language was not detected, the LLM infers the appropriate language from the conversation context.

### Recruiter-User Conversation Workflow

1. **Recruiter sends a message** -- the user pastes it into the system (initial ingestion or follow-up via the follow-up form).
2. **AI processes the message** -- extracts structured data, scores the match, detects language, and generates a draft response.
3. **User reviews the draft** -- edits it if needed, then marks it as final.
4. **User confirms the message was sent** -- the stage advances and the view switches to "Awaiting Follow-up."
5. **Recruiter replies** -- the user pastes the new message as a follow-up. The pipeline re-runs with the full conversation context.
6. **The cycle repeats** until a terminal stage is reached (OFFER, REJECTED, or GHOSTED).

### Stage Lifecycle

Stages progress through the following flow:

```
DISCOVERY --> ENGAGING --> INTERVIEWING --> NEGOTIATING --> [OFFER | REJECTED | GHOSTED]
```

- **Automatic transitions**: DISCOVERY advances to ENGAGING when the user confirms that their first draft response was sent.
- **AI-suggested transitions**: The Stage Detector agent may suggest a transition (e.g., "move to INTERVIEWING" after detecting interview scheduling language in a recruiter message). The user sees an inline banner and a confirmation modal to accept or dismiss the suggestion.
- **Manual transitions**: The user can change the stage via a dropdown in the Actions section. Unusual transitions (such as skipping stages) trigger a confirmation prompt.
- **Terminal stages**: OFFER, REJECTED, and GHOSTED are end states. Opportunities in terminal stages can be archived.

### Match Score

- The match score is only generated when **all required fields** are successfully extracted (no missing fields).
- The score ranges from 0 to 100 and compares the opportunity against the candidate's profile.
- Scoring factors include: salary fit (delta between offer and minimum), tech stack overlap, work model match, and location preferences.
- The score is displayed with color coding and accompanied by detailed reasoning text explaining each factor.
- If required fields are missing, the score displays as "N/A" with a warning indicating which fields are absent.

### Stale Opportunity Alerts

- The dashboard displays a warning banner for opportunities that have had no interaction beyond a configurable threshold (default: 7 days).
- This feature helps prevent unintentional ghosting by reminding the user to follow up on stagnant conversations.

---

## 3. Project Structure

```
frontend/
├── Dockerfile                # Multi-stage production build (standalone output)
├── package.json              # Dependencies and scripts (pnpm)
├── src/
│   ├── app/
│   │   ├── layout.tsx            # Root layout (Geist font, metadata)
│   │   ├── page.tsx              # Landing / redirect
│   │   ├── login/page.tsx        # Login page
│   │   ├── register/page.tsx     # Registration page
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Opportunity list with filters and sorting
│   │   │   └── [id]/page.tsx     # Opportunity detail (timeline, drafts, actions)
│   │   ├── ingest/page.tsx       # Paste recruiter message + SSE progress
│   │   ├── profile/page.tsx      # Profile editor, CV upload, skill extraction
│   │   ├── analytics/page.tsx    # Offer analytics dashboard (charts)
│   │   ├── chat/page.tsx         # Conversational AI chat interface
│   │   └── next-steps/page.tsx   # Next steps guidance
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components + custom shared UI
│   │   │   ├── Navbar.tsx            # Shared navigation bar
│   │   │   ├── Toast.tsx             # Toast notifications + useToast hook
│   │   │   ├── badge.tsx             # Badge component
│   │   │   ├── button.tsx            # Button component
│   │   │   ├── card.tsx              # Card component
│   │   │   ├── dialog.tsx            # Dialog / modal component
│   │   │   ├── dropdown-menu.tsx     # Dropdown menu component
│   │   │   ├── input.tsx             # Input component
│   │   │   ├── select.tsx            # Select component
│   │   │   ├── sheet.tsx             # Sheet (slide-over panel) component
│   │   │   ├── tabs.tsx              # Tabs component
│   │   │   ├── textarea.tsx          # Textarea component
│   │   │   └── tooltip.tsx           # Tooltip component
│   │   ├── opportunity/          # Opportunity-specific components
│   │   │   ├── DraftResponseCard.tsx     # Editable draft with final/confirm actions
│   │   │   ├── FollowUpForm.tsx          # Follow-up message submission form
│   │   │   ├── MatchScoreCard.tsx        # Score display with color coding
│   │   │   ├── OpportunityCard.tsx       # Dashboard card for each opportunity
│   │   │   ├── StageBadge.tsx            # Colored badge for stage display
│   │   │   ├── StageProgressIndicator.tsx # Visual step bar for stage lifecycle
│   │   │   ├── StageSuggestionBanner.tsx  # Inline banner for AI stage suggestions
│   │   │   ├── StageSuggestionModal.tsx   # Confirmation modal for stage changes
│   │   │   └── Timeline.tsx              # Chronological interaction history
│   │   ├── pipeline/
│   │   │   └── PipelineProgress.tsx  # SSE-driven progress indicator
│   │   └── profile/
│   │       ├── CVUpload.tsx          # CV file upload with extraction dialog
│   │       ├── ProfileForm.tsx       # Profile editor form
│   │       └── SkillChips.tsx        # Interactive skill chip input
│   ├── config/
│   │   └── scoring.ts            # Configurable scoring thresholds (env vars)
│   ├── hooks/
│   │   ├── use-opportunities.ts      # API calls for opportunities, drafts, follow-ups
│   │   ├── use-pipeline-progress.ts  # SSE hook for real-time pipeline progress
│   │   └── use-profile-gate.ts       # Ensures profile is complete before proceeding
│   ├── lib/
│   │   ├── api.ts                # Base API client (GET/POST/PUT/PATCH/DELETE/Upload)
│   │   ├── sse.ts                # SSE EventSource utility for pipeline streaming
│   │   └── utils.ts              # cn() utility for className merging (clsx + tailwind-merge)
│   └── proxy.ts                  # Route protection proxy (renamed from middleware in Next.js 16)
```

---

## 4. Component Library

### shadcn/ui Components

These are auto-generated via the shadcn CLI and live in `src/components/ui/`. They are built on Radix UI primitives and styled with TailwindCSS:

| Component       | File                | Purpose                                   |
| --------------- | ------------------- | ----------------------------------------- |
| Badge           | `badge.tsx`         | Status labels and tags                    |
| Button          | `button.tsx`        | Primary action trigger                    |
| Card            | `card.tsx`          | Content container with header and footer  |
| Dialog          | `dialog.tsx`        | Modal dialogs and confirmations           |
| Dropdown Menu   | `dropdown-menu.tsx` | Context menus and action menus            |
| Input           | `input.tsx`         | Text input fields                         |
| Select          | `select.tsx`        | Single-value dropdown selector            |
| Sheet           | `sheet.tsx`         | Slide-over side panels                    |
| Tabs            | `tabs.tsx`          | Tabbed content switcher                   |
| Textarea        | `textarea.tsx`      | Multi-line text input                     |
| Tooltip         | `tooltip.tsx`       | Hover-triggered contextual hints          |

### Custom Shared Components

| Component       | File                | Purpose                                   |
| --------------- | ------------------- | ----------------------------------------- |
| Navbar          | `ui/Navbar.tsx`     | Top navigation bar with links and logout  |
| Toast           | `ui/Toast.tsx`      | Toast notifications with `useToast` hook  |

### Domain Components -- Opportunity

| Component                | File                                      | Purpose                                    |
| ------------------------ | ----------------------------------------- | ------------------------------------------ |
| OpportunityCard          | `opportunity/OpportunityCard.tsx`          | Dashboard card (score, stage, stack, time)  |
| DraftResponseCard        | `opportunity/DraftResponseCard.tsx`        | Editable AI draft with final/confirm flow  |
| FollowUpForm             | `opportunity/FollowUpForm.tsx`             | Follow-up message paste and submission     |
| MatchScoreCard           | `opportunity/MatchScoreCard.tsx`           | Score display with color coding + reasoning|
| StageBadge               | `opportunity/StageBadge.tsx`               | Colored badge for lifecycle stage          |
| StageProgressIndicator   | `opportunity/StageProgressIndicator.tsx`   | Visual step bar across all stages          |
| StageSuggestionBanner    | `opportunity/StageSuggestionBanner.tsx`    | Inline AI suggestion banner                |
| StageSuggestionModal     | `opportunity/StageSuggestionModal.tsx`     | Confirmation modal for stage transitions   |
| Timeline                 | `opportunity/Timeline.tsx`                 | Chronological list of all interactions     |

### Domain Components -- Profile

| Component   | File                      | Purpose                                    |
| ----------- | ------------------------- | ------------------------------------------ |
| CVUpload    | `profile/CVUpload.tsx`    | File upload for CV with extraction dialog  |
| ProfileForm | `profile/ProfileForm.tsx` | Full profile editor form                   |
| SkillChips  | `profile/SkillChips.tsx`  | Interactive skill chip input (add/remove)  |

### Domain Components -- Pipeline

| Component        | File                            | Purpose                              |
| ---------------- | ------------------------------- | ------------------------------------ |
| PipelineProgress | `pipeline/PipelineProgress.tsx` | SSE-driven agent completion tracker  |

---

## 5. Development

### Prerequisites

- **Node.js** 20 or later
- **pnpm** (install globally: `npm install -g pnpm`)
- The backend must be running for API calls and authentication to work

### Installation

```bash
pnpm install
```

### Running the Development Server

```bash
pnpm dev
```

The application starts at **http://127.0.0.1:3000**.

> **Windows note:** Always use `127.0.0.1` instead of `localhost` to avoid IPv6 resolution issues on Windows.

### Building for Production

```bash
pnpm build
```

The build produces a standalone output suitable for containerized deployment.

### Linting

```bash
pnpm lint
```

Uses ESLint 9 with `eslint-config-next` and Prettier integration.

### Environment Variables

| Variable                                | Required | Default                   | Notes                                    |
| --------------------------------------- | -------- | ------------------------- | ---------------------------------------- |
| `NEXT_PUBLIC_API_URL`                   | Yes      | `http://127.0.0.1:8000`  | Backend API base URL. **Build-time variable** -- changing it requires a full rebuild, not just a restart. |
| `NEXT_PUBLIC_SCORING_THRESHOLD_HIGH`    | No       | `70`                      | Score >= this value is displayed as green (strong match).  |
| `NEXT_PUBLIC_SCORING_THRESHOLD_MEDIUM`  | No       | `40`                      | Score >= this value is displayed as yellow (moderate match). |

### Docker

The project includes a multi-stage Dockerfile for production deployment:

```bash
docker build -t talent-inbound-frontend .
docker run -p 3000:3000 talent-inbound-frontend
```

Set `NEXT_PUBLIC_API_URL` at build time:

```bash
docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com -t talent-inbound-frontend .
```
