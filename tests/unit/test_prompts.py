"""Unit tests for agent prompt builders."""

from __future__ import annotations

from vireo_vigia.agent.models import AgentConfig
from vireo_vigia.agent.prompts import build_system_prompt, format_chain_context


class TestBuildSystemPrompt:
    def test_includes_agent_name(self) -> None:
        config = AgentConfig(name="HyperBot")
        prompt = build_system_prompt(config)
        assert "HyperBot" in prompt

    def test_includes_protocol_name(self) -> None:
        config = AgentConfig(protocol_name="Hyperliquid")
        prompt = build_system_prompt(config)
        assert "Hyperliquid" in prompt

    def test_includes_extra_instructions(self) -> None:
        config = AgentConfig(system_instructions="Always cite sources.")
        prompt = build_system_prompt(config)
        assert "Always cite sources." in prompt

    def test_no_extra_instructions_is_clean(self) -> None:
        config = AgentConfig()
        prompt = build_system_prompt(config)
        # Should not have extra blank lines from empty instructions
        assert "\n\n\n" not in prompt

    def test_chain_context_included_when_provided(self) -> None:
        config = AgentConfig()
        prompt = build_system_prompt(config, chain_context="Account value: $50,000")
        assert "Account value: $50,000" in prompt
        assert "Live account state" in prompt

    def test_chain_context_omitted_when_empty(self) -> None:
        config = AgentConfig()
        prompt = build_system_prompt(config, chain_context="")
        assert "Live account state" not in prompt

    def test_rag_context_included_when_provided(self) -> None:
        config = AgentConfig()
        rag = "## Relevant documentation\nFunding rates are..."
        prompt = build_system_prompt(config, rag_context=rag)
        assert "Funding rates are" in prompt

    def test_rag_context_omitted_when_empty(self) -> None:
        config = AgentConfig()
        prompt = build_system_prompt(config, rag_context="")
        assert "Relevant documentation" not in prompt

    def test_whitespace_only_chain_context_omitted(self) -> None:
        config = AgentConfig()
        prompt = build_system_prompt(config, chain_context="   \n  ")
        assert "Live account state" not in prompt

    def test_returns_non_empty_string(self) -> None:
        assert len(build_system_prompt(AgentConfig())) > 50


class TestFormatChainContext:
    def test_includes_account_value(self) -> None:
        result = format_chain_context({"account_value": "48000"}, [])
        assert "48000" in result

    def test_no_positions_shows_placeholder(self) -> None:
        result = format_chain_context({"account_value": "0"}, [])
        assert "No open positions" in result

    def test_positions_listed(self) -> None:
        positions = [
            {"coin": "BTC", "szi": "0.5", "unrealizedPnl": "200"},
            {"coin": "ETH", "szi": "-1.0", "unrealizedPnl": "-50"},
        ]
        result = format_chain_context({"account_value": "10000"}, positions)
        assert "BTC" in result
        assert "ETH" in result
        assert "0.5" in result

    def test_liq_price_shown_when_present(self) -> None:
        positions = [
            {
                "coin": "SOL",
                "szi": "10",
                "unrealizedPnl": "100",
                "liquidationPx": "120.5",
            }
        ]
        result = format_chain_context({}, positions)
        assert "120.5" in result

    def test_accepts_alternative_key_names(self) -> None:
        result = format_chain_context({"accountValue": "9999"}, [])
        assert "9999" in result


_AAVE_BALANCE = {
    "total_collateral_usd": 137891.84,
    "total_debt_usd": 91041.08,
    "available_borrow_usd": 12377.80,
    "current_ltv": 0.75,
    "liquidation_threshold": 0.78,
    "health_factor": 1.18,
}
_AAVE_POSITIONS = [
    {
        "asset_symbol": "USDC",
        "position_type": "supply",
        "balance_usd": 137891.84,
        "apy": 0.024,
        "is_collateral": True,
    },
    {
        "asset_symbol": "WBTC",
        "position_type": "borrow",
        "balance_usd": 91041.08,
        "apy": 0.0098,
        "is_collateral": False,
    },
]


class TestFormatChainContextLending:
    """Aave-style (lending) on-chain context formatting."""

    def test_detects_lending_schema(self) -> None:
        result = format_chain_context(_AAVE_BALANCE, _AAVE_POSITIONS)
        # Should NOT fall back to the perp "Account value" formatting.
        assert "Account value" not in result
        assert "Total collateral" in result
        assert "Total debt" in result

    def test_includes_usd_amounts_and_health_factor(self) -> None:
        result = format_chain_context(_AAVE_BALANCE, _AAVE_POSITIONS)
        assert "$137,891.84" in result
        assert "$91,041.08" in result
        assert "1.18" in result
        assert "LTV: 75%" in result
        assert "78%" in result

    def test_low_health_factor_warns(self) -> None:
        result = format_chain_context({**_AAVE_BALANCE, "health_factor": 1.18}, [])
        assert "elevated liquidation risk" in result

    def test_critical_health_factor(self) -> None:
        result = format_chain_context({**_AAVE_BALANCE, "health_factor": 0.95}, [])
        assert "LIQUIDATION IMMINENT" in result

    def test_healthy_health_factor(self) -> None:
        result = format_chain_context({**_AAVE_BALANCE, "health_factor": 2.1}, [])
        assert "healthy" in result

    def test_positions_rendered_with_apy_and_collateral(self) -> None:
        result = format_chain_context(_AAVE_BALANCE, _AAVE_POSITIONS)
        assert "SUPPLY USDC" in result
        assert "BORROW WBTC" in result
        assert "collateral" in result
        assert "APY" in result

    def test_no_positions_placeholder(self) -> None:
        result = format_chain_context(_AAVE_BALANCE, [])
        assert "No open positions" in result

    def test_lending_detected_from_positions_only(self) -> None:
        # Even with an empty balance, position keys flag the lending schema.
        result = format_chain_context({}, [{"asset_symbol": "ARB", "position_type": "supply"}])
        assert "SUPPLY ARB" in result

    def test_non_numeric_amount_falls_back(self) -> None:
        result = format_chain_context({"total_collateral_usd": "N/A", "health_factor": "n/a"}, [])
        assert "$N/A" in result
