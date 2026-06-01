"""E2E test configuration — loads real settings from .env, bypassing test overrides."""

from __future__ import annotations

import pytest


@pytest.fixture()
def settings(monkeypatch: pytest.MonkeyPatch):
    """
    Load real VireoSettings from .env for E2E tests.

    The global conftest autouse fixture overrides several env vars for unit
    tests (e.g. VIREO_QDRANT_URL=http://localhost:6333). We undo those here
    so E2E tests connect to the real services defined in .env.
    """
    # Remove unit-test overrides so pydantic-settings reads from .env
    for key in [
        "VIREO_QDRANT_URL",
        "VIREO_QDRANT_API_KEY",
        "VIREO_ANTHROPIC_API_KEY",
        "VIREO_OPENAI_API_KEY",
        "VIREO_ENVIRONMENT",
        "VIREO_LOG_LEVEL",
        "VIREO_EMBEDDING_PROVIDER",
    ]:
        monkeypatch.delenv(key, raising=False)

    from vireo_vigia.config import load_settings
    from vireo_vigia.logging import configure_logging

    s = load_settings()
    configure_logging(level="WARNING", environment=s.environment)
    return s
