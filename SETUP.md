# BizMind AI — Setup & Installation Guide

This document covers the complete local setup, environment configuration, and database provisioning for the BizMind AI platform. 

For architecture and feature details, return to the main [README.md](./README.md).

---

## 5-Command Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/yourorg/bizmind-ai && cd bizmind-ai

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your Supabase, Google AI, and Redis credentials

# 3. Run the Supabase SQL migrations (paste into Supabase SQL Editor)
# See "Supabase SQL" section below

# 4. Start backend + Redis with Docker Compose
docker-compose up --build -d

# 5. Start the frontend dev server
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000** — backend Swagger docs at **http://localhost:8000/docs**

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key (server only) |
| `GOOGLE_API_KEY` | ✅ | Google AI Studio API key for Gemini |
| `REDIS_URL` | ⚠️ | Redis URL (optional, falls back gracefully) |
| `GEMINI_MODEL` | — | Default: `gemini-3.0-flash` |
| `EMBEDDING_MODEL` | — | Default: `all-MiniLM-L6-v2` |
| `RAG_SIMILARITY_THRESHOLD` | — | Default: `0.35` |

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

### Serverless Deployment (Modal)
If you prefer not to manage Docker infrastructure, you can deploy the backend infinitely scalable on [Modal.com](https://modal.com) for pennies.

```bash
# 1. Login to Modal
modal setup

# 2. Upload your .env file to a secure Modal vault
modal secret create bizmind-secrets --env-file .env

# 3. Test locally (hot-reloading cloud container)
modal serve modal_app.py

# 4. Deploy permanently to the cloud
modal deploy modal_app.py
```
