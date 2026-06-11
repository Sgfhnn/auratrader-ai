"""Tests for storage.py — In-memory per-session data store."""

import pytest

import config
import storage


class TestCreateSession:
    def test_account_seeded(self, sid) -> None:
        acct = storage.get_account(sid)
        assert acct["balance"] == config.STARTING_BALANCE
        assert acct["equity"] == config.STARTING_BALANCE
        assert acct["used_margin"] == 0.0
        assert acct["free_margin"] == config.STARTING_BALANCE


class TestOpenAndClosePosition:
    def test_open_buy(self, sid) -> None:
        tid = storage.open_position(sid, "EUR_USD", "BUY", 1.0, 1.08500, stop_loss=1.08000, take_profit=1.09500)
        assert tid > 0

        pos = storage.get_open_positions(sid)
        assert len(pos) == 1
        assert pos[0]["ticket_id"] == tid
        assert pos[0]["direction"] == "BUY"
        assert pos[0]["volume_lots"] == 1.0

    def test_open_sell(self, sid) -> None:
        tid = storage.open_position(sid, "GBP_USD", "SELL", 0.5, 1.27000)
        assert tid > 0
        pos = storage.get_open_positions(sid)
        assert len(pos) == 1

    def test_open_invalid_direction(self, sid) -> None:
        with pytest.raises(ValueError, match="direction"):
            storage.open_position(sid, "EUR_USD", "INVALID", 0.1, 1.0)

    def test_open_zero_volume(self, sid) -> None:
        with pytest.raises(ValueError, match="volume_lots must be positive"):
            storage.open_position(sid, "EUR_USD", "BUY", 0, 1.0)

    def test_close_position_updates_balance(self, sid) -> None:
        entry = 1.08500
        exit_p = 1.09500  # profitable
        tid = storage.open_position(sid, "EUR_USD", "BUY", 1.0, entry)
        result = storage.close_position(sid, tid, exit_p, "TP")

        assert result is not None
        assert result["profit_loss"] == pytest.approx((exit_p - entry) * config.LOT_SIZE)
        assert result["exit_reason"] == "TP"

        # Position should be removed from open
        assert len(storage.get_open_positions(sid)) == 0

        # Balance increased
        acct = storage.get_account(sid)
        expected_balance = config.STARTING_BALANCE + (exit_p - entry) * config.LOT_SIZE
        assert acct["balance"] == pytest.approx(expected_balance)

    def test_close_nonexistent(self, sid) -> None:
        result = storage.close_position(sid, 99999, 1.0, "MANUAL")
        assert result is None

    def test_invalid_exit_reason(self, sid) -> None:
        tid = storage.open_position(sid, "EUR_USD", "BUY", 0.1, 1.08)
        with pytest.raises(ValueError, match="exit_reason"):
            storage.close_position(sid, tid, 1.09, "INVALID")

    def test_update_position_prices(self, sid) -> None:
        tid = storage.open_position(sid, "EUR_USD", "BUY", 1.0, 1.08500)
        storage.dispatch_tick_to_all_sessions("EUR_USD", 1.09000, 1.09010)

        pos = storage.get_open_positions(sid)
        assert pos[0]["current_price"] == 1.09000  # BUY → valued at bid


class TestAccountCalculations:
    def test_equity_reflects_floating_pnl(self, sid) -> None:
        tid = storage.open_position(sid, "EUR_USD", "BUY", 1.0, 1.08500)
        storage.dispatch_tick_to_all_sessions("EUR_USD", 1.09500, 1.09510)
        acct = storage.get_account(sid)
        expected_eq = config.STARTING_BALANCE + (1.09500 - 1.08500) * config.LOT_SIZE
        assert acct["equity"] == pytest.approx(expected_eq)


class TestTradeHistory:
    def test_get_trade_history(self, sid) -> None:
        assert storage.get_trade_history(sid) == []

        tid = storage.open_position(sid, "EUR_USD", "BUY", 0.1, 1.08)
        storage.close_position(sid, tid, 1.09, "MANUAL")

        history = storage.get_trade_history(sid)
        assert len(history) == 1
        assert history[0]["ticket_id"] == tid
