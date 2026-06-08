"""Unit tests for AaveV3Reader — mocked, no RPC needed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vireo_vigia.chains.evm import _BASE_CURRENCY_UNIT, _RAY, _WAD, AaveV3Reader, _ray_to_apy
from vireo_vigia.exceptions import ChainConnectionError


def _make_w3(pool_result: tuple, ui_result: tuple | None = None) -> MagicMock:
    """Build a mock web3 instance returning the given call results.

    evm.py now uses ``await contract.functions.xxx().call()`` directly,
    so ``.call`` must be an AsyncMock.
    """
    w3 = MagicMock()
    w3.to_checksum_address = lambda x: x

    pool_contract = MagicMock()
    # .call() is now awaited directly — use AsyncMock
    pool_contract.functions.getUserAccountData.return_value.call = AsyncMock(
        return_value=pool_result
    )

    ui_contract = MagicMock()
    if ui_result is not None:
        ui_contract.functions.getReservesData.return_value.call.return_value = ui_result
        ui_contract.functions.getUserReservesData.return_value.call.return_value = ui_result

    def contract_factory(address: str, abi: list) -> MagicMock:
        from vireo_vigia.chains.evm import _POOL_ABI

        return pool_contract if abi is _POOL_ABI else ui_contract

    w3.eth.contract.side_effect = contract_factory
    return w3


class TestRayToApy:
    def test_zero_rate(self) -> None:
        assert _ray_to_apy(0) == pytest.approx(0.0)

    def test_typical_supply_rate(self) -> None:
        # Aave rates are an annual APR scaled by RAY. 3% APR → ~3.05% APY.
        rate = int(0.03 * _RAY)
        apy = _ray_to_apy(rate)
        assert 0.025 < apy < 0.035

    def test_high_borrow_rate(self) -> None:
        # 20% APR → ~22.1% APY (continuous-ish compounding).
        rate = int(0.20 * _RAY)
        apy = _ray_to_apy(rate)
        assert 0.18 < apy < 0.23


_SAMPLE_POOL_RESULT = (
    int(10_000 * _BASE_CURRENCY_UNIT),  # totalCollateralBase  ($10,000)
    int(5_000 * _BASE_CURRENCY_UNIT),  # totalDebtBase        ($5,000)
    int(2_000 * _BASE_CURRENCY_UNIT),  # availableBorrowsBase ($2,000)
    8000,  # currentLiquidationThreshold (80%)
    7500,  # ltv (75%)
    int(1.8 * _WAD),  # healthFactor (1.8)
)


class TestGetUserBalance:
    async def test_returns_correct_fields(self) -> None:
        reader = AaveV3Reader()
        w3 = _make_w3(_SAMPLE_POOL_RESULT)

        with patch.object(reader, "_get_w3", return_value=w3):
            balance = await reader.get_user_balance("0xabc")

        assert balance["total_collateral_usd"] == pytest.approx(10_000.0)
        assert balance["total_debt_usd"] == pytest.approx(5_000.0)
        assert balance["health_factor"] == pytest.approx(1.8)
        assert balance["current_ltv"] == pytest.approx(0.75)
        assert balance["liquidation_threshold"] == pytest.approx(0.80)

    async def test_rpc_error_raises_chain_connection_error(self) -> None:
        reader = AaveV3Reader()
        w3 = MagicMock()
        w3.to_checksum_address = lambda x: x
        pool = MagicMock()
        # .call() is AsyncMock that raises
        pool.functions.getUserAccountData.return_value.call = AsyncMock(
            side_effect=Exception("timeout")
        )
        w3.eth.contract.return_value = pool

        with patch.object(reader, "_get_w3", return_value=w3):
            with pytest.raises(ChainConnectionError):
                await reader.get_user_balance("0xabc")


class TestGetUserPositions:
    """Positions now come from AaveProtocolDataProvider (real token units)."""

    @staticmethod
    def _reader_with_mocks(reader: AaveV3Reader) -> tuple:
        # USDC supplied as collateral, WBTC borrowed (variable).
        tokens = [("USDC", "0xUSDC"), ("WBTC", "0xWBTC")]
        user_data = {
            # currentATokenBalance, stableDebt, currentVariableDebt, ..., liquidityRate(6), _, collateral(8)
            "0xUSDC": (1000 * 10**6, 0, 0, 0, 0, 0, int(0.024 * _RAY), 0, True),
            "0xWBTC": (0, 0, 50_000_000, 0, 0, 0, int(0.01 * _RAY), 0, False),
        }
        # getReserveData — only index 6 (variableBorrowRate) is read.
        reserve_data = {"0xWBTC": (0, 0, 0, 0, 0, 0, int(0.0098 * _RAY), 0, 0, 0, 0, 0)}
        prices = {
            "0xUSDC": int(1.0 * _BASE_CURRENCY_UNIT),
            "0xWBTC": int(60_000 * _BASE_CURRENCY_UNIT),
        }
        decimals = {"0xusdc": 6, "0xwbtc": 8}

        pdp = MagicMock()
        pdp.functions.getAllReservesTokens.return_value.call = AsyncMock(return_value=tokens)
        pdp.functions.getUserReserveData.side_effect = lambda asset, _user: MagicMock(
            call=AsyncMock(return_value=user_data[asset])
        )
        pdp.functions.getReserveData.side_effect = lambda asset: MagicMock(
            call=AsyncMock(return_value=reserve_data[asset])
        )

        oracle = MagicMock()
        oracle.functions.getAssetPrice.side_effect = lambda asset: MagicMock(
            call=AsyncMock(return_value=prices[asset])
        )
        w3 = MagicMock()
        w3.to_checksum_address = lambda x: x
        w3.eth.contract.return_value = oracle
        return w3, pdp, decimals

    async def test_parses_supply_and_borrow(self) -> None:
        reader = AaveV3Reader()
        w3, pdp, decimals = self._reader_with_mocks(reader)

        with (
            patch.object(reader, "_get_w3", return_value=w3),
            patch.object(reader, "_pdp_contract", AsyncMock(return_value=pdp)),
            patch.object(reader, "_decimals", AsyncMock(side_effect=lambda a: decimals[a.lower()])),
        ):
            positions = await reader.get_user_positions("0xUSER")

        assert len(positions) == 2
        supply = next(p for p in positions if p["position_type"] == "supply")
        borrow = next(p for p in positions if p["position_type"] == "borrow")
        assert supply["asset_symbol"] == "USDC"
        assert supply["balance_usd"] == pytest.approx(1000.0)
        assert supply["is_collateral"] is True
        assert borrow["asset_symbol"] == "WBTC"
        assert borrow["balance_usd"] == pytest.approx(30_000.0)  # 0.5 WBTC @ $60k

    async def test_rpc_failure_degrades_to_empty(self) -> None:
        reader = AaveV3Reader()
        w3 = MagicMock()
        w3.to_checksum_address = lambda x: x

        with (
            patch.object(reader, "_get_w3", return_value=w3),
            patch.object(
                reader,
                "_pdp_contract",
                AsyncMock(side_effect=Exception("rpc down")),
            ),
        ):
            assert await reader.get_user_positions("0xUSER") == []


class TestGetRecentTrades:
    async def test_returns_empty_list(self) -> None:
        reader = AaveV3Reader()
        result = await reader.get_recent_trades("0xabc")
        assert result == []


class TestAaveV3ReaderProtocol:
    def test_implements_onchain_reader(self) -> None:
        from vireo_vigia.chains.base import OnchainReader

        reader = AaveV3Reader()
        assert isinstance(reader, OnchainReader)

    def test_create_from_settings(self) -> None:
        settings = MagicMock()
        settings.arbitrum_rpc_url = "https://arb1.arbitrum.io/rpc"
        from vireo_vigia.chains.evm import create_from_settings

        reader = create_from_settings(settings)
        assert reader._rpc_url == "https://arb1.arbitrum.io/rpc"
