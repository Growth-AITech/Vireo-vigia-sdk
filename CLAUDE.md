# Vireo Vigía SDK — Project Memory

## What this is
**24/7 AI support agent for DeFi protocols.** Deploys an AI agent in Discord or Telegram that
answers protocol questions grounded in your docs (RAG) **and reads each user's real on-chain
positions in real time** (Hyperliquid, Aave V3, GMX on Arbitrum). Unlike a generic chatbot, it
answers about *your* wallet — not textbook examples. Built for the **Arbitrum Buildathon 2026**.

- **Package:** `vireo-vigia` (module `vireo_vigia`), Python 3.12+, MIT.
- **Repo:** `github.com/Growth-AITech/Vireo-vigia-sdk` (standalone — extracted from the `contapp-mono` monorepo, fully self-contained).
- **Business:** services-first ($10–15K setup + $2–3K/mo) → SaaS Q4 2026. See `BUSINESS_MODEL.md`.

## Architecture
```
User (Discord / Telegram / CLI)
        │  "am I at risk of liquidation?"
        ▼
Agent.chat()  — gathers RAG + on-chain context IN PARALLEL, builds system prompt
        ├── RAG    → embed query (local bge-large) → Qdrant top-k → context
        ├── Chain  → HyperliquidReader / AaveV3Reader (live wallet positions)
        └── LLM    → Claude Sonnet 4.5 + prompt caching
        ▼
Personalized answer grounded in docs + the user's real positions
```

## Structure
```
src/vireo_vigia/
├── agent/        # base.py (orchestrator), memory.py, models.py, prompts.py
├── knowledge/    # RAG: embeddings.py (BAAI/bge-large, local/free), vector_store.py (Qdrant),
│                 #      ingest.py (SemanticChunker), retriever.py
├── chains/       # hyperliquid.py, evm.py (Aave V3 Arbitrum), gmx.py (stub)
├── channels/     # discord.py (/ask /positions /health /monitor /help), telegram.py
├── monitoring/   # health_monitor.py (DM alerts before liquidation)
├── intelligence/ # alerts.py / digest.py / whale.py / governance.py
├── llm/          # anthropic.py (+ retry + caching), base.py (LLMProvider protocol)
├── config.py     # Pydantic Settings — ALL env vars prefixed VIREO_
├── exceptions.py # VireoVigiaError → LLMError → RateLimitError, ConfigurationError, ...
├── logging.py    # structlog setup (configure_logging)
└── cli.py        # typer app — entrypoint `vireo-vigia` (version / ingest / chat)

examples/   hyperliquid_demo/ (REPL + ingest_docs.py), arbitrum_aave_demo/, discord_demo/bot.py, telegram_demo/bot.py
tests/      unit/ (211 tests, no external keys) · e2e/ (real Qdrant + HL mainnet) · volume/
docs/       architecture.md, use-cases.md, adr/
```

## Run & test
This repo uses **`uv`** with a project-local `.venv/`.
```bash
uv sync --all-extras                      # install deps into ./.venv
cp .env.example .env                      # fill VIREO_ANTHROPIC_API_KEY (required) + Qdrant + Discord

# ingest docs into Qdrant (REQUIRED before /ask works)
PYTHONUTF8=1 uv run python examples/hyperliquid_demo/ingest_docs.py --collection <your_collection>

PYTHONUTF8=1 uv run python examples/discord_demo/bot.py   # Discord bot
uv run pytest tests/unit/ -q                              # 211 tests, no keys needed
uv run vireo-vigia version                                # CLI entrypoint check

# CLI does ingest + chat too (no demo scripts needed)
uv run vireo-vigia ingest <url|file.md> --collection <your_collection>
uv run vireo-vigia chat 0xYOUR_WALLET --collection <your_collection> --protocol Aave
```
On Windows the venv interpreter is `.venv/Scripts/python.exe` (use it directly if `uv run` is slow).

## Gotchas (learned the hard way)
- **Ingest collection defaults to `vireo_docs` and IGNORES `VIREO_QDRANT_COLLECTION`.** True for both
  `examples/hyperliquid_demo/ingest_docs.py` AND the `vireo-vigia ingest` CLI command. Always pass
  `--collection` to match the collection your bot/agent reads (from `.env`), or `/ask` queries an
  empty collection.
- **Env var prefix is `VIREO_`** (e.g. `VIREO_ANTHROPIC_API_KEY`). Missing the key → fail-fast at
  startup with `ConfigurationError`. The console.anthropic.com API is billed SEPARATELY from a
  Claude.ai (Max) subscription — needs its own prepaid credits.
- **First run downloads ~1.3 GB** embedding model (BAAI/bge-large-en-v1.5) — cached after.
- **Piping bot stdout through grep hides output** (block buffering). Run with `PYTHONUNBUFFERED=1`
  and no pipe to see startup/ready logs.
- **`.env` / `.venv` are gitignored** — never commit secrets.

## Env vars (all prefixed `VIREO_`)
| Var | Required | Notes |
|---|---|---|
| `VIREO_ANTHROPIC_API_KEY` | ✅ | console.anthropic.com (prepaid credits) |
| `VIREO_QDRANT_URL` / `VIREO_QDRANT_API_KEY` | ✅ | cloud.qdrant.io free tier or local :6333 |
| `VIREO_QDRANT_COLLECTION` | — | default `vireo_docs` (see ingest gotcha) |
| `VIREO_DISCORD_BOT_TOKEN` / `VIREO_DISCORD_GUILD_ID` | channel | guild_id → instant slash-command sync |
| `VIREO_TELEGRAM_BOT_TOKEN` | channel | @BotFather |
| `VIREO_HL_WALLET_ADDRESS` / `VIREO_EVM_WALLET_ADDRESS` | — | default demo wallet; can pass per command |
| `VIREO_LLM_MODEL` | — | default `claude-sonnet-4-5` |

## Stack
Claude Sonnet 4.5 · BAAI/bge-large (local embeddings, free) · Qdrant Cloud · httpx + web3.py ·
discord.py 2.7 · tenacity (retry) · pydantic-settings · structlog · pytest · ruff + mypy strict.

## Adding a new chain (~2–4h)
1. `src/vireo_vigia/chains/<name>.py` implementing the `OnchainReader` protocol.
2. Wire it in `agent/base.py` → `_get_chain_context()`.
3. Format its section in `agent/prompts.py` → `build_chain_section()`.
