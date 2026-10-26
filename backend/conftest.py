import os

import pytest


@pytest.fixture(scope='session')
def django_db_use_migrations():
    """SQLite is a fast fallback; PostgreSQL runs the real migrations."""
    return os.getenv('DB_ENGINE', 'postgresql').lower() != 'sqlite'


@pytest.fixture(autouse=True)
def use_deterministic_mock_provider(settings):
    """Tests must not depend on a developer's real provider credentials or network."""
    settings.AI_PROVIDER = 'mock'
    settings.MOCK_SIMILARITY_THRESHOLD = 0.30
