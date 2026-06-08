"""
Parameterised system prompt construction.

Prompts are assembled from a fixed persona section plus dynamic
context blocks (RAG chunks, on-chain data) that change per turn.
Only the static section is eligible for Anthropic prompt caching.
"""

from __future__ import annotations

from typing import Any

from vireo_vigia.agent.models import AgentConfig

_BASE_PERSONA_TEMPLATE = """\
You are {name}, the AI support agent for {protocol_name}.

You have two superpowers:
1. You know the {protocol_name} documentation inside-out (retrieved in real time)
2. You can see the user's actual on-chain positions, health factor, and funding costs

Your job: give precise, numbers-first answers. When you have the user's wallet data,
always cite their specific figures (not generic examples). Warn clearly and early
when liquidation risk is elevated.

Be direct. Lead with the most important number. Use markdown for structure.

{extra_instructions}\
"""

_CHAIN_SECTION_TEMPLATE = """\
## Live account state
The following are the connected user's real, live on-chain positions, already
fetched for you this turn. Treat them as the user's own holdings and cite these
exact figures — never ask the user for their wallet address.
{content}
"""

_RAG_SECTION_HEADER = "## Relevant documentation\n"


def build_system_prompt(
    config: AgentConfig,
    *,
    chain_context: str = "",
    rag_context: str = "",
) -> str:
    """
    Build a complete system prompt for one agent turn.

    The returned string is passed as the ``system`` argument to
    ``LLMProvider.chat()``.  When Anthropic prompt caching is enabled,
    only the static persona section incurs write cost on subsequent turns.

    Args:
        config: Agent configuration (name, protocol, instructions).
        chain_context: Pre-formatted on-chain account state string.
                       Empty string omits the section.
        rag_context: Pre-formatted RAG chunk context string.
                     Empty string omits the section.

    Returns:
        A complete system prompt string.
    """
    extra = config.system_instructions.strip()
    extra_block = f"\n{extra}\n" if extra else ""

    persona = _BASE_PERSONA_TEMPLATE.format(
        name=config.name,
        protocol_name=config.protocol_name,
        extra_instructions=extra_block,
    ).rstrip()

    sections: list[str] = [persona]

    if chain_context.strip():
        sections.append(_CHAIN_SECTION_TEMPLATE.format(content=chain_context.strip()))

    if rag_context.strip():
        # RAG context already has its own header from Retriever.format_context
        sections.append(rag_context.strip())

    return "\n\n".join(sections)


def format_chain_context(
    balance: dict[str, Any],
    positions: list[dict[str, Any]],
) -> str:
    """
    Format raw on-chain data dicts into a human-readable markdown block.

    Accepts the output of ``OnchainReader.get_user_balance()`` and
    ``OnchainReader.get_user_positions()`` from any reader. Two schemas are
    supported and auto-detected:

    * **Lending** (Aave V3): ``health_factor`` / ``total_collateral_usd`` and
      positions with ``asset_symbol`` / ``position_type``.
    * **Perp** (Hyperliquid): ``account_value`` and positions with ``coin`` /
      ``szi`` / ``unrealizedPnl``.

    Args:
        balance: Balance summary dict from the reader.
        positions: List of position dicts from the reader.

    Returns:
        Formatted markdown string.
    """
    is_lending = any(
        k in balance
        for k in ("health_factor", "total_collateral_usd", "total_debt_usd")
    ) or any(("asset_symbol" in p or "position_type" in p) for p in positions)

    if is_lending:
        return _format_lending_context(balance, positions)
    return _format_perp_context(balance, positions)


def _money(value: Any) -> str:
    """Format a USD amount, falling back to the raw value if non-numeric."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return f"${value}"


def _format_lending_context(
    balance: dict[str, Any],
    positions: list[dict[str, Any]],
) -> str:
    """Format an Aave-style lending account (collateral, debt, health factor)."""
    lines: list[str] = []

    if "total_collateral_usd" in balance:
        lines.append(f"- Total collateral: **{_money(balance['total_collateral_usd'])}**")
    if "total_debt_usd" in balance:
        lines.append(f"- Total debt: **{_money(balance['total_debt_usd'])}**")
    if "available_borrow_usd" in balance:
        lines.append(f"- Available to borrow: **{_money(balance['available_borrow_usd'])}**")

    hf = balance.get("health_factor")
    if hf is not None:
        try:
            hf_val = float(hf)
            if hf_val < 1.0:
                note = " — ⚠️ LIQUIDATION IMMINENT"
            elif hf_val < 1.5:
                note = " — ⚠️ elevated liquidation risk"
            else:
                note = " — healthy"
            lines.append(f"- Health factor: **{hf_val:.2f}**{note}")
        except (TypeError, ValueError):
            lines.append(f"- Health factor: **{hf}**")

    ltv = balance.get("current_ltv")
    liq_thr = balance.get("liquidation_threshold")
    if ltv is not None and liq_thr is not None:
        try:
            lines.append(
                f"- LTV: {float(ltv) * 100:.0f}% | "
                f"Liquidation threshold: {float(liq_thr) * 100:.0f}%"
            )
        except (TypeError, ValueError):
            pass

    if positions:
        lines.append("\n**Positions:**")
        for p in positions:
            sym = p.get("asset_symbol", p.get("asset", "?"))
            ptype = str(p.get("position_type", "")).upper()
            bal = p.get("balance_usd")
            bal_str = _money(bal) if bal is not None else "?"
            apy = p.get("apy")
            apy_str = ""
            if apy is not None:
                try:
                    apy_str = f" (APY {float(apy) * 100:.2f}%)"
                except (TypeError, ValueError):
                    apy_str = ""
            coll = " — collateral" if p.get("is_collateral") else ""
            lines.append(f"  - {ptype} {sym}: {bal_str}{apy_str}{coll}")
    else:
        lines.append("\n*No open positions.*")

    return "\n".join(lines)


def _format_perp_context(
    balance: dict[str, Any],
    positions: list[dict[str, Any]],
) -> str:
    """Format a Hyperliquid-style perpetuals account (account value, PnL)."""
    lines: list[str] = []

    account_value = balance.get("account_value", balance.get("accountValue", "—"))
    free_margin = balance.get("free_margin", balance.get("freeMargin", "—"))
    lines.append(f"- Account value: **${account_value}**")
    lines.append(f"- Free margin: **${free_margin}**")

    if positions:
        lines.append("\n**Open positions:**")
        for p in positions:
            asset = p.get("coin", p.get("asset", "[unknown asset]"))
            size = p.get("szi", p.get("size", "?"))
            pnl = p.get("unrealizedPnl", p.get("unrealized_pnl", "?"))
            liq = p.get("liquidationPx", p.get("liquidation_price"))
            liq_str = f" | liq ${liq}" if liq else ""
            lines.append(f"  - {asset}: size {size} | PnL ${pnl}{liq_str}")
    else:
        lines.append("\n*No open positions.*")

    return "\n".join(lines)
