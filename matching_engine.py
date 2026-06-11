"""
matching_engine.py — AuraTrader AI
Asynchronous real-time tick evaluation loop.

Data source priority (automatic tier selection)
------------------------------------------------
  1. OANDA streaming    — if OANDA_API_KEY + OANDA_ACCOUNT_ID are set
  2. yfinance real data — fetches Yahoo Finance FX rates every 30 s and reseeds
                          the random-walk generator so prices stay anchored to
                          reality even without a broker connection
  3. Pure mock          — self-contained random-walk if yfinance is not installed

On every incoming price tick, all open positions are evaluated:
  - BUY  positions: close if Bid <= stop_loss OR Bid >= take_profit
  - SELL positions: close if Ask >= stop_loss OR Ask <= take_profit

Execution friction is applied when opening positions:
  - Spread penalty: DEFAULT_SPREAD_PIPS added to the execution price
  - Slippage:       random.uniform(0, MAX_SLIPPAGE_PIPS) * PIP_SIZE
"""

from __future__ import annotations

import logging
import random
import time
from collections import deque
from datetime import datetime
from typing import Callable, Deque, Dict, Generator, List, Optional

import requests

try:
    import yfinance as yf
    _YFINANCE_AVAILABLE: bool = True
except ImportError:
    yf = None  # type: ignore[assignment]
    _YFINANCE_AVAILABLE: bool = False

import config
import storage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
TickCallback = Callable[[str, float, float], None]

# ---------------------------------------------------------------------------
# In-memory price history (mid prices, used for SMA computation)
# ---------------------------------------------------------------------------
_price_history: Dict[str, Deque[float]] = {
    instrument: deque(maxlen=config.SMA_SLOW_PERIOD + 5)
    for instrument in config.INSTRUMENTS
}

# Timestamped tick log — read by Home.py / pages for candlestick charts (thread-safe append)
_tick_log: Dict[str, Deque[dict]] = {
    instrument: deque(maxlen=200)
    for instrument in config.INSTRUMENTS
}

# Latest bid/ask keyed by instrument — populated by dispatch_tick
_latest_prices: Dict[str, Dict[str, float]] = {}

# Tick subscriber callbacks
_tick_subscribers: list[TickCallback] = []

# Human-readable data source label read by Home.py / pages
_data_source: str = "MOCK"

# Last tick timestamp (for health check)
_last_tick_time: float = 0.0


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

def get_data_source() -> str:
    return _data_source


def is_engine_alive() -> bool:
    return (time.time() - _last_tick_time) < 10.0


def get_latest_prices() -> Dict[str, Dict[str, float]]:
    return dict(_latest_prices)


def get_price_history(instrument: str) -> list[float]:
    return list(_price_history.get(instrument, deque()))


def get_tick_log(instrument: str) -> List[dict]:
    """Return a list of {time, bid, ask, mid} dicts for building charts."""
    return list(_tick_log.get(instrument, deque()))


def subscribe(callback: TickCallback) -> None:
    _tick_subscribers.append(callback)


def unsubscribe(callback: TickCallback) -> None:
    if callback in _tick_subscribers:
        _tick_subscribers.remove(callback)


# ---------------------------------------------------------------------------
# Execution friction
# ---------------------------------------------------------------------------

def apply_spread_and_slippage(
    price: float,
    direction: str,
    spread_pips: float = config.DEFAULT_SPREAD_PIPS,
    max_slippage_pips: float = config.MAX_SLIPPAGE_PIPS,
) -> float:
    slippage = random.uniform(0.0, max_slippage_pips) * config.PIP_SIZE
    half_spread = (spread_pips * config.PIP_SIZE) / 2.0
    if direction == "BUY":
        return price + half_spread + slippage
    else:
        return price - half_spread - slippage


# ---------------------------------------------------------------------------
# Tick dispatcher
# ---------------------------------------------------------------------------

def _dispatch_tick(instrument: str, bid: float, ask: float) -> None:
    global _last_tick_time
    _last_tick_time = time.time()
    _latest_prices[instrument] = {"bid": bid, "ask": ask}
    mid = (bid + ask) / 2.0
    _price_history[instrument].append(mid)
    _tick_log[instrument].append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "bid": bid,
        "ask": ask,
        "mid": mid,
    })

    storage.dispatch_tick_to_all_sessions(instrument, bid, ask)

    for cb in _tick_subscribers:
        try:
            cb(instrument, bid, ask)
        except Exception as exc:
            logger.warning("Tick subscriber error: %s", exc)


# ---------------------------------------------------------------------------
# Mock tick generator (random walk)
# ---------------------------------------------------------------------------

_BASE_PRICES: Dict[str, float] = {
    "EUR_USD": 1.08500,
    "GBP_USD": 1.27000,
    "USD_JPY": 149.500,
    "AUD_USD": 0.65500,
    "USD_CAD": 1.36000,
}

_current_prices: Dict[str, float] = dict(_BASE_PRICES)

# Pre-seed latest_prices so they're available before the first tick
_half_spread = (config.DEFAULT_SPREAD_PIPS * config.PIP_SIZE) / 2.0
for _inst, _mid in _BASE_PRICES.items():
    _latest_prices[_inst] = {"bid": round(_mid - _half_spread, 5), "ask": round(_mid + _half_spread, 5)}


def _next_mock_tick(instrument: str) -> tuple[float, float]:
    prev = _current_prices.get(instrument, _BASE_PRICES.get(instrument, 1.0))
    drift = random.uniform(-0.5, 0.5) * config.PIP_SIZE
    reversion = (_BASE_PRICES.get(instrument, prev) - prev) * 0.001
    new_mid = prev + drift + reversion
    _current_prices[instrument] = new_mid
    half_spread = (config.DEFAULT_SPREAD_PIPS * config.PIP_SIZE) / 2.0
    return round(new_mid - half_spread, 5), round(new_mid + half_spread, 5)


def _run_mock_loop() -> None:
    """Background thread loop — generates mock ticks sequentially."""
    logger.info("Mock tick generator activated.")
    instruments = config.INSTRUMENTS
    idx = 0
    interval = config.TICK_INTERVAL_SECONDS / len(instruments)
    while True:
        try:
            instrument = instruments[idx % len(instruments)]
            bid, ask = _next_mock_tick(instrument)
            _dispatch_tick(instrument, bid, ask)
            idx += 1
            time.sleep(interval)
        except Exception as exc:
            logger.warning("Mock tick error: %s", exc)
            time.sleep(0.5)


# ---------------------------------------------------------------------------
# yfinance real-data reseeder
# ---------------------------------------------------------------------------

# Maps our instrument names to Yahoo Finance ticker symbols
_YAHOO_MAP: Dict[str, str] = {
    "EUR_USD": "EURUSD=X",
    "GBP_USD": "GBPUSD=X",
    "USD_JPY": "USDJPY=X",
    "AUD_USD": "AUDUSD=X",
    "USD_CAD": "USDCAD=X",
}

def _check_yfinance() -> bool:
    return _YFINANCE_AVAILABLE


def _fetch_real_prices_blocking() -> Dict[str, float]:
    """Fetch latest FX prices from Yahoo Finance. Runs in a thread executor."""
    if not _YFINANCE_AVAILABLE:
        return {}
    updates: Dict[str, float] = {}
    for instrument, symbol in _YAHOO_MAP.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if hist is not None and not hist.empty:
                price = float(hist["Close"].iloc[-1])
                if price > 0:
                    updates[instrument] = price
        except Exception as exc:
            logger.debug("yfinance fetch skipped for %s: %s", instrument, exc)
    return updates


def _run_yfinance_loop() -> None:
    """
    Background thread — periodically fetch real prices and reseed the
    random-walk base prices so the simulation stays anchored to reality.
    """
    global _data_source
    if not _check_yfinance():
        logger.info("yfinance not installed — pure mock mode.")
        return

    _data_source = "REAL (Yahoo Finance, ~15 min delayed)"
    logger.info("yfinance real-data reseeder started.")

    while True:
        try:
            updates = _fetch_real_prices_blocking()
            for instrument, price in updates.items():
                _current_prices[instrument] = price
                _BASE_PRICES[instrument] = price
            if updates:
                logger.info(
                    "yfinance reseeded %d instruments. EUR_USD=%.5f",
                    len(updates),
                    updates.get("EUR_USD", 0.0),
                )
        except Exception as exc:
            logger.warning("yfinance reseed error: %s", exc)
        time.sleep(30)


# ---------------------------------------------------------------------------
# OANDA live streaming
# ---------------------------------------------------------------------------

def _oanda_stream_ticks() -> Generator[dict, None, None]:
    instruments_param = "%2C".join(config.INSTRUMENTS)
    url = (
        f"https://stream-fxtrade.oanda.com/v3/accounts/"
        f"{config.OANDA_ACCOUNT_ID}/pricing/stream"
        f"?instruments={instruments_param}"
    )
    headers = {
        "Authorization": f"Bearer {config.OANDA_API_KEY}",
        "Accept-Encoding": "gzip, deflate",
    }
    with requests.get(url, headers=headers, stream=True, timeout=30) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            try:
                import json
                data = json.loads(line)
                if data.get("type") != "PRICE":
                    continue
                yield {
                    "instrument": data["instrument"],
                    "bid": float(data["bids"][0]["price"]),
                    "ask": float(data["asks"][0]["price"]),
                }
            except Exception as exc:
                logger.debug("OANDA parse error: %s", exc)


def _run_oanda_loop() -> None:
    """Background thread — connects to OANDA live stream and dispatches ticks."""
    global _data_source
    _data_source = "LIVE (OANDA)"
    logger.info("Connecting to OANDA live stream…")
    try:
        for tick in _oanda_stream_ticks():
            _dispatch_tick(tick["instrument"], tick["bid"], tick["ask"])
    except Exception as exc:
        logger.error("OANDA stream failed: %s — falling back to mock.", exc)
        _data_source = "REAL (Yahoo Finance, ~15 min delayed)"
        _run_mock_loop()


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def start_engine_thread() -> None:
    """Start the matching engine background threads (daemon)."""
    import threading

    if config.OANDA_API_KEY and config.OANDA_ACCOUNT_ID:
        t = threading.Thread(target=_run_oanda_loop, daemon=True, name="OANDA")
        t.start()
    else:
        t1 = threading.Thread(target=_run_mock_loop, daemon=True, name="MockTicks")
        t1.start()
        t2 = threading.Thread(target=_run_yfinance_loop, daemon=True, name="YFinance")
        t2.start()

    logger.info("Matching engine started in background thread(s).")
