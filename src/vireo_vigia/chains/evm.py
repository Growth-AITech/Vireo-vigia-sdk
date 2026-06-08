"""
Aave V3 on Arbitrum — read-only on-chain reader.

Implements ``OnchainReader`` Protocol using Web3.py against the
Arbitrum mainnet (or any EVM-compatible RPC).

Aave V3 Arbitrum contract addresses (mainnet):
  Pool:                       0x794a61358D6845594F94dc1DB02A252b5b4814aD
  PoolAddressesProvider:      0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb
  AaveOracle:                 0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7
  AaveProtocolDataProvider:   0x243Aa95cAC2a25651eda86e80bEe66114413c43b

Usage::

    async with AaveV3Reader() as reader:
        balance = await reader.get_user_balance("0xYOUR_WALLET")
        positions = await reader.get_user_positions("0xYOUR_WALLET")
"""

from __future__ import annotations

from typing import Any

from vireo_vigia.exceptions import ChainConnectionError, ChainDataError
from vireo_vigia.logging import get_logger

_log = get_logger(__name__)

# ── Arbitrum mainnet contract addresses ───────────────────────────────────────

_POOL_ADDR = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
_POOL_ADDRESSES_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"
_AAVE_ORACLE = "0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7"
# AaveProtocolDataProvider (a.k.a. PoolDataProvider). Resolved at runtime from the
# PoolAddressesProvider; this is the current Arbitrum deployment used as fallback.
# Preferred over UiPoolDataProvider — its ABI is stable across Aave V3 versions,
# returns balances in real token units, and never reverts on struct drift.
_PROTOCOL_DATA_PROVIDER = "0x243Aa95cAC2a25651eda86e80bEe66114413c43b"
_DEFAULT_RPC = "https://arb1.arbitrum.io/rpc"

# ── Minimal ABIs ──────────────────────────────────────────────────────────────

_POOL_ABI: list[dict[str, Any]] = [
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"name": "totalCollateralBase", "type": "uint256"},
            {"name": "totalDebtBase", "type": "uint256"},
            {"name": "availableBorrowsBase", "type": "uint256"},
            {"name": "currentLiquidationThreshold", "type": "uint256"},
            {"name": "ltv", "type": "uint256"},
            {"name": "healthFactor", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getReservesList",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# PoolAddressesProvider — resolves the canonical PoolDataProvider address.
_PROVIDER_ABI: list[dict[str, Any]] = [
    {
        "inputs": [],
        "name": "getPoolDataProvider",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# AaveProtocolDataProvider — stable ABI, balances already in real token units.
_PDP_ABI: list[dict[str, Any]] = [
    {
        "inputs": [],
        "name": "getAllReservesTokens",
        "outputs": [
            {
                "components": [
                    {"name": "symbol", "type": "string"},
                    {"name": "tokenAddress", "type": "address"},
                ],
                "name": "",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "user", "type": "address"},
        ],
        "name": "getUserReserveData",
        "outputs": [
            {"name": "currentATokenBalance", "type": "uint256"},
            {"name": "currentStableDebt", "type": "uint256"},
            {"name": "currentVariableDebt", "type": "uint256"},
            {"name": "principalStableDebt", "type": "uint256"},
            {"name": "scaledVariableDebt", "type": "uint256"},
            {"name": "stableBorrowRate", "type": "uint256"},
            {"name": "liquidityRate", "type": "uint256"},
            {"name": "stableRateLastUpdated", "type": "uint40"},
            {"name": "usageAsCollateralEnabled", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {"name": "unbacked", "type": "uint256"},
            {"name": "accruedToTreasury", "type": "uint256"},
            {"name": "totalAToken", "type": "uint256"},
            {"name": "totalStableDebt", "type": "uint256"},
            {"name": "totalVariableDebt", "type": "uint256"},
            {"name": "liquidityRate", "type": "uint256"},
            {"name": "variableBorrowRate", "type": "uint256"},
            {"name": "stableBorrowRate", "type": "uint256"},
            {"name": "averageStableBorrowRate", "type": "uint256"},
            {"name": "liquidityIndex", "type": "uint256"},
            {"name": "variableBorrowIndex", "type": "uint256"},
            {"name": "lastUpdateTimestamp", "type": "uint40"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getReserveConfigurationData",
        "outputs": [
            {"name": "decimals", "type": "uint256"},
            {"name": "ltv", "type": "uint256"},
            {"name": "liquidationThreshold", "type": "uint256"},
            {"name": "liquidationBonus", "type": "uint256"},
            {"name": "reserveFactor", "type": "uint256"},
            {"name": "usageAsCollateralEnabled", "type": "bool"},
            {"name": "borrowingEnabled", "type": "bool"},
            {"name": "stableBorrowRateEnabled", "type": "bool"},
            {"name": "isActive", "type": "bool"},
            {"name": "isFrozen", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# AaveOracle — asset prices in the base currency (USD, 8 decimals).
_ORACLE_ABI: list[dict[str, Any]] = [
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getAssetPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Minimal ERC-20 — only the metadata we read.
_ERC20_ABI: list[dict[str, Any]] = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

_WAD = 10**18
_RAY = 10**27
_BASE_CURRENCY_UNIT = 10**8  # Aave oracle prices in USD with 8 decimals


def _ray_to_apy(ray_rate: int) -> float:
    """Convert an Aave RAY-denominated annual rate (APR) to a compounded APY.

    Aave V3 expresses ``liquidityRate`` / ``variableBorrowRate`` as an annual
    percentage rate scaled by 1e27. APY applies per-second compounding:
    ``(1 + APR / secondsPerYear) ** secondsPerYear - 1``.
    """
    seconds_per_year = 365 * 24 * 3600
    apr = ray_rate / _RAY
    return (1 + apr / seconds_per_year) ** seconds_per_year - 1


class AaveV3Reader:
    """
    Read-only Aave V3 client for Arbitrum mainnet.

    Satisfies the ``OnchainReader`` Protocol.

    For DeFi protocols on Arbitrum: shows user collateral positions,
    borrows, health factor, and per-market borrow/supply rates.

    Args:
        rpc_url: Arbitrum JSON-RPC endpoint.
        pool_address: Aave V3 Pool contract address.
        max_retries: Retry attempts on transient RPC failures.
    """

    def __init__(
        self,
        rpc_url: str = _DEFAULT_RPC,
        *,
        pool_address: str = _POOL_ADDR,
        max_retries: int = 3,
    ) -> None:
        self._rpc_url = rpc_url
        self._pool_addr = pool_address
        self._max_retries = max_retries
        self._w3: Any = None
        self._pdp: Any = None  # cached AaveProtocolDataProvider contract
        self._decimals_cache: dict[str, int] = {}

    # ── Context manager ───────────────────────────────────────────────────────

    async def __aenter__(self) -> AaveV3Reader:
        self._get_w3()
        return self

    async def __aexit__(self, *_: object) -> None:
        pass  # web3 AsyncHTTPProvider has no explicit close

    def _get_w3(self) -> Any:  # noqa: ANN401
        if self._w3 is None:
            try:
                from web3 import AsyncWeb3
                from web3.providers import AsyncHTTPProvider

                self._w3 = AsyncWeb3(AsyncHTTPProvider(self._rpc_url))
            except ImportError as exc:
                raise ChainConnectionError(
                    "web3 not installed. Run: uv add web3",
                    code="CHAIN_IMPORT",
                ) from exc
        return self._w3

    async def _pdp_contract(self) -> Any:  # noqa: ANN401
        """Return the AaveProtocolDataProvider contract, resolving its address once.

        The canonical address is read from the PoolAddressesProvider; on any
        failure we fall back to the known Arbitrum deployment constant.
        """
        if self._pdp is None:
            w3 = self._get_w3()
            addr = _PROTOCOL_DATA_PROVIDER
            try:
                provider = w3.eth.contract(
                    address=w3.to_checksum_address(_POOL_ADDRESSES_PROVIDER),
                    abi=_PROVIDER_ABI,
                )
                addr = await provider.functions.getPoolDataProvider().call()
            except Exception as exc:  # provider lookup is best-effort
                _log.debug("aave_pdp_lookup_fallback", error=str(exc)[:120])
            self._pdp = w3.eth.contract(
                address=w3.to_checksum_address(addr), abi=_PDP_ABI
            )
        return self._pdp

    async def _decimals(self, asset: str) -> int:
        """Return (and cache) an ERC-20 token's decimals."""
        key = asset.lower()
        if key not in self._decimals_cache:
            w3 = self._get_w3()
            erc20 = w3.eth.contract(
                address=w3.to_checksum_address(asset), abi=_ERC20_ABI
            )
            self._decimals_cache[key] = int(await erc20.functions.decimals().call())
        return self._decimals_cache[key]

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_user_positions(self, wallet: str) -> list[dict[str, Any]]:
        """
        Return active Aave V3 positions (supplies + borrows) for a wallet.

        Positions with zero balance are excluded.

        Returns:
            List of dicts with keys matching ``AaveUserPosition``:
            asset_symbol, asset_address, position_type, balance_usd,
            apy, is_collateral.
        """
        w3 = self._get_w3()
        try:
            pdp = await self._pdp_contract()
            oracle = w3.eth.contract(
                address=w3.to_checksum_address(_AAVE_ORACLE), abi=_ORACLE_ABI
            )
            user = w3.to_checksum_address(wallet)
            tokens = await pdp.functions.getAllReservesTokens().call()

            positions: list[dict[str, Any]] = []
            for symbol, asset in tokens:
                ud = await pdp.functions.getUserReserveData(asset, user).call()
                a_balance, _stable_debt, var_debt = ud[0], ud[1], ud[2]
                if a_balance == 0 and var_debt == 0:
                    continue

                decimals = await self._decimals(asset)
                price_usd = (
                    await oracle.functions.getAssetPrice(asset).call()
                ) / _BASE_CURRENCY_UNIT
                unit = 10**decimals

                if a_balance > 0:
                    positions.append(
                        {
                            "asset_symbol": symbol,
                            "asset_address": asset,
                            "position_type": "supply",
                            "balance_usd": (a_balance / unit) * price_usd,
                            "apy": _ray_to_apy(ud[6]),  # liquidityRate
                            "is_collateral": bool(ud[8]),  # usageAsCollateralEnabled
                        }
                    )
                if var_debt > 0:
                    rd = await pdp.functions.getReserveData(asset).call()
                    positions.append(
                        {
                            "asset_symbol": symbol,
                            "asset_address": asset,
                            "position_type": "borrow",
                            "balance_usd": (var_debt / unit) * price_usd,
                            "apy": _ray_to_apy(rd[6]),  # variableBorrowRate
                            "is_collateral": False,
                        }
                    )
        except Exception as exc:
            if isinstance(exc, ChainConnectionError):
                raise
            # Empty wallet or transient RPC issue — degrade gracefully.
            _log.warning("aave_positions_unavailable", error=str(exc)[:120])
            return []

        _log.debug("aave_positions_fetched", wallet=wallet[:10], count=len(positions))
        return positions

    async def get_user_balance(self, wallet: str) -> dict[str, Any]:
        """
        Return Aave V3 account health summary for a wallet.

        Returns:
            Dict with keys matching ``AaveAccountSummary``:
            total_collateral_usd, total_debt_usd, available_borrow_usd,
            current_ltv, liquidation_threshold, health_factor.
        """
        w3 = self._get_w3()
        try:
            pool = w3.eth.contract(
                address=w3.to_checksum_address(self._pool_addr),
                abi=_POOL_ABI,
            )
            result = await pool.functions.getUserAccountData(
                w3.to_checksum_address(wallet)
            ).call()
        except Exception as exc:
            raise ChainConnectionError(f"Aave getUserAccountData failed: {exc}") from exc

        total_col, total_debt, avail_borrow, liq_threshold, ltv, hf = result
        unit = _BASE_CURRENCY_UNIT
        wad = _WAD

        # Aave returns type(uint256).max when there is no debt (health factor = infinity)
        # Cap at 999 for display purposes
        raw_health = hf / wad
        health = min(raw_health, 999.0)
        _log.debug("aave_balance_fetched", wallet=wallet[:10], health_factor=health)

        return {
            "total_collateral_usd": total_col / unit,
            "total_debt_usd": total_debt / unit,
            "available_borrow_usd": avail_borrow / unit,
            "current_ltv": ltv / 10_000,
            "liquidation_threshold": liq_threshold / 10_000,
            "health_factor": health,
        }

    async def get_recent_trades(self, wallet: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Aave V3 does not have a native trades/fills concept.

        Returns an empty list — Aave protocol interactions are tracked
        via on-chain events, which require an indexer not available here.
        """
        _log.debug("aave_recent_trades_not_supported")
        return []

    async def get_funding_rate(self, asset: str) -> dict[str, Any]:
        """
        Return Aave V3 borrow/supply APYs for a given asset symbol.

        Args:
            asset: Token symbol (e.g. ``"USDC"``, ``"WETH"``, ``"ARB"``).

        Returns:
            Dict with keys: asset, supply_apy, variable_borrow_apy,
            stable_borrow_apy, utilization_rate.

        Raises:
            ChainDataError: If the asset is not found in Aave V3 Arbitrum.
        """
        market = await self.get_market_info(asset)
        return {
            "asset": market["asset_symbol"],
            "supply_apy": market["supply_apy"],
            "variable_borrow_apy": market["variable_borrow_apy"],
            "stable_borrow_apy": market["stable_borrow_apy"],
            "utilization_rate": market["utilization_rate"],
        }

    async def get_market_info(self, asset: str) -> dict[str, Any]:
        """
        Return full market data for an Aave V3 Arbitrum asset.

        Args:
            asset: Token symbol (case-insensitive, e.g. ``"USDC"``, ``"WETH"``).

        Returns:
            Dict with keys matching ``AaveMarket``.

        Raises:
            ChainDataError: If asset symbol not found in Aave V3 reserves.
        """
        w3 = self._get_w3()
        try:
            pdp = await self._pdp_contract()
            tokens = await pdp.functions.getAllReservesTokens().call()
        except Exception as exc:
            raise ChainConnectionError(f"Aave getAllReservesTokens failed: {exc}") from exc

        target = asset.upper()
        for symbol, addr in tokens:
            if symbol.upper() != target:
                continue

            oracle = w3.eth.contract(
                address=w3.to_checksum_address(_AAVE_ORACLE), abi=_ORACLE_ABI
            )
            decimals = await self._decimals(addr)
            price_usd = (await oracle.functions.getAssetPrice(addr).call()) / _BASE_CURRENCY_UNIT
            unit = 10**decimals

            rd = await pdp.functions.getReserveData(addr).call()
            cfg = await pdp.functions.getReserveConfigurationData(addr).call()

            total_atoken = rd[2]  # total supplied
            total_stable_debt = rd[3]
            total_var_debt = rd[4]
            supply_apy = _ray_to_apy(rd[5])  # liquidityRate
            var_borrow_apy = _ray_to_apy(rd[6])  # variableBorrowRate
            stable_borrow_apy = _ray_to_apy(rd[7])  # stableBorrowRate

            total_debt = total_var_debt + total_stable_debt
            util = total_debt / total_atoken if total_atoken > 0 else 0.0

            _log.debug("aave_market_fetched", asset=asset, supply_apy=supply_apy)
            return {
                "asset_symbol": symbol,
                "asset_address": addr,
                "supply_apy": supply_apy,
                "variable_borrow_apy": var_borrow_apy,
                "stable_borrow_apy": stable_borrow_apy,
                "total_supplied_usd": (total_atoken / unit) * price_usd,
                "total_borrowed_usd": (total_debt / unit) * price_usd,
                "utilization_rate": util,
                "ltv": int(cfg[1]) / 10_000,
                "liquidation_threshold": int(cfg[2]) / 10_000,
            }

        raise ChainDataError(
            f"Asset '{asset}' not found in Aave V3 Arbitrum reserves",
            code="CHAIN_DATA",
        )


def create_from_settings(settings: Any) -> AaveV3Reader:  # noqa: ANN401
    """Factory: build an ``AaveV3Reader`` from a ``VireoSettings`` instance."""
    return AaveV3Reader(rpc_url=settings.arbitrum_rpc_url)
