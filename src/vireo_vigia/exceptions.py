"""
Typed exception hierarchy for the Vireo Vigía SDK.

All SDK exceptions inherit from ``VireoVigiaError`` so callers can catch
the entire family with a single ``except VireoVigiaError`` clause.

Error codes follow the pattern ``CATEGORY_SPECIFIC_ISSUE`` and are
intended to be stable across versions for programmatic handling.
"""

from __future__ import annotations


class VireoVigiaError(Exception):
    """
    Base exception for all Vireo Vigía SDK errors.

    Attributes:
        message: Human-readable description.
        code: Stable machine-readable identifier (e.g. ``LLM_RATE_LIMIT``).
    """

    def __init__(self, message: str, *, code: str = "VIREO_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message={self.message!r}, code={self.code!r})"


# ── Configuration ─────────────────────────────────────────────────────────────


class ConfigurationError(VireoVigiaError):
    """
    Raised when required configuration is missing or invalid.

    Typically thrown at startup via ``load_settings()`` before any
    network calls are made.
    """

    def __init__(self, message: str, *, code: str = "CONFIG_ERROR") -> None:
        super().__init__(message, code=code)


# ── LLM ───────────────────────────────────────────────────────────────────────


class LLMError(VireoVigiaError):
    """Base for all LLM provider errors."""

    def __init__(self, message: str, *, code: str = "LLM_ERROR") -> None:
        super().__init__(message, code=code)


class RateLimitError(LLMError):
    """
    Raised when the LLM provider returns a 429 rate-limit response.

    Callers should back off and retry using the ``retry_after``
    hint if provided.

    Attributes:
        retry_after: Suggested seconds to wait before retrying (may be None).
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        code: str = "LLM_RATE_LIMIT",
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, code=code)


class ContextLengthError(LLMError):
    """Raised when the request exceeds the model's context window."""

    def __init__(self, message: str, *, code: str = "LLM_CONTEXT_LENGTH") -> None:
        super().__init__(message, code=code)


# ── Knowledge Base ────────────────────────────────────────────────────────────


class KnowledgeBaseError(VireoVigiaError):
    """Base for all RAG / vector store errors."""

    def __init__(self, message: str, *, code: str = "KB_ERROR") -> None:
        super().__init__(message, code=code)


class EmbeddingError(KnowledgeBaseError):
    """Raised when an embedding API call fails."""

    def __init__(self, message: str, *, code: str = "KB_EMBEDDING_FAILED") -> None:
        super().__init__(message, code=code)


class VectorStoreError(KnowledgeBaseError):
    """Raised when a Qdrant operation fails (connection, upsert, search)."""

    def __init__(self, message: str, *, code: str = "KB_VECTOR_STORE") -> None:
        super().__init__(message, code=code)


class IngestError(KnowledgeBaseError):
    """Raised when document ingestion fails (fetch, parse, or chunking)."""

    def __init__(self, message: str, *, code: str = "KB_INGEST_FAILED") -> None:
        super().__init__(message, code=code)


# ── Chain ─────────────────────────────────────────────────────────────────────


class ChainError(VireoVigiaError):
    """Base for all on-chain reader errors."""

    def __init__(self, message: str, *, code: str = "CHAIN_ERROR") -> None:
        super().__init__(message, code=code)


class ChainConnectionError(ChainError):
    """Raised when the chain RPC endpoint cannot be reached."""

    def __init__(self, message: str, *, code: str = "CHAIN_CONNECTION") -> None:
        super().__init__(message, code=code)


class ChainDataError(ChainError):
    """Raised when on-chain data is malformed or unexpected."""

    def __init__(self, message: str, *, code: str = "CHAIN_DATA") -> None:
        super().__init__(message, code=code)


# ── Auth ──────────────────────────────────────────────────────────────────────


class AuthenticationError(VireoVigiaError):
    """Raised when an API key or credential is rejected by an external service."""

    def __init__(self, message: str, *, code: str = "AUTH_FAILED") -> None:
        super().__init__(message, code=code)
