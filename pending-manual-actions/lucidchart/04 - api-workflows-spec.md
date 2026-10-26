# 04 — API Workflows & Sequence Diagrams Specification

> **Project:** AI SaaS Workspace  
> **Prepared for:** FalconXoft Weekend 2 Internship Evaluation  
> **Mandatory Rule per PDF:** *"Lucidchart sequence/API flows covering success and failure; include api-spec.md or openapi.yaml. Document routes, methods, auth, request/response examples, validation, errors and idempotency/retry behavior where relevant."*

---

## 1. Lucidchart URL & OpenAPI Specification

* **Editable Lucidchart URL:** **USER ACTION REQUIRED** — import/redraw `04 - api-workflows.mmd`, share it from the submitter account, then paste the authentic edit URL.
* **Exported PDF Deliverable:** `04 - api-workflows.pdf`
* **Complete OpenAPI 3.0 Specification:** [openapi.yaml](file:///d:/Muaz/Programming/FX%20internship/Weekend%20Assessments/Week%20Two/AI%20SaaS%20Workspace/deliverables/01_AI_SaaS/openapi.yaml) *(Included in this directory)*

---

## 2. Sequence Diagram 1: Success Journey (Upload ➔ Ingestion ➔ Q&A with Citations)

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Browser
    participant FE as Next.js Frontend
    participant API as Django REST API
    participant Worker as Celery Worker
    participant DB as PostgreSQL + pgvector
    participant AI as AI Provider (Mock / Real)

    %% Document Upload Phase
    Note over User, DB: Phase 1: Document Upload & Asynchronous Ingestion
    User->>FE: Select "leave-policy.pdf" (Drag & Drop)
    FE->>FE: Client-side check (ext: .pdf, size <= 10MB)
    FE->>API: POST /api/v1/workspaces/1/documents/ (multipart/form-data)
    Note over API: Auth & Workspace Check<br/>Magic Bytes Check (%PDF-)<br/>SHA-256 Hash Duplicate Check
    API->>DB: INSERT INTO documents (status="uploaded", content_hash, ...)
    API-->>FE: HTTP 202 Accepted {"id": 15, "status": "uploaded"}
    API-)Worker: Enqueue process_document_task(doc_id=15)
    
    Worker->>Worker: Extract text page-by-page
    Worker->>Worker: Chunk text (400-token target, 50-token overlap)
    Worker->>AI: Batch embed chunks
    AI-->>Worker: Return 1536-dim vector embeddings
    Worker->>DB: INSERT INTO document_chunks (vectors, page_numbers)
    Worker->>DB: UPDATE documents SET status="ready"

    %% Grounded Q&A Phase
    Note over User, AI: Phase 2: Grounded Q&A with Citations
    User->>FE: Ask: "How many sick leaves do employees get?"
    FE->>FE: Generate unique Idempotency-Key: UUIDv4
    FE->>API: POST /api/v1/workspaces/1/ask/<br/>Headers: Idempotency-Key: 9d1a-7c34...
    
    Note over API: 1. Check & Deduct Daily Quota (questions_today < 20)<br/>2. Embed query prompt
    API->>AI: Embed question
    AI-->>API: Return query_vector
    
    API->>DB: SELECT chunks WHERE workspace_id = 1<br/>ORDER BY embedding <=> query_vector LIMIT 4
    DB-->>API: Top 4 chunks (Best similarity score = 0.84)
    Note over API: Check uses active threshold: 0.55 real provider / 0.30 mock demo
    
    API->>AI: Call LLM with Bounded Context & System Rules
    AI-->>API: "Employees get 10 sick leaves per year [1]."
    
    Note over API: Post-Process & Validate [1] against retrieved chunks
    API->>DB: BEGIN TRANSACTION<br/>INSERT INTO ask_requests<br/>INSERT INTO request_sources (snapshot citations)<br/>INSERT INTO usage_records (unique request_id)<br/>COMMIT
    
    API-->>FE: HTTP 200 OK {"status": "answered", "answer": "...", "sources": [{...}]}
    FE->>User: Render answer with glowing [1] pill & update usage meter
```

---

## 3. Sequence Diagram 2: Failure & Exception Workflows

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Browser
    participant FE as Next.js Frontend
    participant API as Django REST API
    participant DB as PostgreSQL + pgvector
    participant AI as External AI Provider

    %% Scenario A: Unsupported Question (Threshold Miss)
    Note over User, AI: Failure Scenario A: Unrelated Question (Zero AI Cost)
    User->>FE: Ask: "Who won the 2022 World Cup?"
    FE->>API: POST /api/v1/workspaces/1/ask/
    API->>DB: Cosine Vector Search WHERE workspace_id = 1
    DB-->>API: Top chunk score below active threshold (0.55 real / 0.30 mock)
    Note over API: Threshold Miss: ABORT AI CALL IMMEDIATELY
    API->>DB: INSERT INTO ask_requests (status="unsupported")<br/>(ZERO usage_records inserted)
    API-->>FE: HTTP 200 OK {"status": "unsupported", "answer": "I could not find this in your documents.", "sources": []}
    FE->>User: Display violet "Unsupported Question (Zero Cost)" card

    %% Scenario B: AI Provider Timeout & Retry
    Note over User, AI: Failure Scenario B: Provider Timeout & Idempotent Retry
    User->>FE: Ask: "Explain vacation carryover policy"
    FE->>API: POST /api/v1/workspaces/1/ask/ (Idempotency-Key: X)
    API->>AI: Call LLM API (Timeout=20s)
    AI--xAPI: Connection Timeout (No response)
    Note over API: Exponential Backoff Retry (Attempt 2)
    API->>AI: Retry LLM API Call
    AI--xAPI: Connection Timeout (Failure)
    API->>DB: INSERT INTO ask_requests (status="failed", failure_code="provider_timeout")
    API-->>FE: HTTP 503 Service Unavailable {"detail": "The AI service is unavailable. Please retry."}
    FE->>User: Show Alert with "Retry" button
    
    User->>FE: Click "Retry"
    FE->>API: Re-send POST /ask/ with SAME Idempotency-Key: X
    Note over API: Idempotency safety: Returns cached state or re-attempts safely without double billing
```

---

## 4. Key Request / Response Payloads

### 4.1 Grounded Q&A Success (HTTP 200)
```json
// POST /api/v1/workspaces/1/ask/
// Headers: Authorization: Bearer <token>, Idempotency-Key: 9d1a7c34-2b6e-4f0a-8c11-5e2f7a6b9c10
{
  "question": "How many sick leaves do employees get per year?"
}

// Response (HTTP 200 OK)
{
  "request_id": 120,
  "status": "answered",
  "answer": "Employees get 10 sick leaves per year [1].",
  "sources": [
    {
      "n": 1,
      "document": "leave-policy.pdf",
      "page": 3,
      "score": 0.842,
      "snippet": "Each employee is entitled to 10 days of paid sick leave per calendar year."
    }
  ],
  "usage": {
    "questions_today": 1,
    "daily_limit": 20
  },
  "latency_ms": 210
}
```

### 4.2 Unsupported Question (HTTP 200, status="unsupported")
```json
{
  "request_id": 121,
  "status": "unsupported",
  "answer": "I could not find this in your documents.",
  "sources": []
}
```

### 4.3 Daily Quota Limit Exceeded (HTTP 429)
```json
{
  "detail": "Daily question limit reached.",
  "resets_at": "2026-10-27T00:00:00Z"
}
```

---

## 5. How to Export to `04 - api-workflows.pdf` for Submission

1. In Lucidchart, use the **UML Sequence** shape library.
2. Recreate the lifelines (`User`, `Next.js Frontend`, `Django API`, `Celery Worker`, `PostgreSQL`, `AI Provider`).
3. Add the arrows with sequence numbers and notes.
4. Export as PDF (`04 - api-workflows.pdf`).
