# 03 — Database Design Specification & ERD Guide

> **Project:** AI SaaS Workspace  
> **Prepared for:** FalconXoft Weekend 2 Internship Evaluation  
> **Mandatory Rule per PDF:** *"Lucidchart ERD with PK/FK, data types, cardinality, constraints and indexes; include schema.sql or migrations and editable URL. Address file ownership and request usage records."*

---

## 1. Lucidchart ERD URL & Associated Files

* **Editable Lucidchart ERD URL:** **USER ACTION REQUIRED** — import/redraw `03 - database-design.mmd`, share it from the submitter account, then paste the authentic edit URL.
* **Exported PDF Deliverable:** `03 - database-design.pdf`
* **Executable SQL Script:** [schema.sql](file:///d:/Muaz/Programming/FX%20internship/Weekend%20Assessments/Week%20Two/AI%20SaaS%20Workspace/deliverables/01_AI_SaaS/schema.sql) *(Included in this directory)*

---

## 2. Entity-Relationship Diagram (Mermaid Visual ERD)

```mermaid
erDiagram
    USERS ||--o{ WORKSPACE_MEMBERS : "belongs to (1:N)"
    WORKSPACES ||--o{ WORKSPACE_MEMBERS : "has members (1:N)"
    WORKSPACES ||--o{ DOCUMENTS : "owns (1:N)"
    USERS ||--o{ DOCUMENTS : "uploaded_by [File Owner] (1:N)"
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : "splits into (1:N)"
    WORKSPACES ||--o{ DOCUMENT_CHUNKS : "tenant boundary (1:N)"
    WORKSPACES ||--o{ ASK_REQUESTS : "scoped within (1:N)"
    USERS ||--o{ ASK_REQUESTS : "asked by (1:N)"
    ASK_REQUESTS ||--o{ REQUEST_SOURCES : "cites (1:N)"
    DOCUMENT_CHUNKS ||--o{ REQUEST_SOURCES : "references (1:N)"
    ASK_REQUESTS ||--|| USAGE_RECORDS : "1-to-1 usage billing"
    USERS ||--o{ USAGE_RECORDS : "billed to (1:N)"
    WORKSPACES ||--o{ USAGE_RECORDS : "billed in (1:N)"

    USERS {
        bigserial id PK
        varchar email UK "Indexed"
        varchar password_hash
        varchar full_name
        boolean is_active
        timestamptz created_at
    }

    WORKSPACES {
        bigserial id PK
        varchar name
        bigint owner_id FK "References users(id)"
        varchar plan "CHECK: free, pro"
        timestamptz created_at
    }

    WORKSPACE_MEMBERS {
        bigserial id PK
        bigint workspace_id FK "ON DELETE CASCADE"
        bigint user_id FK "ON DELETE CASCADE"
        varchar role "CHECK: owner, admin, member"
        timestamptz created_at
    }

    DOCUMENTS {
        bigserial id PK
        bigint workspace_id FK "Tenant Root, ON DELETE CASCADE"
        bigint uploaded_by FK "File Owner, References users(id)"
        varchar original_name
        varchar storage_key "UUID randomized path"
        varchar mime_type "CHECK: application/pdf, text/plain"
        bigint size_bytes "CHECK: > 0 AND <= 10485760"
        char content_hash "SHA-256 for duplicate check"
        varchar status "CHECK: uploaded, processing, ready, failed"
        text failure_reason "Nullable"
        integer page_count
        timestamptz created_at
        timestamptz updated_at
    }

    DOCUMENT_CHUNKS {
        bigserial id PK
        bigint document_id FK "ON DELETE CASCADE"
        bigint workspace_id FK "Denormalized for zero-leak filter"
        integer chunk_index "Order in document"
        integer page_number "Page number for citations"
        text content "Chunk text snippet"
        integer token_count
        vector embedding "VECTOR(1536) pgvector"
    }

    ASK_REQUESTS {
        bigserial id PK
        bigint workspace_id FK
        bigint user_id FK
        text question
        text answer "Nullable until answered"
        varchar status "CHECK: pending, answered, unsupported, failed"
        varchar failure_code
        varchar provider "mock or real provider"
        varchar model
        integer prompt_tokens
        integer completion_tokens
        integer latency_ms
        varchar idempotency_key UK "Unique per user"
        timestamptz created_at
    }

    REQUEST_SOURCES {
        bigserial id PK
        bigint request_id FK "ON DELETE CASCADE"
        bigint chunk_id FK "ON DELETE SET NULL"
        varchar document_name "Snapshot copy for audit"
        integer page_number
        real similarity_score
        smallint rank
    }

    USAGE_RECORDS {
        bigserial id PK
        bigint user_id FK
        bigint workspace_id FK
        bigint request_id FK "UNIQUE 1-to-1 guard"
        varchar kind "CHECK: question, embedding"
        integer tokens_used
        numeric estimated_cost
        date period_day "UTC date for daily quota"
        timestamptz created_at
    }
```

---

## 3. Critical Integrity Constraints & Index Architecture

### 3.1 File Ownership & Tenant Isolation
* **`uploaded_by` (FK to `users.id`):** Preserves immutable file ownership. Even in a shared workspace, only the user who uploaded the document or a workspace `admin`/`owner` can delete it.
* **Denormalized `workspace_id` on `document_chunks`:** Eliminates expensive table joins during vector search. The search index query directly applies:
  `WHERE workspace_id = :ws`.

### 3.2 Duplicate Prevention & Idempotency Constraints
* **`UniqueConstraint(workspace_id, content_hash)` on `documents`:** Prevents users from uploading the exact same document twice into the same workspace, saving database disk space and redundant embedding costs.
* **`UniqueConstraint(user_id, idempotency_key)` on `ask_requests`:** Enforces API-level idempotency so network retries never double charge daily question quotas.
* **`UniqueConstraint(request_id)` on `usage_records`:** Guarantees a strictly 1-to-1 relationship between an answered question and its billing charge.

### 3.3 High-Performance Indexing Strategy
1. **`HNSW` Vector Index:** `CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);` — Provides logarithmic sub-linear vector nearest-neighbor search.
2. **Compound Index `documents(workspace_id, status)`:** Accelerates document list and processing queue queries.
3. **Compound Index `ask_requests(user_id, created_at DESC)`:** Provides instant loading of the user's history log.
4. **Compound Index `usage_records(user_id, period_day)`:** Ensures sub-millisecond daily quota verification.

---

## 4. How to Export to `03 - database-design.pdf` for Submission

1. Open [Lucidchart](https://www.lucidchart.com) and select the **Entity Relationship Diagram (ERD)** shape library.
2. Recreate the 9 tables showing field names, data types, and PK/FK markers.
3. Draw connecting relationship lines with exact crow's foot cardinality (`1:N`, `1:1`).
4. Add a notes panel highlighting **File Ownership** (`uploaded_by`) and **Unique 1-to-1 Usage Billing** (`request_id`).
5. Export as PDF (`03 - database-design.pdf`).
