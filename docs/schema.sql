-- ==============================================================================
-- AI SaaS Workspace - PostgreSQL Schema with pgvector
-- Submission Deliverable: 03-database-design.pdf (+ schema.sql)
-- ==============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(254) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- 3. Workspaces Table (Tenant Root)
CREATE TABLE IF NOT EXISTS workspaces (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    owner_id BIGINT NOT NULL REFERENCES users (id) ON DELETE PROTECT,
    plan VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces (owner_id);

-- 4. Workspace Members Table (RBAC)
CREATE TABLE IF NOT EXISTS workspace_members (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_workspace_member UNIQUE (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_ws_member_user_ws ON workspace_members (user_id, workspace_id);

-- 5. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    uploaded_by_id BIGINT NOT NULL REFERENCES users (id) ON DELETE PROTECT,
    original_name VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
    content_hash CHAR(64) NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'ready', 'failed')),
    failure_reason TEXT NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_workspace_content_hash UNIQUE (workspace_id, content_hash)
);
CREATE INDEX IF NOT EXISTS idx_doc_ws_status ON documents (workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_doc_user_created ON documents (uploaded_by_id, created_at);

-- 6. Document Chunks Table (RAG Vector Store)
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding VECTOR(1536) NOT NULL,
    CONSTRAINT unique_doc_chunk_index UNIQUE (document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunk_workspace ON document_chunks (workspace_id);
-- Fast Approximate Nearest Neighbor (ANN) HNSW vector index using cosine distance
CREATE INDEX IF NOT EXISTS idx_chunk_embedding_hnsw 
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 7. Ask Requests Table (Audit History)
CREATE TABLE IF NOT EXISTS ask_requests (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'answered', 'unsupported', 'failed')),
    failure_code VARCHAR(40) NULL,
    provider VARCHAR(30) NOT NULL DEFAULT 'mock',
    model VARCHAR(60) NOT NULL DEFAULT '',
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    idempotency_key VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_idempotency_key UNIQUE (user_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_req_user_created ON ask_requests (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_req_ws_created ON ask_requests (workspace_id, created_at DESC);

-- 8. Request Sources Table (Citations)
CREATE TABLE IF NOT EXISTS request_sources (
    id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL REFERENCES ask_requests (id) ON DELETE CASCADE,
    chunk_id BIGINT NULL REFERENCES document_chunks (id) ON DELETE SET NULL,
    document_name VARCHAR(255) NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    similarity_score REAL NOT NULL DEFAULT 0.0,
    rank SMALLINT NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_sources_request ON request_sources (request_id);

-- 9. Plan Limits Table (Seed Configuration)
CREATE TABLE IF NOT EXISTS plan_limits (
    plan VARCHAR(20) PRIMARY KEY CHECK (plan IN ('free', 'pro')),
    daily_questions INTEGER NOT NULL DEFAULT 20,
    monthly_tokens INTEGER NOT NULL DEFAULT 100000,
    max_documents INTEGER NOT NULL DEFAULT 10,
    max_file_mb INTEGER NOT NULL DEFAULT 10
);

-- 10. Usage Records Table (Cost & Limit Tracking)
CREATE TABLE IF NOT EXISTS usage_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    request_id BIGINT NULL UNIQUE REFERENCES ask_requests (id) ON DELETE CASCADE,
    kind VARCHAR(12) NOT NULL DEFAULT 'question' CHECK (kind IN ('question', 'embedding')),
    tokens_used INTEGER NOT NULL DEFAULT 0,
    estimated_cost NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    period_day DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_usage_user_day ON usage_records (user_id, period_day);
CREATE INDEX IF NOT EXISTS idx_usage_ws_day ON usage_records (workspace_id, period_day);

-- Initial Seed Data
INSERT INTO plan_limits (plan, daily_questions, monthly_tokens, max_documents, max_file_mb)
VALUES 
    ('free', 20, 100000, 10, 10),
    ('pro', 200, 2000000, 100, 50)
ON CONFLICT (plan) DO NOTHING;
