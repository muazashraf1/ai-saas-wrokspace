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
MOCK_SIMILARITY_THRESHOLD = 0.30
TOP_K_CHUNKS = 4

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

STORAGE_DIR = BASE_DIR / 'storage' / 'demo-uploads'  # noqa: F405
