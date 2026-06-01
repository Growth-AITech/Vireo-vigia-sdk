"""
Vireo Vigía Intelligence — AI-powered monitoring and analysis for DeFi protocols.

Modules:
    alerts       — condition-based alert engine (price, funding, liquidation)
    whale        — on-chain large-wallet movement tracker with AI context
    governance   — governance proposal summarizer powered by Claude
    digest       — daily/weekly portfolio digest generator
"""

from vireo_vigia.intelligence.alerts import AlertCondition, AlertEngine, AlertEvent
from vireo_vigia.intelligence.digest import PortfolioDigest
from vireo_vigia.intelligence.governance import GovernanceDigest
from vireo_vigia.intelligence.whale import WhaleAlert, WhaleTracker

__all__ = [
    "AlertCondition",
    "AlertEngine",
    "AlertEvent",
    "GovernanceDigest",
    "PortfolioDigest",
    "WhaleAlert",
    "WhaleTracker",
]
