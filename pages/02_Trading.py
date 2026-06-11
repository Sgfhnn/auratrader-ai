from __future__ import annotations

import streamlit as st

import ai_agents
import config
import matching_engine
import storage
from components.theme import inject_theme
from components.layout import render_sidebar, render_page_header
from utils.session import ensure_initialized


def _sid() -> str:
    return st.session_state.get("session_id", "")

inject_theme()
render_sidebar()
ensure_initialized()
render_page_header("Trading", "Manual · Co-Pilot · Autonomous")

# ───────────────────────────────────────────────────────────────────────────────
# Three trading modes
# ───────────────────────────────────────────────────────────────────────────────
tab_manual, tab_copilot, tab_auto = st.tabs(["🖱️ Manual", "💬 Co-Pilot", "🤖 Autonomous"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MANUAL TRADE ENTRY
# ═══════════════════════════════════════════════════════════════════════════════
with tab_manual:
    prices_latest = matching_engine.get_latest_prices()

    # ── Execution form ──────────────────────────────────────────────────
    col_form, col_status = st.columns([1, 1])

    with col_form:
        st.markdown('<div class="panel"><div class="panel-title">✍️ Place Trade</div>', unsafe_allow_html=True)

        c_inst, c_dir = st.columns(2)
        with c_inst:
            instrument = st.selectbox("Instrument", config.INSTRUMENTS, index=0, key="manual_inst")
        with c_dir:
            direction = st.selectbox("Direction", ["BUY", "SELL"], index=0, key="manual_dir")

        c_vol, c_sl, c_tp = st.columns(3)
        with c_vol:
            volume = st.number_input("Lots", min_value=0.01, max_value=100.0, value=0.1, step=0.01, key="manual_vol")
        with c_sl:
            stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.0, step=0.0001, format="%.5f", key="manual_sl")
        with c_tp:
            take_profit = st.number_input("Take Profit", min_value=0.0, value=0.0, step=0.0001, format="%.5f", key="manual_tp")

        lp = prices_latest.get(instrument, {})
        bid = lp.get("bid", 0.0)
        ask = lp.get("ask", 0.0)
        if bid and ask:
            st.markdown(
                f'<div style="display:flex;gap:1rem;font-size:0.78rem;color:var(--text-muted);margin:0.25rem 0 0.75rem;">'
                f'<span>Bid: <span style="font-family:var(--mono);color:var(--text-primary);">{bid:.5f}</span></span>'
                f'<span>Ask: <span style="font-family:var(--mono);color:var(--text-primary);">{ask:.5f}</span></span>'
                f'<span>Spread: <span style="font-family:var(--mono);color:var(--text-primary);">{(ask-bid):.5f}</span></span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if st.button("🚀 Execute BUY" if direction == "BUY" else "🚀 Execute SELL",
                     type="primary", width="stretch", key="manual_execute"):
            raw = lp.get("ask" if direction == "BUY" else "bid", 0.0)
            if not raw:
                st.error("No live price — wait for ticks.")
            else:
                ep = matching_engine.apply_spread_and_slippage(raw, direction)
                tk = storage.open_position(_sid(), instrument, direction, volume, ep, stop_loss, take_profit)
                st.session_state["last_trade"] = {
                    "ticket": tk, "instrument": instrument, "direction": direction,
                    "volume": volume, "entry": ep,
                }
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col_status:
        st.markdown('<div class="panel"><div class="panel-title">📊 Trade Summary</div>', unsafe_allow_html=True)

        # Show last executed trade confirmation
        last = st.session_state.get("last_trade")
        if last:
            st.markdown(
                f'<div style="background:var(--green-bg);border:1px solid var(--green-border);border-radius:var(--radius-sm);'
                f'padding:0.75rem 1rem;margin-bottom:1rem;">'
                f'<div style="font-size:0.7rem;color:var(--green);text-transform:uppercase;letter-spacing:0.08em;">Last Execution</div>'
                f'<div style="font-size:0.9rem;font-weight:700;color:var(--text-primary);font-family:var(--mono);">'
                f'#{last["ticket"]} {last["direction"]} {last["volume"]} {last["instrument"].replace("_","/")} @ {last["entry"]:.5f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        acct = storage.get_account(_sid())
        pos_ct = len(storage.get_open_positions(_sid()))
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:0.35rem 0;font-size:0.82rem;">'
            f'<span style="color:var(--text-muted);">Balance</span>'
            f'<span style="font-family:var(--mono);">${acct.get("balance",0):,.2f}</span></div>'
            f'<div style="display:flex;justify-content:space-between;padding:0.35rem 0;font-size:0.82rem;">'
            f'<span style="color:var(--text-muted);">Equity</span>'
            f'<span style="font-family:var(--mono);">${acct.get("equity",0):,.2f}</span></div>'
            f'<div style="display:flex;justify-content:space-between;padding:0.35rem 0;font-size:0.82rem;">'
            f'<span style="color:var(--text-muted);">Open Positions</span>'
            f'<span style="font-family:var(--mono);">{pos_ct}</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Open positions table ────────────────────────────────────────────
    st.markdown('<div class="section-header">📋 Open Positions</div>', unsafe_allow_html=True)

    @st.fragment(run_every=1)
    def manual_positions() -> None:
        sid = _sid()
        positions = storage.get_open_positions(sid)
        prices = matching_engine.get_latest_prices()
        if not positions:
            st.info("No open positions. Use the form above to place a trade.")
            return

        for pos in positions:
            pnl = (
                (pos["current_price"] - pos["entry_price"]) * pos["volume_lots"] * config.LOT_SIZE
                if pos["direction"] == "BUY"
                else (pos["entry_price"] - pos["current_price"]) * pos["volume_lots"] * config.LOT_SIZE
            )
            pnl_cls = "green" if pnl >= 0 else "red"
            pnl_sign = "+" if pnl >= 0 else ""
            tid = pos["ticket_id"]
            cf_flag = f"cf_{tid}"
            with st.container():
                cols = st.columns([2, 1.2, 1, 1.5, 0.8])
                cols[0].markdown(
                    f'<span style="font-weight:600;font-size:0.85rem;">{pos["instrument"].replace("_","/")}</span>'
                    f'<br><span style="font-size:0.7rem;color:var(--text-muted);">#{tid}</span>',
                    unsafe_allow_html=True,
                )
                cols[1].markdown(
                    f'<span class="badge {"badge-green" if pos["direction"]=="BUY" else "badge-red"}">{pos["direction"]}</span>',
                    unsafe_allow_html=True,
                )
                cols[2].markdown(
                    f'<span style="font-family:var(--mono);font-size:0.82rem;">{pos["volume_lots"]} lots</span>',
                    unsafe_allow_html=True,
                )
                cols[3].markdown(
                    f'<span style="font-family:var(--mono);font-size:0.82rem;color:var(--{pnl_cls});">'
                    f'{pnl_sign}${pnl:,.2f}</span>',
                    unsafe_allow_html=True,
                )
                if st.session_state.get(cf_flag, False):
                    ccols = cols[4].columns([1, 1], gap="small")
                    if ccols[0].button("✓", key=f"doc_{tid}", type="primary"):
                        lp = prices.get(pos["instrument"], {})
                        exit_p = lp.get("bid" if pos["direction"] == "BUY" else "ask", pos["current_price"])
                        storage.close_position(sid, tid, exit_p, "MANUAL")
                        st.session_state[cf_flag] = False
                        st.rerun()
                    if ccols[1].button("✕", key=f"noc_{tid}"):
                        st.session_state[cf_flag] = False
                        st.rerun()
                else:
                    if cols[4].button("✕", key=f"clo_{tid}"):
                        st.session_state[cf_flag] = True
                        st.rerun()
            st.markdown('<div style="height:1px;background:rgba(30,58,95,0.2);margin:0.15rem 0;"></div>',
                        unsafe_allow_html=True)

    manual_positions()

    # ── Recent closed trades ────────────────────────────────────────────
    st.markdown('<div class="section-header">🕐 Recent Closed Trades</div>', unsafe_allow_html=True)

    @st.fragment(run_every=3)
    def recent_closed() -> None:
        history = storage.get_trade_history(_sid())
        if not history:
            st.caption("No closed trades yet.")
            return
        for t in history[:5]:
            pnl = t["profit_loss"]
            pnl_cls = "green" if pnl >= 0 else "red"
            reason = t.get("exit_reason", "MANUAL")
            reason_badge = {
                "TP": '<span class="badge badge-green">TP</span>',
                "SL": '<span class="badge badge-red">SL</span>',
                "MANUAL": '<span class="badge badge-neutral">MANUAL</span>',
            }.get(reason, f'<span class="badge badge-neutral">{reason}</span>')
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:0.78rem;padding:0.3rem 0;'
                f'border-bottom:1px solid rgba(30,58,95,0.15);">'
                f'<span>#{t["ticket_id"]} {t["instrument"].replace("_","/")} '
                f'<span class="badge {"badge-green" if t["direction"]=="BUY" else "badge-red"}">{t["direction"]}</span>'
                f' {reason_badge}</span>'
                f'<span style="font-family:var(--mono);color:var(--{pnl_cls});">${pnl:+,.2f}</span></div>',
                unsafe_allow_html=True,
            )

    recent_closed()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CO-PILOT (AI-assisted)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_copilot:
    st.markdown(
        '<div class="mode-banner copilot">💬 Co-Pilot — describe a trade in plain English, review, then approve</div>',
        unsafe_allow_html=True,
    )

    col_form, col_preview = st.columns([1, 1])

    with col_form:
        st.markdown('<div class="panel"><div class="panel-title">✏️ Trade Instruction</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:0.75rem;">'
            'Agent A parses natural language into structured trade parameters.</p>',
            unsafe_allow_html=True,
        )

        with st.form(key="copilot_form", clear_on_submit=True):
            user_instruction = st.text_area(
                "Instruction",
                placeholder='e.g. "Buy 1 lot of EUR_USD, stop loss 1.0750, take profit 1.0950"',
                height=100,
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("🔍 Parse with AI", type="primary", width="stretch")

        if submitted and user_instruction.strip():
            with st.spinner("Agent A parsing…"):
                st.session_state["pending_trade"] = ai_agents.agent_a_parse_trade(user_instruction)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_preview:
        if st.session_state["pending_trade"]:
            trade = st.session_state["pending_trade"]
            st.markdown('<div class="panel">', unsafe_allow_html=True)

            if "error" in trade:
                st.error(f"Parsing error: {trade['error']}")
                st.code(trade.get("raw_response", ""), language="text")
            else:
                action = trade.get("action", "OPEN")
                is_close = action == "CLOSE_ALL"

                st.markdown('<div class="panel-title">📋 Parsed Parameters</div>', unsafe_allow_html=True)

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.markdown(
                        f'<div class="metric-card"><div class="label">Instrument</div>'
                        f'<div class="value accent">{trade.get("instrument", "—")}</div></div>',
                        unsafe_allow_html=True,
                    )
                with mc2:
                    st.markdown(
                        f'<div class="metric-card"><div class="label">Action</div>'
                        f'<div class="value {"red" if is_close else "green"}">{"CLOSE ALL" if is_close else "OPEN"}</div></div>',
                        unsafe_allow_html=True,
                    )
                with mc3:
                    if is_close:
                        positions = storage.get_open_positions(_sid())
                        ct = sum(1 for p in positions if p["instrument"] == trade.get("instrument", ""))
                        st.markdown(
                            f'<div class="metric-card"><div class="label">Open Positions</div>'
                            f'<div class="value">{ct}</div></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        d = trade.get("direction", "—")
                        st.markdown(
                            f'<div class="metric-card"><div class="label">Direction</div>'
                            f'<div class="value {"green" if d=="BUY" else "red"}">{d}</div></div>',
                            unsafe_allow_html=True,
                        )

                if not is_close:
                    info_lines = [
                        ("Volume", f'{trade.get("volume_lots", 0.1)} lots'),
                        ("Stop Loss", f'{trade.get("stop_loss", 0.0):.5f}' if trade.get("stop_loss") else "Not set"),
                        ("Take Profit", f'{trade.get("take_profit", 0.0):.5f}' if trade.get("take_profit") else "Not set"),
                    ]
                    for lbl, val in info_lines:
                        st.markdown(
                            f'<div style="display:flex;justify-content:space-between;padding:0.35rem 0;'
                            f'border-bottom:1px solid rgba(30,58,95,0.3);font-size:0.8rem;">'
                            f'<span style="color:var(--text-muted);">{lbl}</span>'
                            f'<span style="color:var(--text-primary);font-family:var(--mono);">{val}</span></div>',
                            unsafe_allow_html=True,
                        )

                if trade.get("notes"):
                    st.markdown(
                        f'<div style="margin-top:0.5rem;font-size:0.78rem;color:var(--text-secondary);">'
                        f'📝 {trade["notes"]}</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                ap, rej = st.columns(2)
                with ap:
                    if is_close:
                        if st.button("🔴 Close All Positions", key="close_all_exec", type="primary", width="stretch"):
                            inst = trade.get("instrument", "EUR_USD")
                            if inst not in config.INSTRUMENTS:
                                st.error(f"Invalid instrument '{inst}'.")
                            else:
                                n = storage.close_all_positions(_sid(), inst)
                                st.success(f"Closed {n} position(s) for {inst.replace('_','/')}.")
                                st.session_state["pending_trade"] = None
                                st.rerun()
                    else:
                        if st.button("✅ Approve & Execute", key="approve_trade", type="primary", width="stretch"):
                            inst = trade.get("instrument", "EUR_USD")
                            dirn = str(trade.get("direction", "BUY")).upper().strip()
                            dirn = {"LONG": "BUY", "SHORT": "SELL"}.get(dirn, dirn)
                            vol = float(trade.get("volume_lots", 0.1))
                            sl = float(trade.get("stop_loss", 0.0))
                            tp = float(trade.get("take_profit", 0.0))

                            if inst not in config.INSTRUMENTS:
                                st.error(f"Invalid instrument '{inst}'.")
                            elif dirn not in ("BUY", "SELL"):
                                st.error(f"Direction must be BUY or SELL.")
                            elif vol <= 0 or vol > 100:
                                st.error(f"Volume must be 0.01–100 lots, got {vol}.")
                            else:
                                lp = matching_engine.get_latest_prices().get(inst, {})
                                raw = lp.get("ask" if dirn == "BUY" else "bid", 0.0)
                                if not raw:
                                    st.error("No live price yet.")
                                else:
                                    ep = matching_engine.apply_spread_and_slippage(raw, dirn)
                                    tk = storage.open_position(_sid(), inst, dirn, vol, ep, sl, tp)
                                    st.success(f"✅ Trade #{tk}: {dirn} {vol} lots {inst} @ {ep:.5f}")
                                    st.session_state["pending_trade"] = None
                                    st.rerun()
                with rej:
                    if st.button("❌ Reject", key="reject_trade", width="stretch"):
                        st.session_state["pending_trade"] = None
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="panel" style="text-align:center;padding:2.5rem 1rem;">'
                '<div style="font-size:2rem;margin-bottom:0.5rem;">💬</div>'
                '<div style="color:var(--text-muted);font-size:0.85rem;">'
                'Enter a trade instruction on the left to see parsed parameters here.</div></div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AUTONOMOUS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_auto:
    st.markdown(
        '<div class="mode-banner autonomous">⚡ Autonomous Engine — trades execute automatically when SMA + Sentiment align</div>',
        unsafe_allow_html=True,
    )

    col_sentiment, col_signal = st.columns([1, 1])

    with col_sentiment:
        st.markdown('<div class="panel"><div class="panel-title">📰 Market Sentiment</div>', unsafe_allow_html=True)
        sc = st.session_state["sentiment_cache"]
        sentiment = sc.get("sentiment", "NEUTRAL")
        s_cls = {"BULLISH": "bullish", "BEARISH": "bearish"}.get(sentiment, "neutral")
        emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "⚪"}

        r1, r2 = st.columns([2, 1])
        with r1:
            st.markdown(
                f'<span class="sentiment-chip sentiment-{s_cls}">{emoji.get(sentiment, "⚪")} {sentiment}</span>',
                unsafe_allow_html=True,
            )
        with r2:
            if st.button("🔄 Refresh", key="refresh_sentiment", width="stretch"):
                with st.spinner("Agent B scanning news…"):
                    st.session_state["sentiment_cache"] = ai_agents.agent_b_market_sentiment()
                st.rerun()

        if sc.get("headlines"):
            with st.expander("📰 View Headlines"):
                st.text(sc["headlines"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col_signal:
        st.markdown('<div class="panel"><div class="panel-title">📈 SMA Crossover</div>', unsafe_allow_html=True)

        @st.fragment(run_every=2)
        def signal_display() -> None:
            price_hist = matching_engine.get_price_history("EUR_USD")
            if len(price_hist) < config.SMA_SLOW_PERIOD:
                st.info(f"⏳ Collecting data ({len(price_hist)}/{config.SMA_SLOW_PERIOD} ticks)")
                return

            fast = sum(price_hist[-config.SMA_FAST_PERIOD:]) / config.SMA_FAST_PERIOD
            slow = sum(price_hist[-config.SMA_SLOW_PERIOD:]) / config.SMA_SLOW_PERIOD
            crossover = "BUY" if fast > slow else "SELL"
            c_cls = "bullish" if crossover == "BUY" else "bearish"
            st.markdown(
                f'<span class="sentiment-chip sentiment-{c_cls}">{"🟢" if crossover=="BUY" else "🔴"} {crossover}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="margin-top:0.5rem;font-size:0.72rem;color:var(--text-muted);">'
                f'SMA({config.SMA_FAST_PERIOD}): {fast:.5f} &nbsp;·&nbsp; SMA({config.SMA_SLOW_PERIOD}): {slow:.5f}</div>',
                unsafe_allow_html=True,
            )

        signal_display()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="panel-title">🤖 Auto-Trade Engine</div>', unsafe_allow_html=True)

    auto_active = st.checkbox("Enable auto-trading", value=st.session_state.get("auto_active", False),
                              key="auto_active")

    st.caption("When enabled, trades execute automatically every 2 seconds when SMA + Sentiment align. "
               "Disable when using Manual or Co-Pilot tabs to prevent unexpected trades.")

    @st.fragment(run_every=60)
    def auto_refresh_sentiment() -> None:
        if st.session_state.get("auto_active", False):
            st.session_state["sentiment_cache"] = ai_agents.agent_b_market_sentiment()
            st.rerun()

    auto_refresh_sentiment()

    @st.fragment(run_every=2)
    def live_autonomous_panel() -> None:
        if not st.session_state.get("auto_active", False):
            st.info("⏸ Auto-trading is paused. Toggle 'Enable auto-trading' above to start.")
            return

        prices = matching_engine.get_latest_prices()
        positions = storage.get_open_positions(_sid())
        price_hist = matching_engine.get_price_history("EUR_USD")
        sc2 = st.session_state["sentiment_cache"]
        sentiment2 = sc2.get("sentiment", "NEUTRAL")

        crossover_signal = None
        if len(price_hist) >= config.SMA_SLOW_PERIOD:
            fast = sum(price_hist[-config.SMA_FAST_PERIOD:]) / config.SMA_FAST_PERIOD
            slow = sum(price_hist[-config.SMA_SLOW_PERIOD:]) / config.SMA_SLOW_PERIOD
            crossover_signal = "BUY" if fast > slow else "SELL"
            st.markdown(
                f'<div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:0.5rem;">'
                f'SMA{config.SMA_FAST_PERIOD} {"›" if fast > slow else "‹"} SMA{config.SMA_SLOW_PERIOD} → {crossover_signal}</div>',
                unsafe_allow_html=True,
            )

        should_trade = (
            (crossover_signal == "BUY" and sentiment2 == "BULLISH") or
            (crossover_signal == "SELL" and sentiment2 == "BEARISH")
        )

        if should_trade and crossover_signal:
            inst = "EUR_USD"
            lp = prices.get(inst, {})
            raw = lp.get("ask" if crossover_signal == "BUY" else "bid", 0.0)
            if raw and not any(p["instrument"] == inst for p in positions):
                ep = matching_engine.apply_spread_and_slippage(raw, crossover_signal)
                pip = config.PIP_SIZE
                sl = ep - config.AUTO_SL_PIPS * pip if crossover_signal == "BUY" else ep + config.AUTO_SL_PIPS * pip
                tp = ep + config.AUTO_TP_PIPS * pip if crossover_signal == "BUY" else ep - config.AUTO_TP_PIPS * pip
                tk = storage.open_position(_sid(), inst, crossover_signal, 0.1, ep, round(sl, 5), round(tp, 5))
                log = f"[AUTO] {crossover_signal} 0.1 {inst} @ {ep:.5f} | SL {sl:.5f} | TP {tp:.5f} | #{tk}"
                st.session_state["auto_log"].insert(0, log)
                st.success(f"🤖 {log}")
        else:
            details = []
            if crossover_signal:
                details.append(f"SMA: {crossover_signal}")
            else:
                details.append("SMA: N/A (insufficient data)")
            details.append(f"Sentiment: {sentiment2}")
            st.info(f"⏸ Waiting for alignment — {' · '.join(details)}")

    live_autonomous_panel()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["auto_log"]:
        st.markdown(
            '<div style="margin-top:1rem;font-size:0.82rem;font-weight:600;color:var(--text-secondary);">'
            '📜 Auto Trade Log</div>',
            unsafe_allow_html=True,
        )
        for entry in st.session_state["auto_log"][:15]:
            st.markdown(f'<div class="trade-log-entry">{entry}</div>', unsafe_allow_html=True)
