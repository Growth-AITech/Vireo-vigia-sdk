#!/usr/bin/env python3
"""
Vireo Vigía — Telegram Bot demo.

Prerequisites:
  1. uv add 'python-telegram-bot>=20.7'
  2. Set in .env:
       VIREO_ANTHROPIC_API_KEY=...
       VIREO_OPENAI_API_KEY=...
       VIREO_TELEGRAM_BOT_TOKEN=...
       VIREO_HL_WALLET_ADDRESS=...  (or use /setwallet in chat)

Usage:
  uv run python examples/telegram_demo/bot.py
"""

from __future__ import annotations

import asyncio


async def main() -> None:
    from vireo_vigia.agent.base import Agent
    from vireo_vigia.agent.models import AgentConfig
    from vireo_vigia.chains.hyperliquid import HyperliquidReader
    from vireo_vigia.channels.telegram import create_adapter_from_settings
    from vireo_vigia.config import load_settings
    from vireo_vigia.knowledge.retriever import Retriever
    from vireo_vigia.knowledge.vector_store import QdrantVectorStore
    from vireo_vigia.llm.anthropic import AnthropicLLM
    from vireo_vigia.logging import configure_logging

    settings = load_settings()
    configure_logging(level=settings.log_level, environment=settings.environment)

    llm = AnthropicLLM(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model=settings.llm_model,
    )
    from vireo_vigia.knowledge.embeddings import create_from_settings as create_embeddings

    embeddings = create_embeddings(settings)
    vector_store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None,
        collection=settings.qdrant_collection,
        vector_dim=settings.embedding_dimensions,
    )
    retriever = Retriever(embeddings=embeddings, vector_store=vector_store)
    chain_reader = HyperliquidReader(network=settings.hl_network)

    config = AgentConfig(
        name="VireoBot",
        protocol_name="Hyperliquid",
        system_instructions=(
            "You are a precise DeFi assistant. "
            "Keep answers concise for Telegram. "
            "Use plain text or minimal Markdown."
        ),
    )

    agent = Agent(
        llm=llm,
        retriever=retriever,
        chain_reader=chain_reader,
        config=config,
    )

    async with chain_reader:
        adapter = create_adapter_from_settings(settings, agent)
        await adapter.start()


if __name__ == "__main__":
    asyncio.run(main())
