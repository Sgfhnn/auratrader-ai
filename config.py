"""
config.py — AuraTrader AI
Central configuration: API keys, trading constants, risk management limits.
All secrets are read from environment variables with empty-string fallbacks so
the application boots even without credentials (mock mode activates automatically).
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# LLM Provider API Keys
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
NVIDIA_NIM_API_KEY: str = os.environ.get("NVIDIA_NIM_API_KEY", "")

# ---------------------------------------------------------------------------
# OANDA Brokerage Credentials (optional — mock tick generator used if absent)
# ---------------------------------------------------------------------------
OANDA_API_KEY: str = os.environ.get("OANDA_API_KEY", "")
OANDA_ACCOUNT_ID: str = os.environ.get("OANDA_ACCOUNT_ID", "")

# ---------------------------------------------------------------------------
# LLM Base URLs
# ---------------------------------------------------------------------------
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
NVIDIA_NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

# ---------------------------------------------------------------------------
# Virtual Account Defaults
# ---------------------------------------------------------------------------
STARTING_BALANCE: float = 100_000.00

# ---------------------------------------------------------------------------
# Execution / Risk Constants
# ---------------------------------------------------------------------------
DEFAULT_SPREAD_PIPS: float = 1.5
MAX_SLIPPAGE_PIPS: float = 0.5

# Pip value for major pairs quoted vs USD (e.g., EUR/USD, GBP/USD)
PIP_SIZE: float = 0.0001

# Margin requirement: 2 % of notional (50:1 leverage)
MARGIN_RATE: float = 0.02

# Contract size: 1 standard lot = 100,000 units of base currency
LOT_SIZE: int = 100_000

# ---------------------------------------------------------------------------
# Matching Engine
# ---------------------------------------------------------------------------
TICK_INTERVAL_SECONDS: float = 1.0   # interval between mock ticks

# ---------------------------------------------------------------------------
# Instruments available for trading
# ---------------------------------------------------------------------------
INSTRUMENTS: list[str] = [
    "EUR_USD",
    "GBP_USD",
    "USD_JPY",
    "AUD_USD",
    "USD_CAD",
]

# ---------------------------------------------------------------------------
# Autonomous Mode — Simple Moving Average windows
# ---------------------------------------------------------------------------
SMA_FAST_PERIOD: int = 5    # ticks
SMA_SLOW_PERIOD: int = 20   # ticks

# ---------------------------------------------------------------------------
# Autonomous Mode — default SL / TP distances (in pips)
# ---------------------------------------------------------------------------
AUTO_SL_PIPS: int = 20
AUTO_TP_PIPS: int = 40
