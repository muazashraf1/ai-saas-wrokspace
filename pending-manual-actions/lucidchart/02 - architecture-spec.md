# 02 — System Architecture Specification & Diagram Guide

> **Project:** AI SaaS Workspace  
> **Prepared for:** FalconXoft Weekend 2 Internship Evaluation  
> **Mandatory Rule per PDF:** *"Lucidchart system architecture showing frontend, API, authentication, database, object storage where relevant, background jobs, external services, security boundaries and deployment location. Explain component responsibilities and design trade-offs. Plus editable Lucidchart URL."*

---

## 1. Lucidchart Diagram URL

* **Editable Lucidchart URL:** **USER ACTION REQUIRED** — import/redraw `02 - architecture.mmd`, share it from the submitter account, then paste the authentic edit URL.
* **Exported File:** `02 - architecture.pdf`

---

## 2. System Architecture Diagram (Mermaid & Visual Blueprint)

```mermaid
flowchart TB
    subgraph PUBLIC_ZONE["Public Zone (Internet)"]
        CLIENT["Web Browser / Client Device"]
    end

    subgraph INGRESS_ZONE["Edge & Ingress (Port 80 / 443)"]
        NGINX["Nginx / Reverse Proxy & SSL (Proposed)"]
        NEXTJS["Next.js 16 Frontend (Port 3000)\n- App Router (React JSX)\n- Bearer Token Injector\n- Citation Highlighting Engine"]
    end

    subgraph PRIVATE_ZONE["Private Application Zone (Internal VPC)"]
        subgraph DJANGO_CORE["Django 5 + DRF Core API (Port 8000)"]
            AUTH["JWT Auth & RBAC Guard\n(Owner / Admin / Member)"]
            UPLOAD_SVC["Document Ingestion Service\n- Magic Bytes Check (%PDF-)\n- SHA-256 Duplicate Check"]
            RAG_ENGINE["RAG & Retrieval Engine\n- Cosine Similarity <=> Query\n- Threshold: 0.55 real / 0.30 mock\n- Prompt Injection Delimiter Guard"]
            QUOTA_MGR["Usage & Quotas Manager\n- Atomic Transaction Decrement\n- Idempotency-Key Handler"]
        end

        subgraph DATA_TIER["Persistence & Storage Tier"]
            POSTGRES[("PostgreSQL 15/16 + pgvector (Port 5432)\n- 8 Relational Tables\n- HNSW Vector Cosine Index\n- WHERE workspace_id = :ws")]
            STORAGE[("Local File Storage / S3 (backend/storage/)\n- Randomized UUID storage keys\n- No direct public HTTP access")]
        end

        subgraph ASYNC_TIER["Asynchronous Processing Tier"]
            REDIS[("Redis Broker / Memurai (Port 6379)\n- Task queue\n- Rate limiting counters")]
            CELERY["Celery Ingestion Worker\n- Page-by-page text extract\n- 400 target / 50 overlap\n- Vector embedding batcher"]
        end
    end

    subgraph EXTERNAL_ZONE["External AI Zone (Outbound HTTPS Only)"]
        AI_INTERFACE["Pluggable AI Provider Interface"]
        MOCK_AI["[MOCK] MockAIProvider\n(Deterministic 1536-dim unit vectors\n100% offline, zero-cost)"]
        REAL_AI["[IMPLEMENTED PATH] Gemini API\n(OpenAI is comparison-only)"]
    end

    %% Data Flows
    CLIENT -->|HTTPS JSON / JWT| NEXTJS
    NEXTJS -->|HTTP REST API (Bearer JWT)| DJANGO_CORE
    AUTH --> DJANGO_CORE

    UPLOAD_SVC -->|Save File| STORAGE
    UPLOAD_SVC -->|Push Ingestion Task| REDIS
    REDIS -->|Consume Task| CELERY
    CELERY -->|Extract Text & Chunk| STORAGE
    CELERY -->|Batch Embed Chunks| AI_INTERFACE
    CELERY -->|Save Chunks & Vectors| POSTGRES

    RAG_ENGINE -->|1. Check Quota & Deduct| QUOTA_MGR
    RAG_ENGINE -->|2. Cosine Vector Search| POSTGRES
    RAG_ENGINE -->|3. Bounded Context Prompt| AI_INTERFACE

    AI_INTERFACE -.->|Active Default| MOCK_AI
    AI_INTERFACE -.->|Config Switch| REAL_AI

    DJANGO_CORE -->|Save Request & Citations| POSTGRES
```

---

## 3. Trust & Security Boundaries

### 3.1 Public Zone vs. Private Zone
* **Public Zone:** End-users interact only with the Next.js frontend over standard HTTPS.
* **Private Zone:** Django REST API, PostgreSQL, Redis, Celery workers, and file storage reside in an isolated private network. No database or Redis port is exposed publicly.

### 3.2 Tenant Isolation Boundary
* **Every SQL & Vector Query:** The `workspace_id` is extracted strictly from the authenticated JWT session membership, **never** accepted blindly from client query strings.
* **Vector Filter:** The pgvector similarity query strictly enforces `WHERE workspace_id = :current_ws`, ensuring zero possibility of cross-tenant vector leakage.

### 3.3 Outbound AI Boundary
* Calls to external AI providers are **strictly outbound-only** over HTTPS TLS 1.3.
* API keys are stored solely in server-side environment variables and are never transmitted to or accessible by the browser client.

---

## 4. How to Export to `02 - architecture.pdf` for Submission

1. Open [Lucidchart](https://www.lucidchart.com) and create a new blank document.
2. Draw the 4 boundary zones (Public, Ingress, Private Zone, External AI Zone) as distinct bordered containers.
3. Add the components and label each connecting arrow (e.g., `HTTPS JSON`, `SQL <=> Cosine`, `Celery Task Queue`).
4. Mark the `MockAIProvider` box with a **dashed border** and label it **MOCK (Zero-Cost Offline)**.
5. Click **File ➔ Export ➔ PDF** and save as `02 - architecture.pdf` in your submission folder.
6. Copy the shareable edit link and paste it into `07 - source-and-demo-links.md` and `10 - submission-index.md`.
