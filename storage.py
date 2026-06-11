"""
storage.py — AuraTrader AI
Per-session in-memory data store (replaces SQLite).

Each browser tab gets its own SessionStore with isolated account,
positions, and trade history. The matching engine iterates all
active sessions to update prices and evaluate SL/TP.
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

import config

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_sessions: dict[str, "SessionStore"] = {}


# ---------------------------------------------------------------------------
# SessionStore — one per browser tab
# ---------------------------------------------------------------------------

class SessionStore:
    def __init__(self, session_id: str, balance: float) -> None:
        self.session_id = session_id
        self.account: dict[str, float] = {
            "balance": balance,
            "equity": balance,
            "used_margin": 0.0,
            "free_margin": balance,
        }
        self.positions: dict[int, dict] = {}
        self.history: list[dict] = []
        self._next_ticket = 1

    def _next_ticket_id(self) -> int:
        tid = self._next_ticket
        self._next_ticket += 1
        return tid

    def _recalculate(self) -> None:
        floating_pnl = 0.0
        used_margin = 0.0
        for pos in self.positions.values():
            units = pos["volume_lots"] * config.LOT_SIZE
            if pos["direction"] == "BUY":
                pnl = (pos["current_price"] - pos["entry_price"]) * units
            else:
                pnl = (pos["entry_price"] - pos["current_price"]) * units
            floating_pnl += pnl
            used_margin += pos["volume_lots"] * config.LOT_SIZE * pos["current_price"] * config.MARGIN_RATE

        bal = self.account["balance"]
        equity = bal + floating_pnl
        self.account["equity"] = equity
        self.account["used_margin"] = max(used_margin, 0.0)
        self.account["free_margin"] = equity - max(used_margin, 0.0)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def _new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def create_session(balance: float) -> SessionStore:
    sid = _new_session_id()
    with _lock:
        sd = SessionStore(sid, balance)
        _sessions[sid] = sd
        logger.info("Created session %s with balance %.2f", sid, balance)
        return sd


def get_session(session_id: str) -> Optional[SessionStore]:
    return _sessions.get(session_id)


def remove_session(session_id: str) -> None:
    with _lock:
        _sessions.pop(session_id, None)


def get_all_sessions() -> list[SessionStore]:
    with _lock:
        return list(_sessions.values())


# ---------------------------------------------------------------------------
# Position operations (called from pages with a specific session)
# ---------------------------------------------------------------------------

def open_position(
    session_id: str,
    instrument: str,
    direction: str,
    volume_lots: float,
    entry_price: float,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
) -> int:
    if direction not in ("BUY", "SELL"):
        raise ValueError(f"direction must be 'BUY' or 'SELL', got '{direction}'")
    if volume_lots <= 0:
        raise ValueError("volume_lots must be positive")

    with _lock:
        sd = _sessions.get(session_id)
        if sd is None:
            raise ValueError(f"Session {session_id} not found")

        tid = sd._next_ticket_id()
        sd.positions[tid] = {
            "ticket_id": tid,
            "instrument": instrument,
            "direction": direction,
            "volume_lots": volume_lots,
            "entry_price": entry_price,
            "current_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": _now_utc(),
        }
        sd._recalculate()
        logger.info("Opened position #%d: %s %s %.2f lots @ %.5f",
                     tid, direction, instrument, volume_lots, entry_price)
        return tid


def close_position(
    session_id: str,
    ticket_id: int,
    exit_price: float,
    exit_reason: str,
) -> Optional[dict]:
    if exit_reason not in ("TP", "SL", "MANUAL"):
        raise ValueError(f"exit_reason must be 'TP', 'SL', or 'MANUAL', got '{exit_reason}'")

    with _lock:
        sd = _sessions.get(session_id)
        if sd is None:
            return None

        pos = sd.positions.pop(ticket_id, None)
        if pos is None:
            logger.warning("close_position: ticket #%d not found in session %s", ticket_id, session_id)
            return None

        direction: str = pos["direction"]
        volume_lots: float = pos["volume_lots"]
        entry_price: float = pos["entry_price"]
        instrument: str = pos["instrument"]
        units: float = volume_lots * config.LOT_SIZE

        if direction == "BUY":
            profit_loss = (exit_price - entry_price) * units
        else:
            profit_loss = (entry_price - exit_price) * units

        record = {
            "ticket_id": ticket_id,
            "instrument": instrument,
            "direction": direction,
            "volume_lots": volume_lots,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "profit_loss": profit_loss,
            "exit_reason": exit_reason,
            "timestamp": _now_utc(),
        }
        sd.history.append(record)

        sd.account["balance"] += profit_loss
        sd._recalculate()

        logger.info("Closed position #%d | P&L: %.2f | Reason: %s",
                     ticket_id, profit_loss, exit_reason)
        return record


def close_all_positions(session_id: str, instrument: str) -> int:
    from matching_engine import get_latest_prices
    prices = get_latest_prices()
    closed = 0
    with _lock:
        sd = _sessions.get(session_id)
        if sd is None:
            return 0
        for tid, pos in list(sd.positions.items()):
            if pos["instrument"] != instrument:
                continue
            lp = prices.get(instrument, {})
            exit_p = lp.get("bid" if pos["direction"] == "BUY" else "ask", pos["current_price"])
            lp_prices = lp
            sd.positions.pop(tid, None)
            units = pos["volume_lots"] * config.LOT_SIZE
            if pos["direction"] == "BUY":
                pnl = (exit_p - pos["entry_price"]) * units
            else:
                pnl = (pos["entry_price"] - exit_p) * units
            record = {
                "ticket_id": tid,
                "instrument": pos["instrument"],
                "direction": pos["direction"],
                "volume_lots": pos["volume_lots"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_p,
                "profit_loss": pnl,
                "exit_reason": "MANUAL",
                "timestamp": _now_utc(),
            }
            sd.history.append(record)
            sd.account["balance"] += pnl
            closed += 1
        if closed:
            sd._recalculate()
    return closed


def get_open_positions(session_id: str) -> list[dict]:
    with _lock:
        sd = _sessions.get(session_id)
        if sd is None:
            return []
        return sorted(sd.positions.values(), key=lambda p: p["timestamp"], reverse=True)


def get_trade_history(session_id: str) -> list[dict]:
    with _lock:
        sd = _sessions.get(session_id)
        if sd is None:
            return []
        return list(reversed(sd.history))


def get_account(session_id: str) -> dict:
    with _lock:
        sd = _sessions.get(session_id)
        if sd is None:
            return {}
        return dict(sd.account)


# ---------------------------------------------------------------------------
# Engine-facing — operates on all sessions
# ---------------------------------------------------------------------------

def dispatch_tick_to_all_sessions(instrument: str, bid: float, ask: float) -> None:
    """
    Called by the matching engine on every tick.
    Updates current_price for all open positions of *instrument*,
    then checks SL/TP triggers across every active session.
    """
    with _lock:
        for sd in list(_sessions.values()):
            _update_positions_in_session(sd, instrument, bid, ask)
            _evaluate_sl_tp_in_session(sd, instrument, bid, ask)


def _update_positions_in_session(sd: SessionStore, instrument: str, bid: float, ask: float) -> None:
    for pos in sd.positions.values():
        if pos["instrument"] != instrument:
            continue
        pos["current_price"] = bid if pos["direction"] == "BUY" else ask
    sd._recalculate()


def _evaluate_sl_tp_in_session(sd: SessionStore, instrument: str, bid: float, ask: float) -> None:
    for tid, pos in list(sd.positions.items()):
        if pos["instrument"] != instrument:
            continue
        direction: str = pos["direction"]
        sl: float = pos["stop_loss"]
        tp: float = pos["take_profit"]

        exit_price: Optional[float] = None
        exit_reason: Optional[str] = None

        if direction == "BUY":
            if sl > 0 and bid <= sl:
                exit_price, exit_reason = bid, "SL"
            elif tp > 0 and bid >= tp:
                exit_price, exit_reason = bid, "TP"
        else:
            if sl > 0 and ask >= sl:
                exit_price, exit_reason = ask, "SL"
            elif tp > 0 and ask <= tp:
                exit_price, exit_reason = ask, "TP"

        if exit_price is not None and exit_reason is not None:
            logger.info(
                "Auto-closing #%d (%s %s) @ %.5f — %s triggered",
                tid, direction, instrument, exit_price, exit_reason,
            )
            pos_data = sd.positions.pop(tid, None)
            if pos_data is None:
                continue
            units = pos_data["volume_lots"] * config.LOT_SIZE
            pnl = (exit_price - pos_data["entry_price"]) * units if direction == "BUY" \
                else (pos_data["entry_price"] - exit_price) * units
            sd.history.append({
                "ticket_id": tid,
                "instrument": pos_data["instrument"],
                "direction": direction,
                "volume_lots": pos_data["volume_lots"],
                "entry_price": pos_data["entry_price"],
                "exit_price": exit_price,
                "profit_loss": pnl,
                "exit_reason": exit_reason,
                "timestamp": _now_utc(),
            })
            sd.account["balance"] += pnl
            sd._recalculate()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def all_session_count() -> int:
    with _lock:
        return len(_sessions)
