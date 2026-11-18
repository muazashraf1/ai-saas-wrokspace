"""Low-space local demo settings.

This profile is intentionally separate from production. It uses SQLite, executes
Celery tasks eagerly in the Django process, and forces the deterministic mock AI
provider so a complete video demo needs no Docker, Redis, PostgreSQL, or API key.
"""

from .settings import *  # noqa: F403,F401


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_demo.sqlite3',  # noqa: F405
    }
}

# The production document migration contains a PostgreSQL HNSW index. For this
# disposable demo database Django creates the custom app tables directly from
# the current models while still applying Django's built-in migrations.
MIGRATION_MODULES = {
    'users': None,
    'workspaces': None,
    'documents': None,
    'qa': None,
    'usage': None,
    'ai': None,
}

AI_PROVIDER = 'mock'
AI_API_KEY = ''
# The offline lexical mock scores a short question against an entire document
# chunk.  A 0.30 semantic-embedding threshold is too strict for that purpose:
# valid, specific questions about a 300-500-token PDF chunk can score around
# 0.13.  0.08 still rejects unrelated questions (which have no shared terms)
# while making the no-cost walkthrough reliable.
MOCK_SIMILARITY_THRESHOLD = 0.08
TOP_K_CHUNKS = 4

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

STORAGE_DIR = BASE_DIR / 'storage' / 'demo-uploads'  # noqa: F405
