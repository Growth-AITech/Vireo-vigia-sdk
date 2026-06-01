"""Unit tests for the exception hierarchy."""

from __future__ import annotations

import pytest

from vireo_vigia.exceptions import (
    AuthenticationError,
    ChainConnectionError,
    ChainDataError,
    ChainError,
    ConfigurationError,
    ContextLengthError,
    EmbeddingError,
    IngestError,
    KnowledgeBaseError,
    LLMError,
    VireoVigiaError,
    RateLimitError,
    VectorStoreError,
)


class TestVireoVigiaError:
    def test_default_code(self) -> None:
        err = VireoVigiaError("something failed")
        assert err.code == "VIREO_ERROR"
        assert err.message == "something failed"

    def test_custom_code(self) -> None:
        err = VireoVigiaError("oops", code="CUSTOM_CODE")
        assert err.code == "CUSTOM_CODE"

    def test_str_includes_code(self) -> None:
        err = VireoVigiaError("boom", code="TEST_CODE")
        assert "[TEST_CODE]" in str(err)
        assert "boom" in str(err)

    def test_repr(self) -> None:
        err = VireoVigiaError("boom", code="X")
        assert "VireoVigiaError" in repr(err)

    def test_is_exception(self) -> None:
        with pytest.raises(VireoVigiaError):
            raise VireoVigiaError("test")


class TestInheritanceHierarchy:
    def test_config_is_vireo(self) -> None:
        assert issubclass(ConfigurationError, VireoVigiaError)

    def test_llm_is_vireo(self) -> None:
        assert issubclass(LLMError, VireoVigiaError)

    def test_rate_limit_is_llm(self) -> None:
        assert issubclass(RateLimitError, LLMError)
        assert issubclass(RateLimitError, VireoVigiaError)

    def test_context_length_is_llm(self) -> None:
        assert issubclass(ContextLengthError, LLMError)

    def test_kb_is_vireo(self) -> None:
        assert issubclass(KnowledgeBaseError, VireoVigiaError)

    def test_embedding_is_kb(self) -> None:
        assert issubclass(EmbeddingError, KnowledgeBaseError)

    def test_vector_store_is_kb(self) -> None:
        assert issubclass(VectorStoreError, KnowledgeBaseError)

    def test_ingest_is_kb(self) -> None:
        assert issubclass(IngestError, KnowledgeBaseError)

    def test_chain_is_vireo(self) -> None:
        assert issubclass(ChainError, VireoVigiaError)

    def test_chain_connection_is_chain(self) -> None:
        assert issubclass(ChainConnectionError, ChainError)

    def test_chain_data_is_chain(self) -> None:
        assert issubclass(ChainDataError, ChainError)

    def test_auth_is_vireo(self) -> None:
        assert issubclass(AuthenticationError, VireoVigiaError)

    def test_catch_all_with_base(self) -> None:
        """All subtypes can be caught with base VireoVigiaError."""
        errors = [
            ConfigurationError("cfg"),
            LLMError("llm"),
            RateLimitError("rl"),
            KnowledgeBaseError("kb"),
            ChainError("chain"),
            AuthenticationError("auth"),
        ]
        for err in errors:
            with pytest.raises(VireoVigiaError):
                raise err


class TestRateLimitError:
    def test_retry_after_default_none(self) -> None:
        err = RateLimitError("too many requests")
        assert err.retry_after is None

    def test_retry_after_set(self) -> None:
        err = RateLimitError("slow down", retry_after=30.0)
        assert err.retry_after == 30.0

    def test_default_code(self) -> None:
        assert RateLimitError("x").code == "LLM_RATE_LIMIT"
