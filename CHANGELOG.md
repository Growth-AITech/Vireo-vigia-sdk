# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 1: project bootstrap, DevOps toolchain, core config/logging/exceptions modules
- Phase 2: AnthropicLLM (retry, caching, streaming), OpenAIEmbeddings, QdrantVectorStore, SemanticChunker, IngestPipeline, Retriever — 79 unit tests
- Phase 3: Agent class (RAG + chain + LLM orchestration, graceful degradation, streaming), InMemoryConversationMemory, AgentConfig/AgentResponse, build_system_prompt — 43 unit tests
- Phase 4: HyperliquidReader (httpx + tenacity retry, all 5 OnchainReader methods, Pydantic models) — 22 unit tests + 8 integration tests
- Phase 5: working terminal demo (ingest_docs.py + streaming chat REPL), ADR-0002 (agent orchestration decisions), updated README with demo walkthrough and coverage

## [0.1.1] - 2026-06-08

### Fixed
- **Aave V3 on-chain reads now work end to end.** `get_user_positions` and
  `get_market_info` reverted because the `UiPoolDataProvider.getReservesData`
  ABI had drifted from the deployed Arbitrum contract — positions silently came
  back empty. Rewrote both on top of the `AaveProtocolDataProvider` (stable ABI,
  balances already in real token units).
- `_ray_to_apy` overflowed by treating the RAY annual rate as a per-second rate;
  it now compounds the APR correctly.
- `format_chain_context` only understood the Hyperliquid schema, so Aave
  balances rendered as `$—` and the agent replied "share your wallet address".
  Added a lending-schema branch so the agent cites the user's real Aave figures
  (collateral, debt, health factor, per-asset APY).

### Added
- Package metadata: `authors` and `[project.urls]` so the PyPI page links to the
  repository.
- Unit tests for the Aave lending formatter and `get_market_info` (224 unit tests).

### Changed
- CI: the pull-request gate runs the deterministic unit suite; the e2e and
  integration suites are opt-in (`pytest -m e2e` / `-m integration`).
- Bumped `aiohttp` to 3.14.1 to clear transitive security advisories.

## [0.1.0] - 2026-05-12

### Added
- Initial project scaffold
- `pyproject.toml` with full dependency set and tool configuration (ruff, mypy, pytest, bandit)
- `.pre-commit-config.yaml` with ruff, mypy, bandit, pip-audit hooks
- GitHub Actions CI workflow (lint + types + tests + security)
- Docker Compose for local Qdrant instance
- Railway deployment config
- `config.py`: Pydantic Settings with fail-fast validation
- `logging.py`: structlog with JSON (prod) / console (dev) renderers
- `exceptions.py`: typed error hierarchy (`VireoVigiaError`, `ConfigurationError`, `LLMError`, etc.)
- Architecture documentation with Mermaid diagram
- ADR-0001: tech stack decision record
