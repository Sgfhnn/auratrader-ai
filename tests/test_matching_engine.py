"""Tests for matching_engine.py — tick generation, SL/TP evaluation, friction."""

import matching_engine
import storage


class TestSpreadAndSlippage:
    def test_buy_execution_higher_than_raw(self) -> None:
        """BUY should execute above the raw price (spread + slippage)."""
        result = matching_engine.apply_spread_and_slippage(1.08500, "BUY")
        assert result > 1.08500

    def test_sell_execution_lower_than_raw(self) -> None:
        """SELL should execute below the raw price (spread + slippage)."""
        result = matching_engine.apply_spread_and_slippage(1.08500, "SELL")
        assert result < 1.08500


class TestTickDispatch:
    def test_dispatch_updates_prices(self) -> None:
        matching_engine._dispatch_tick("EUR_USD", 1.08500, 1.08510)
        prices = matching_engine.get_latest_prices()
        assert "EUR_USD" in prices
        assert prices["EUR_USD"]["bid"] == 1.08500
        assert prices["EUR_USD"]["ask"] == 1.08510

    def test_dispatch_stores_history(self) -> None:
        matching_engine._dispatch_tick("EUR_USD", 1.08500, 1.08510)
        hist = matching_engine.get_price_history("EUR_USD")
        assert len(hist) >= 1
        assert hist[-1] == (1.08500 + 1.08510) / 2.0

    def test_dispatch_appends_tick_log(self) -> None:
        matching_engine._dispatch_tick("EUR_USD", 1.08500, 1.08510)
        log = matching_engine.get_tick_log("EUR_USD")
        assert len(log) >= 1


class TestMockTickGenerator:
    def test_next_mock_tick_returns_bid_ask(self) -> None:
        bid, ask = matching_engine._next_mock_tick("EUR_USD")
        assert isinstance(bid, float)
        assert isinstance(ask, float)
        assert bid < ask  # bid should always be lower than ask
        assert bid > 0
        assert ask > 0


class TestStopLossTakeProfit:
    def test_buy_stop_loss_hit(self, sid) -> None:
        """BUY position closes when bid hits SL."""
        storage.open_position(
            sid, "EUR_USD", "BUY", 1.0, 1.08500,
            stop_loss=1.08000, take_profit=1.09500,
        )
        # Tick below SL → should trigger close
        matching_engine._dispatch_tick("EUR_USD", 1.07950, 1.07960)
        assert len(storage.get_open_positions(sid)) == 0

        history = storage.get_trade_history(sid)
        assert history[0]["exit_reason"] == "SL"

    def test_buy_take_profit_hit(self, sid) -> None:
        """BUY position closes when bid hits TP."""
        storage.open_position(
            sid, "EUR_USD", "BUY", 1.0, 1.08500,
            stop_loss=1.08000, take_profit=1.09500,
        )
        matching_engine._dispatch_tick("EUR_USD", 1.09550, 1.09560)
        assert len(storage.get_open_positions(sid)) == 0

        history = storage.get_trade_history(sid)
        assert history[0]["exit_reason"] == "TP"

    def test_sell_stop_loss_hit(self, sid) -> None:
        """SELL position closes when ask hits SL."""
        storage.open_position(
            sid, "EUR_USD", "SELL", 1.0, 1.08500,
            stop_loss=1.09000, take_profit=1.07500,
        )
        matching_engine._dispatch_tick("EUR_USD", 1.09050, 1.09060)
        assert len(storage.get_open_positions(sid)) == 0

        history = storage.get_trade_history(sid)
        assert history[0]["exit_reason"] == "SL"

    def test_sell_take_profit_hit(self, sid) -> None:
        """SELL position closes when ask hits TP."""
        storage.open_position(
            sid, "EUR_USD", "SELL", 1.0, 1.08500,
            stop_loss=1.09000, take_profit=1.07500,
        )
        matching_engine._dispatch_tick("EUR_USD", 1.07450, 1.07460)
        assert len(storage.get_open_positions(sid)) == 0

        history = storage.get_trade_history(sid)
        assert history[0]["exit_reason"] == "TP"

    def test_unaffected_position_not_closed(self, sid) -> None:
        """Tick for one instrument should not close another instrument's position."""
        storage.open_position(
            sid, "GBP_USD", "BUY", 1.0, 1.27000,
            stop_loss=1.26000, take_profit=1.28000,
        )
        matching_engine._dispatch_tick("EUR_USD", 0.50000, 0.50010)
        assert len(storage.get_open_positions(sid)) == 1


class TestDataAccessors:
    def test_get_data_source(self) -> None:
        src = matching_engine.get_data_source()
        assert isinstance(src, str)

    def test_subscribe_unsubscribe(self) -> None:
        calls = []

        def cb(inst: str, bid: float, ask: float) -> None:
            calls.append((inst, bid, ask))

        matching_engine.subscribe(cb)
        matching_engine._dispatch_tick("EUR_USD", 1.0, 1.1)
        assert len(calls) == 1

        matching_engine.unsubscribe(cb)
        matching_engine._dispatch_tick("EUR_USD", 1.0, 1.1)
        assert len(calls) == 1  # no new call
