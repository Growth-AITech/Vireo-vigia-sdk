"""Shared pytest fixtures for the Vireo Vigía SDK test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Inject minimal required environment variables for all tests.

    This prevents real API calls and satisfies ``VireoSettings`` validation.
    """
    monkeypatch.setenv("VIREO_ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("VIREO_OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("VIREO_EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("VIREO_ENVIRONMENT", "development")
    monkeypatch.setenv("VIREO_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("VIREO_QDRANT_URL", "http://localhost:6333")
