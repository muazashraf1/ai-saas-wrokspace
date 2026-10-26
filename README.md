# AI SaaS Workspace

Multi-tenant document Q&A MVP built with Django REST Framework, Next.js,
PostgreSQL/pgvector, Celery and Redis. The default `mock` AI provider requires no
API key and uses deterministic lexical embeddings so the complete upload-to-answer
journey works offline. Gemini is the optional real provider.

## Fastest run: Docker

Requirements: Docker Desktop with the Linux engine running.

```powershell
docker compose up --build
```

Open `http://localhost:3000`. The backend health endpoint is
`http://localhost:8000/api/v1/health/` and API documentation is at
`http://localhost:8000/api/docs/`.

Demo login created by the startup seed command:

- Email: `demo@example.com`
- Password: `Password123!`

Stop services with `docker compose down`. Add `-v` only when you intentionally
want to delete the local database, Redis data and uploaded files.

## Local run without Docker

### Low-space video demo (no PostgreSQL, Redis, or API key)

The dedicated demo profile uses SQLite, the deterministic mock provider and
synchronous Celery execution:

```powershell
cd backend
..\venv\Scripts\Activate.ps1
python manage.py migrate --run-syncdb --settings=config.settings_demo
python manage.py seed_demo_data --settings=config.settings_demo
python manage.py runserver 8000 --settings=config.settings_demo
```

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`. This profile is for the offline demo and automated
evaluation only; production continues to use PostgreSQL/pgvector and Redis.

### Production-like local services

Start PostgreSQL with the pgvector extension and Redis first. Then:

```powershell
Copy-Item .env.example .env
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 8000
```

In a second terminal from `backend`:

```powershell
..\venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo
```

In a third terminal:

```powershell
cd frontend
npm ci
npm run dev
```

For a quick local demo without Redis, set `CELERY_TASK_ALWAYS_EAGER=True`; the
web process will ingest documents synchronously.

## Tests

Fast offline suite using SQLite and an in-process cosine-search fallback:

```powershell
cd backend
$env:DB_ENGINE='sqlite'
$env:STORAGE_DIR='storage/test-uploads'
pytest -q
```

Production-parity PostgreSQL suite:

```powershell
docker compose up -d db redis
cd backend
$env:POSTGRES_HOST='localhost'
$env:POSTGRES_DB='ai_saas_db'
$env:POSTGRES_USER='postgres'
$env:POSTGRES_PASSWORD='postgres'
pytest -q
```

Frontend verification:

```powershell
cd frontend
npm ci
npm run lint
npm run build
```

## Required manual acceptance journey

1. Log in and create/open a workspace.
2. Upload a text PDF or TXT containing: `Employees receive 10 paid sick leaves per calendar year.`
3. Wait until its status becomes `Ready`.
4. Ask: `How many sick leaves do employees get per year?`
5. Confirm the answer contains `[1]`, opens its source, and appears in History.
6. Ask `Who won the football world cup?` and confirm the unsupported response.
7. Confirm Usage increases and duplicate requests with one idempotency key do not double-count.
8. Use a second user/workspace and confirm cross-workspace documents return 403/404.

## Provider modes

- `AI_PROVIDER=mock`: offline, deterministic, zero external cost.
- `AI_PROVIDER=gemini`: requires `AI_API_KEY`; provider timeouts are retried and
  then returned as a recorded 503 failure. Failures never silently become mock answers.

## Scope and known production gaps

Real billing, email delivery, OCR, S3 storage, HTTPS/Nginx, streaming answers and
self-hosted GPU inference are intentionally out of scope. Local file storage and
the Django development server are for the MVP; use object storage and a production
WSGI/ASGI server for deployment.
