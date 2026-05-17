# BizMind AI 🧠

> **AI Business Assistant Platform for SMEs** — FastAPI backend + Next.js frontend powered by Gemini 2.0 Flash, Supabase pgvector RAG, and Redis caching.

---

## 5-Command Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/yourorg/bizmind-ai && cd bizmind-ai

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your Supabase, Google AI, and Redis credentials

# 3. Run the Supabase SQL migrations (paste into Supabase SQL Editor)
# See "Supabase Tables" section below

# 4. Start backend + Redis with Docker Compose
docker-compose up --build -d

# 5. Start the frontend dev server
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000** — backend Swagger docs at **http://localhost:8000/docs**

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
            │  Gemini 2.0 Flash│
            │  text-embed-004 │
            └─────────────────┘
```

---

## Supabase SQL — Run These in SQL Editor

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  filename TEXT NOT NULL,
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own documents" ON documents
  FOR ALL USING (auth.uid() = user_id);

-- Document Chunks (pgvector)
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(384),
  chunk_index INTEGER NOT NULL
);
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own document chunks" ON document_chunks
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM documents d
      WHERE d.id = document_chunks.document_id AND d.user_id = auth.uid()
    )
  );
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Leads
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  company TEXT,
  need TEXT,
  status TEXT DEFAULT 'cold' CHECK (status IN ('hot', 'warm', 'cold')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own leads" ON leads
  FOR ALL USING (auth.uid() = user_id);

-- Conversations
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  message_count INTEGER DEFAULT 0
);
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own conversations" ON conversations
  FOR ALL USING (auth.uid() = user_id);

-- Messages
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own messages" ON messages
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM conversations c
      WHERE c.id = messages.conversation_id AND c.user_id = auth.uid()
    )
  );

-- Workflow Logs
CREATE TABLE workflow_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workflow_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
  duration_ms INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE workflow_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own workflow logs" ON workflow_logs
  FOR ALL USING (auth.uid() = user_id);

-- User Memory
CREATE TABLE user_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, key)
);
ALTER TABLE user_memory ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own memory" ON user_memory
  FOR ALL USING (auth.uid() = user_id);

-- AI Usage
CREATE TABLE ai_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  conversation_id UUID,
  tokens_used INTEGER DEFAULT 0,
  rag_hit BOOLEAN DEFAULT FALSE,
  similarity_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own AI usage" ON ai_usage
  FOR ALL USING (auth.uid() = user_id);

-- RPC: pgvector similarity search
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector(384),
  match_count INT,
  p_user_id UUID
)
RETURNS TABLE (
  id UUID,
  document_id UUID,
  content TEXT,
  similarity FLOAT,
  document_filename TEXT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    dc.id,
    dc.document_id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity,
    d.filename AS document_filename
  FROM document_chunks dc
  JOIN documents d ON d.id = dc.document_id
  WHERE d.user_id = p_user_id
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- RPC: Increment conversation message count
CREATE OR REPLACE FUNCTION increment_message_count(conv_id UUID, delta INT)
RETURNS void
LANGUAGE sql
AS $$
  UPDATE conversations SET message_count = message_count + delta WHERE id = conv_id;
$$;
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

## Development

### Backend (uv)
```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev  # http://localhost:3000
```

### Docker (production-like)
```bash
docker-compose up --build
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key (server only) |
| `GOOGLE_API_KEY` | ✅ | Google AI Studio API key for Gemini |
| `REDIS_URL` | ⚠️ | Redis URL (optional, falls back gracefully) |
| `GEMINI_MODEL` | — | Default: `gemini-2.0-flash` |
| `EMBEDDING_MODEL` | — | Default: `models/text-embedding-004` |
| `RAG_SIMILARITY_THRESHOLD` | — | Default: `0.35` |

---

## Known Limitations

1. **Redis is optional** — If Redis is not running, the cache layer is disabled and all RAG queries go directly to Gemini. No data loss, just slower responses.

2. **CRM export writes locally** — `POST /workflows/crm-export` exports to `exports/leads_export.json`. In production, this would POST to a real CRM API (Salesforce, HubSpot, Pipedrive).

3. **Lead notifier is stubbed** — `POST /workflows/lead-notify` logs the event but does not send real notifications. Production would integrate SendGrid (email) or Slack webhooks.

4. **Auth is email/password only** — OAuth providers (Google, GitHub) are the next step. Supabase supports them via `supabase.auth.signInWithOAuth()`.

5. **Short-term memory is in-process** — Stored in a Python dict, lost on server restart. Production would use Redis or a persistent store.

6. **Token counting is approximate** — Gemini's SDK doesn't always expose exact token counts. The `ai_usage.tokens_used` column is stored as 0 and would need Gemini's `count_tokens()` API in production.

7. **`agno` dependency** — The `pyproject.toml` includes `agno` but the current implementation uses the Gemini SDK directly for agent logic, which is more reliable for the MVP. The Agno orchestration layer can be wired in as a next step.

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
