"""
AuraTrader AI — FastAPI Backend
REST API + WebSocket for real-time tick streaming.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
import matching_engine
import storage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TradeRequest(BaseModel):
    instrument: str
    direction: str
    volume_lots: float
    stop_loss: float = 0.0
    take_profit: float = 0.0

class CloseRequest(BaseModel):
    ticket_id: int
    exit_price: float

class CoPilotRequest(BaseModel):
    text: str

class SessionCreate(BaseModel):
    balance: float = 10_000.0

# ---------------------------------------------------------------------------
# WebSocket connections
# ---------------------------------------------------------------------------

_ws_clients: set[WebSocket] = set()
_tick_queue: asyncio.Queue | None = None


def _broadcast_tick(instrument: str, bid: float, ask: float) -> None:
    """Called from the matching engine thread — pushes to the async queue."""
    if _tick_queue is not None:
        try:
            _tick_queue.put_nowait({
                "type": "tick",
                "instrument": instrument,
                "bid": round(bid, 5),
                "ask": round(ask, 5),
            })
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Lifespan — start engine on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tick_queue
    _tick_queue = asyncio.Queue()

    matching_engine.subscribe(_broadcast_tick)
    matching_engine.start_engine_thread()

    # Background task to broadcast ticks to WebSocket clients
    async def _broadcast_loop():
        while True:
            try:
                msg = await asyncio.wait_for(_tick_queue.get(), timeout=1.0)
                dead = set()
                for ws in _ws_clients:
                    try:
                        await ws.send_json(msg)
                    except Exception:
                        dead.add(ws)
                _ws_clients.difference_update(dead)
            except asyncio.TimeoutError:
                continue
            except Exception:
                await asyncio.sleep(0.1)

    task = asyncio.create_task(_broadcast_loop())
    yield
    task.cancel()
    matching_engine.unsubscribe(_broadcast_tick)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AuraTrader AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_session(session_id: str) -> storage.SessionStore:
    sd = storage.get_session(session_id)
    if sd is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return sd


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "engine_alive": matching_engine.is_engine_alive()}


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@app.post("/api/session")
def create_session(body: SessionCreate):
    sd = storage.create_session(body.balance)
    return {"session_id": sd.session_id, "balance": body.balance}


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    sd = _get_session(session_id)
    return {
        "session_id": sd.session_id,
        "account": sd.account,
    }


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    storage.remove_session(session_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

@app.get("/api/account/{session_id}")
def get_account(session_id: str):
    acct = storage.get_account(session_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Session not found")
    return acct


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

@app.get("/api/prices")
def get_prices():
    return matching_engine.get_latest_prices()


@app.get("/api/prices/{instrument}")
def get_price(instrument: str):
    prices = matching_engine.get_latest_prices()
    if instrument not in prices:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return prices[instrument]


@app.get("/api/price-history/{instrument}")
def get_price_history(instrument: str):
    return matching_engine.get_price_history(instrument)


@app.get("/api/tick-log/{instrument}")
def get_tick_log(instrument: str):
    return matching_engine.get_tick_log(instrument)


# ---------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------

@app.get("/api/positions/{session_id}")
def get_positions(session_id: str):
    return storage.get_open_positions(session_id)


@app.post("/api/positions/{session_id}")
def open_position(session_id: str, body: TradeRequest):
    _get_session(session_id)  # validate session
    raw = matching_engine.get_latest_prices().get(body.instrument, {})
    if not raw:
        raise HTTPException(status_code=400, detail="No price data available")

    if body.direction == "BUY":
        raw_price = raw.get("ask", 0)
    else:
        raw_price = raw.get("bid", 0)

    if not raw_price:
        raise HTTPException(status_code=400, detail="Invalid price")

    ep = matching_engine.apply_spread_and_slippage(raw_price, body.direction)
    ticket = storage.open_position(
        session_id, body.instrument, body.direction,
        body.volume_lots, ep, body.stop_loss, body.take_profit,
    )
    return {"ticket_id": ticket, "entry_price": ep}


@app.post("/api/positions/{session_id}/close")
def close_position(session_id: str, body: CloseRequest):
    result = storage.close_position(session_id, body.ticket_id, body.exit_price, "MANUAL")
    if result is None:
        raise HTTPException(status_code=404, detail="Position not found")
    return result


@app.post("/api/positions/{session_id}/close-all/{instrument}")
def close_all_positions(session_id: str, instrument: str):
    closed = storage.close_all_positions(session_id, instrument)
    return {"closed": closed}


# ---------------------------------------------------------------------------
# Trade history
# ---------------------------------------------------------------------------

@app.get("/api/history/{session_id}")
def get_history(session_id: str):
    return storage.get_trade_history(session_id)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.get("/api/metrics/{session_id}")
def get_metrics(session_id: str):
    history = storage.get_trade_history(session_id)
    acct = storage.get_account(session_id)
    positions = storage.get_open_positions(session_id)

    if not history:
        return {
            "total_pnl": 0.0, "win_rate": 0.0, "total_trades": 0,
            "best_trade": 0.0, "worst_trade": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
            "sharpe": 0.0, "sortino": 0.0, "max_drawdown": 0.0,
            "balance": acct.get("balance", 0.0), "equity": acct.get("equity", 0.0),
            "floating_pnl": acct.get("equity", 0.0) - acct.get("balance", 0.0),
            "open_positions": len(positions),
        }

    import pandas as pd
    import numpy as np

    df = pd.DataFrame(history)
    pnls = df["profit_loss"].values

    wins = int((pnls > 0).sum())
    losses = int((pnls <= 0).sum())
    total = wins + losses

    # Sharpe & Sortino (annualized, assume ~86400 ticks/day)
    if len(pnls) > 1:
        mean_ret = np.mean(pnls)
        std_ret = np.std(pnls, ddof=1)
        downside = np.std(pnls[pnls < 0], ddof=1) if (pnls < 0).any() else 1.0
        sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0
        sortino = (mean_ret / downside * np.sqrt(252)) if downside > 0 else 0.0
    else:
        sharpe = sortino = 0.0

    # Max drawdown
    equity_curve = np.cumsum(pnls) + acct.get("balance", 0.0)
    peak = np.maximum.accumulate(equity_curve)
    drawdowns = (peak - equity_curve) / np.where(peak > 0, peak, 1.0)
    max_dd = float(np.max(drawdowns)) * 100 if len(drawdowns) > 0 else 0.0

    return {
        "total_pnl": float(pnls.sum()),
        "win_rate": (wins / total * 100) if total else 0.0,
        "total_trades": total,
        "best_trade": float(pnls.max()),
        "worst_trade": float(pnls.min()),
        "avg_win": float(pnls[pnls > 0].mean()) if wins else 0.0,
        "avg_loss": float(pnls[pnls <= 0].mean()) if losses else 0.0,
        "sharpe": round(float(sharpe), 2),
        "sortino": round(float(sortino), 2),
        "max_drawdown": round(max_dd, 2),
        "balance": acct.get("balance", 0.0),
        "equity": acct.get("equity", 0.0),
        "floating_pnl": acct.get("equity", 0.0) - acct.get("balance", 0.0),
        "open_positions": len(positions),
    }


# ---------------------------------------------------------------------------
# AI Agents
# ---------------------------------------------------------------------------

@app.post("/api/copilot")
def copilot_parse(body: CoPilotRequest):
    import ai_agents
    return ai_agents.agent_a_parse_trade(body.text)


@app.post("/api/sentiment")
def get_sentiment():
    import ai_agents
    return ai_agents.agent_b_market_sentiment()


@app.get("/api/data-source")
def get_data_source():
    return {"source": matching_engine.get_data_source()}


# ---------------------------------------------------------------------------
# Config (read-only)
# ---------------------------------------------------------------------------

@app.get("/api/config")
def get_config():
    return {
        "starting_balance": config.STARTING_BALANCE,
        "spread_pips": config.DEFAULT_SPREAD_PIPS,
        "max_slippage_pips": config.MAX_SLIPPAGE_PIPS,
        "margin_rate": config.MARGIN_RATE,
        "lot_size": config.LOT_SIZE,
        "pip_size": config.PIP_SIZE,
        "tick_interval": config.TICK_INTERVAL_SECONDS,
        "sma_fast": config.SMA_FAST_PERIOD,
        "sma_slow": config.SMA_SLOW_PERIOD,
        "auto_sl_pips": config.AUTO_SL_PIPS,
        "auto_tp_pips": config.AUTO_TP_PIPS,
        "instruments": config.INSTRUMENTS,
    }


# ---------------------------------------------------------------------------
# WebSocket — real-time tick stream
# ---------------------------------------------------------------------------

@app.websocket("/ws/ticks")
async def ws_ticks(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            # Keep connection alive; ignore incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)
