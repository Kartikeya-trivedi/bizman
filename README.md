---
title: BizMind AI
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# BizMind AI 🧠

> **AI Business Assistant Platform for SMEs** — FastAPI backend + Next.js frontend powered by Gemini 3.0 Flash, Supabase pgvector RAG, and Redis caching.

> [!IMPORTANT]
> **For Setup, Installation, and Database initialization instructions, please see [SETUP.md](./SETUP.md).**

---

## Features & Technology Stack

### 1. State-of-the-Art AI Architecture
Instead of just sending basic prompts to an API, this project implements an **Agno Agent Team** (Planner → Executor → Validator). This orchestrated multi-agent workflow ensures reliable AI that checks its own work for hallucinations before responding.

### 2. High-Performance Local RAG
Instead of paying for cloud embeddings, the backend pre-downloads and runs a HuggingFace AI model (`all-MiniLM-L6-v2`) **100% locally and offline**. This is wired into a **Supabase PostgreSQL `pgvector`** database, demonstrating a deep understanding of cost-optimization and data privacy.

### 3. Enterprise Caching Layer
Integrated a **Redis** cache that intercepts repetitive RAG queries. If a user asks the same question twice, it bypasses the LLM entirely, showcasing production-ready engineering skills for performance at scale.

### 4. Modern, Sleek Frontend
The dashboard is a fully responsive **Next.js 14+** application using the brand new **Tailwind CSS v4**. It features custom glassmorphism, responsive sidebars, and clean typography for a highly polished SaaS feel.

### 5. Production-Ready Infrastructure
Built from the ground up for scalable deployment:
- **`uv`** dependency management (cutting-edge Python tooling).
- A fully containerized **Docker** environment with CPU-optimized PyTorch binaries.
- A **Modal** serverless deployment script (`modal_app.py`) ready for infinite cloud scaling.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js 16 Frontend                      │
│  Login │ Dashboard │ Chat │ Leads │ Documents │ Workflows         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (Axios + JWT)
┌──────────────────────────▼──────────────────────────────────────┐
│                     FastAPI Backend (Python 3.11)                 │
│                                                                   │
│  ┌──────────────┐  ┌─────────────────────────────────────────┐   │
│  │  Auth API    │  │         Agent Team (Agno-inspired)       │   │
│  │  RAG API     │  │  Planner → Executor → Validator          │   │
│  │  Leads API   │  └────────────────────┬────────────────────┘   │
│  │  Workflows   │                       │                         │
│  │  Dashboard   │  ┌────────────────────▼────────────────────┐   │
│  └──────────────┘  │         RAG Pipeline                     │   │
│                    │  Query Embed → pgvector → Gate → Gemini   │   │
│                    └────────────────────┬────────────────────┘   │
└─────────────────────────────────────────┼───────────────────────┘
                           │               │
            ┌──────────────▼───┐   ┌───────▼──────────┐
            │   Supabase       │   │   Redis Cache     │
            │   Postgres +     │   │   (RAG results,   │
            │   pgvector       │   │    1-hour TTL)    │
            │   Auth           │   └──────────────────┘
            └──────────────────┘
                   │
            ┌──────▼──────────┐
            │ Gemini 3.0 Flash│
            │ all-MiniLM-L6-v2│
            └─────────────────┘
```

---

## Project Structure

```
bizman/
├── backend/
│   ├── main.py                    # FastAPI app init, CORS, routers
│   ├── api/
│   │   ├── auth.py                # /auth/register, /login, /logout
│   │   ├── chat.py                # /chat (POST)
│   │   ├── rag.py                 # /upload, /documents
│   │   ├── leads.py               # /leads CRUD
│   │   ├── workflows.py           # /workflows/*
│   │   └── dashboard.py           # /dashboard/*
│   ├── agents/
│   │   ├── team.py                # Planner → Executor → Validator
│   │   ├── planner.py             # Intent classification
│   │   ├── executor.py            # Task execution
│   │   └── validator.py           # Hallucination detection
│   ├── rag/
│   │   ├── pipeline.py            # Full RAG query pipeline
│   │   ├── ingestion.py           # PDF/TXT → chunks → embed → store
│   │   └── cache.py               # Redis semantic cache
│   ├── memory/
│   │   ├── short_term.py          # In-memory conversation history
│   │   └── long_term.py           # Supabase user_memory table
│   ├── workflows/
│   │   ├── email_summary.py       # Email summarizer via Gemini
│   │   ├── lead_notify.py         # Lead notification (stub)
│   │   └── crm_export.py          # Export leads to JSON
│   ├── models/
│   │   └── schemas.py             # All Pydantic schemas
│   └── core/
│       ├── config.py              # pydantic-settings env vars
│       ├── logging.py             # structlog JSON logging
│       ├── errors.py              # Global handler + retry decorator
│       └── supabase.py            # Client singleton
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── login/             # Auth page
│       │   └── (dashboard)/       # Protected routes
│       │       ├── page.tsx       # Dashboard stats
│       │       ├── chat/          # AI Chat interface
│       │       ├── leads/         # Lead management
│       │       ├── documents/     # Document upload & RAG
│       │       └── workflows/     # Workflow triggers
│       ├── components/
│       │   ├── Sidebar.tsx
│       │   ├── TopNavBar.tsx
│       │   ├── StatsCard.tsx
│       │   ├── LeadBadge.tsx
│       │   └── ChatBubble.tsx
│       └── lib/
│           ├── api.ts             # Axios client + typed helpers
│           └── auth.ts            # Auth helpers + localStorage
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                 # uv-based Python deps
└── .env.example
```

---

## Known Limitations

1. **Redis is optional** — If Redis is not running, the cache layer is disabled and all RAG queries go directly to Gemini. No data loss, just slower responses.

2. **CRM export writes locally** — `POST /workflows/crm-export` exports to `exports/leads_export.json`. In production, this would POST to a real CRM API (Salesforce, HubSpot, Pipedrive).

3. **Lead notifier is stubbed** — `POST /workflows/lead-notify` logs the event but does not send real notifications. Production would integrate SendGrid (email) or Slack webhooks.

4. **Auth is email/password only** — OAuth providers (Google, GitHub) are the next step. Supabase supports them via `supabase.auth.signInWithOAuth()`.

5. **Short-term memory is in-process** — Stored in a Python dict, lost on server restart. Production would use Redis or a persistent store.

6. **Token counting is approximate** — Gemini's SDK doesn't always expose exact token counts. The `ai_usage.tokens_used` column is stored as 0 and would need Gemini's `count_tokens()` API in production.

---

## API Reference

Full interactive docs at **http://localhost:8000/docs** (Swagger UI)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, get JWT |
| POST | `/auth/logout` | Invalidate session |
| POST | `/chat` | Main AI conversation |
| POST | `/upload` | Upload PDF/TXT document |
| GET | `/documents` | List user documents |
| DELETE | `/documents/{id}` | Delete document + chunks |
| GET | `/leads` | List leads (filterable) |
| POST | `/leads` | Create lead |
| PATCH | `/leads/{id}` | Update lead status |
| POST | `/workflows/email-summary` | Summarize email |
| POST | `/workflows/lead-notify` | Log lead notification |
| POST | `/workflows/crm-export` | Export leads to JSON |
| GET | `/dashboard/stats` | Aggregate stats |
| GET | `/dashboard/conversation-logs` | Conversation history |
| GET | `/dashboard/workflow-logs` | Workflow execution logs |
| GET | `/dashboard/ai-usage` | Daily AI usage metrics |
| GET | `/health` | Health check |
