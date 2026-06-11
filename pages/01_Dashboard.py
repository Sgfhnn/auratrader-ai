from __future__ import annotations

import logging
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_agents
import config
import matching_engine
import storage
from components.theme import inject_theme
from components.layout import render_sidebar
from utils.session import ensure_initialized


def _sid() -> str:
    return st.session_state.get("session_id", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AuraTrader AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

inject_theme()
render_sidebar()
ensure_initialized()


_PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["toImage", "fullscreen"],
    "responsive": True,
}


# ── ACCOUNT HEADER BAR ─────────────────────────────────────────────────
@st.fragment(run_every=1)
def account_header() -> None:
    sid = _sid()
    acct = storage.get_account(sid)
    bal = acct.get("balance", 0.0)
    eq = acct.get("equity", 0.0)
    um = acct.get("used_margin", 0.0)
    fpnl = eq - bal
    open_pos = len(storage.get_open_positions(sid))
    hist = storage.get_trade_history(sid)

    st.session_state["equity_history"].append({"t": time.strftime("%H:%M:%S"), "equity": eq, "balance": bal})

    pnl_cls = "green" if fpnl >= 0 else "red"
    pnl_sgn = "+" if fpnl >= 0 else ""
    mrg_lvl = (eq / um * 100) if um > 0 else float("inf")
    mrg_str = f"{mrg_lvl:.1f}%" if mrg_lvl != float("inf") else "∞"
    mrg_cls = "green" if mrg_lvl > 200 else ("red" if mrg_lvl < 100 else "amber")

    st.markdown(
        f'<div class="header-bar">'
        f'<div class="header-item"><span class="header-label">Balance</span><span class="header-value">${bal:,.2f}</span></div>'
        f'<div class="header-divider"></div>'
        f'<div class="header-item"><span class="header-label">Equity</span><span class="header-value {"green" if eq >= bal else "red"}">${eq:,.2f}</span></div>'
        f'<div class="header-divider"></div>'
        f'<div class="header-item"><span class="header-label">Floating P&L</span><span class="header-value {pnl_cls}">{pnl_sgn}${fpnl:,.2f}</span></div>'
        f'<div class="header-divider"></div>'
        f'<div class="header-item"><span class="header-label">Margin Level</span><span class="header-value {mrg_cls}">{mrg_str}</span></div>'
        f'<div class="header-divider"></div>'
        f'<div class="header-item"><span class="header-label">Open</span><span class="header-value">{open_pos}</span></div>'
        f'<div class="header-divider"></div>'
        f'<div class="header-item"><span class="header-label">Closed</span><span class="header-value">{len(hist)}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


account_header()

st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)


# ── MAIN LAYOUT: CHART + MARKET WATCH ────────────────────────────────
col_right, col_left = st.columns([2.2, 1])


# ── RIGHT COLUMN: PRICE CHART ─────────────────────────────────────────
with col_right:
    st.markdown('<div class="panel" style="padding:1rem;">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([0.4, 0.2, 0.2, 0.2])
    with c1:
        inst_keys = {i.replace("_", "/"): i for i in config.INSTRUMENTS}
        sel_label = st.selectbox("", list(inst_keys.keys()), index=0, key="dash_inst_label", label_visibility="collapsed")
        sel = inst_keys[sel_label]
    with c2:
        expand = st.checkbox("Expand", key="expand_chart")
    with c3:
        candle = st.checkbox("Candle", key="candlestick_chart")
    with c4:
        st.markdown("<div style='padding-top:0.15rem;'>", unsafe_allow_html=True)
        if st.button("⚡ DEC", key="qt_dec", help="Decrease volume"):
            prev = st.session_state.get("qt_vol", 0.1)
            st.session_state["qt_vol"] = max(0.01, round(prev - 0.01, 2))
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    @st.fragment(run_every=2)
    def live_price_chart() -> None:
        sel_local = st.session_state.get("dash_inst_label", "EUR/USD")
        sel_code = inst_keys.get(sel_local, "EUR_USD")
        ticks = matching_engine.get_tick_log(sel_code)
        lp = matching_engine.get_latest_prices().get(sel_code, {})
        bid = lp.get("bid", 0.0)
        ask = lp.get("ask", 0.0)
        mid = (bid + ask) / 2.0 if bid and ask else 0.0

        ch = st.session_state.get("expand_chart", False)
        is_candle = st.session_state.get("candlestick_chart", False)
        height = 440 if ch else 320

        if mid:
            prev_hist = matching_engine.get_price_history(sel_code)
            if len(prev_hist) >= 2:
                chg = prev_hist[-1] - prev_hist[-2]
                chg_p = (chg / prev_hist[-2]) * 100 if prev_hist[-2] else 0
                color = "#22c55e" if chg >= 0 else "#ef4444"
                arrow = "▲" if chg >= 0 else "▼"
            else:
                chg, chg_p, color, arrow = 0, 0, "#8899b4", "–"

            st.markdown(
                f'<div style="display:flex;align-items:baseline;gap:10px;margin-bottom:4px;">'
                f'<span style="font-size:1.3rem;font-weight:700;letter-spacing:-0.02em;">{mid:.5f}</span>'
                f'<span style="color:{color};font-weight:600;font-family:var(--mono);font-size:0.82rem;">{arrow} {chg:+.5f} ({chg_p:+.3f}%)</span>'
                f'<span style="color:var(--text-muted);font-size:0.7rem;">Bid {bid:.5f} / Ask {ask:.5f} &nbsp;·&nbsp; Spread {(ask-bid)*10000:.1f} pip</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if len(ticks) >= 2:
            df = pd.DataFrame(ticks)
            fig = go.Figure()

            if is_candle:
                df["t_sec"] = df["time"].astype("datetime64[ns]")
                ohlc = df.resample("3s", on="t_sec")["mid"].ohlc().dropna()
                if len(ohlc) >= 2:
                    fig.add_trace(go.Candlestick(
                        x=ohlc.index, open=ohlc["open"], high=ohlc["high"],
                        low=ohlc["low"], close=ohlc["close"],
                        increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
                        showlegend=False,
                    ))
                else:
                    is_candle = False

            if not is_candle:
                df["diff"] = df["mid"].diff()
                df["up"] = df["diff"] >= 0
                df["group"] = (df["up"] != df["up"].shift()).cumsum()
                for _, grp in df.groupby("group"):
                    c = "#22c55e" if grp["up"].iloc[0] else "#ef4444"
                    fig.add_trace(go.Scatter(
                        x=grp["time"], y=grp["mid"], mode="lines",
                        line=dict(color=c, width=2), showlegend=False,
                        hovertemplate="%{y:.5f}<extra></extra>", connectgaps=False,
                    ))
                last = df.iloc[-1]
                fig.add_trace(go.Scatter(
                    x=[last["time"]], y=[last["mid"]], mode="markers",
                    marker=dict(color="#22c55e" if last["up"] else "#ef4444", size=7,
                                line=dict(color="#0d1421", width=2)),
                    showlegend=False, hoverinfo="skip",
                ))

            fig.update_layout(
                height=height, xaxis_rangeslider_visible=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,33,0.6)",
                font=dict(color="#8899b4", family="Inter", size=11),
                xaxis=dict(gridcolor="rgba(59,130,246,0.06)", zerolinecolor="rgba(59,130,246,0.1)",
                           spikecolor="rgba(59,130,246,0.2)", spikesnap="cursor", spikemode="across",
                           showspikes=True, spikethickness=1),
                yaxis=dict(gridcolor="rgba(59,130,246,0.06)", zerolinecolor="rgba(59,130,246,0.1)",
                           spikecolor="rgba(59,130,246,0.2)", spikesnap="cursor", spikemode="across",
                           showspikes=True, spikethickness=1),
                margin=dict(l=4, r=4, t=4, b=4), uirevision="lock", hovermode="x unified",
            )
            st.plotly_chart(fig, width="stretch", key=f"dash_price_{sel_code}", config=_PLOTLY_CONFIG)
        else:
            st.info("⏳ Collecting ticks…", icon="⏳")

    live_price_chart()

    # ── Quick Trade (inline) ──
    st.markdown('<div style="margin-top:0.5rem;">', unsafe_allow_html=True)
    qt_inst_code = inst_keys.get(st.session_state.get("dash_inst_label", "EUR/USD"), "EUR_USD")
    qt_prices = matching_engine.get_latest_prices().get(qt_inst_code, {})
    qt_bid = qt_prices.get("bid", 0)
    qt_ask = qt_prices.get("ask", 0)
    qt_vol = st.session_state.get("qt_vol", 0.1)
    qc1, qc2, qc3, qc4, qc5 = st.columns([0.15, 0.6, 0.3, 0.3, 0.3])
    with qc1:
        st.markdown(f'<span style="font-size:0.8rem;color:var(--text-muted);font-family:var(--mono);">x{qt_vol}</span>', unsafe_allow_html=True)
    with qc2:
        st.slider("", 0.01, 1.0, qt_vol, 0.01, key="qt_vol_slider", label_visibility="collapsed", format="%.2f")
    with qc3:
        if st.button("BUY", key="qt_buy_btn", type="primary", width="stretch"):
            raw = qt_ask or matching_engine.get_latest_prices().get(qt_inst_code, {}).get("ask", 0)
            if raw:
                vol = st.session_state.get("qt_vol_slider", 0.1)
                ep = matching_engine.apply_spread_and_slippage(raw, "BUY")
                tk = storage.open_position(_sid(), qt_inst_code, "BUY", vol, ep, 0, 0)
                st.session_state["last_trade"] = {"ticket": tk, "instrument": qt_inst_code, "direction": "BUY", "volume": vol, "entry": ep}
                st.rerun()
    with qc4:
        if st.button("SELL", key="qt_sell_btn", type="primary", width="stretch"):
            raw = qt_bid or matching_engine.get_latest_prices().get(qt_inst_code, {}).get("bid", 0)
            if raw:
                vol = st.session_state.get("qt_vol_slider", 0.1)
                ep = matching_engine.apply_spread_and_slippage(raw, "SELL")
                tk = storage.open_position(_sid(), qt_inst_code, "SELL", vol, ep, 0, 0)
                st.session_state["last_trade"] = {"ticket": tk, "instrument": qt_inst_code, "direction": "SELL", "volume": vol, "entry": ep}
                st.rerun()
    with qc5:
        pass

    last = st.session_state.get("last_trade")
    if last:
        st.markdown(
            f'<div style="background:var(--green-bg);border:1px solid var(--green-border);border-radius:var(--radius-sm);'
            f'padding:0.3rem 0.7rem;margin-top:0.2rem;font-size:0.75rem;font-family:var(--mono);color:var(--green);">'
            f'✅ #{last["ticket"]} {last["direction"]} {last["volume"]} {last["instrument"].replace("_","/")} @ {last["entry"]:.5f}</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── LEFT COLUMN: MARKET WATCH + SENTIMENT ─────────────────────────────
with col_left:
    st.markdown('<div class="panel" style="padding:1rem 0.75rem;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Market Watch</div>', unsafe_allow_html=True)

    @st.fragment(run_every=2)
    def market_watch() -> None:
        all_prices = matching_engine.get_latest_prices()
        rows_html = ""
        for inst in config.INSTRUMENTS:
            p = all_prices.get(inst, {})
            bid = p.get("bid", 0.0)
            ask = p.get("ask", 0.0)
            mid = (bid + ask) / 2.0 if bid and ask else 0.0
            h = matching_engine.get_price_history(inst)
            if len(h) >= 2:
                chg = h[-1] - h[-2]
                arrow = "▲" if chg >= 0 else "▼"
                chg_cls = "green" if chg >= 0 else "red"
                chg_str = f"{chg:+.5f}"
            else:
                arrow, chg_cls, chg_str = "–", "muted", "—"
            rows_html += (
                f'<div class="mw-row">'
                f'<span class="mw-pair">{inst.replace("_","/")}</span>'
                f'<span class="mw-bid">{bid:.5f}</span>'
                f'<span class="mw-change {chg_cls}">{arrow} {chg_str[:8]}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="mw-header"><span>Pair</span><span>Bid</span><span>Δ</span></div>'
            f'{rows_html}'
            f'<div class="mw-row" style="border:none;padding:0.35rem 0 0;font-size:0.65rem;color:var(--text-muted);">'
            f'Updated {time.strftime("%H:%M:%S")}</div>',
            unsafe_allow_html=True,
        )

    market_watch()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sentiment Widget ──
    st.markdown('<div class="panel" style="padding:0.75rem;margin-top:0.5rem;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Sentiment</div>', unsafe_allow_html=True)
    sc = st.session_state["sentiment_cache"]
    sentiment = sc.get("sentiment", "NEUTRAL")
    s_cls = {"BULLISH": "bullish", "BEARISH": "bearish"}.get(sentiment, "neutral")
    s_emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "⚪"}
    sr1, sr2 = st.columns([1.5, 1])
    with sr1:
        st.markdown(
            f'<span class="sentiment-chip sentiment-{s_cls}" style="font-size:0.78rem;">{s_emoji.get(sentiment, "⚪")} {sentiment}</span>',
            unsafe_allow_html=True,
        )
    with sr2:
        if st.button("↻", key="dash_refresh_sent", width="stretch"):
            with st.spinner(""):
                st.session_state["sentiment_cache"] = ai_agents.agent_b_market_sentiment()
            st.rerun()
    if sc.get("headlines"):
        with st.expander("Headlines"):
            st.caption(sc["headlines"])
    st.markdown('</div>', unsafe_allow_html=True)


# ── BOTTOM SECTION ──────────────────────────────────────────────────────
st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)

bcol1, bcol2 = st.columns([1.5, 1])


# ── BOTTOM LEFT: OPEN POSITIONS ─────────────────────────────────────────
with bcol1:
    st.markdown('<div class="panel" style="padding:0.75rem 1rem;">', unsafe_allow_html=True)
    st.markdown('<div class="section-header" style="margin:0 0 0.5rem;">📋 Open Positions</div>', unsafe_allow_html=True)

    @st.fragment(run_every=2)
    def open_positions() -> None:
        positions = storage.get_open_positions(_sid())
        prices = matching_engine.get_latest_prices()
        if not positions:
            st.caption("No open positions.")
            return

        for pos in positions:
            pnl = (
                (pos["current_price"] - pos["entry_price"]) * pos["volume_lots"] * config.LOT_SIZE
                if pos["direction"] == "BUY"
                else (pos["entry_price"] - pos["current_price"]) * pos["volume_lots"] * config.LOT_SIZE
            )
            pnl_cls = "green" if pnl >= 0 else "red"
            pnl_sgn = "+" if pnl >= 0 else ""
            st.markdown(
                f'<div class="op-row">'
                f'<span class="op-inst">{pos["instrument"].replace("_","/")}</span>'
                f'<span class="badge {"badge-green" if pos["direction"]=="BUY" else "badge-red"}">{pos["direction"]}</span>'
                f'<span class="op-vol">{pos["volume_lots"]} lot</span>'
                f'<span class="op-pnl {pnl_cls}">{pnl_sgn}${pnl:,.2f}</span>'
                f'<span class="op-entry">{pos["entry_price"]:.5f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    open_positions()
    st.markdown('</div>', unsafe_allow_html=True)


# ── BOTTOM RIGHT: STATS + EQUITY SPARKLINE ──────────────────────────────
with bcol2:
    st.markdown('<div class="panel" style="padding:0.75rem 1rem;">', unsafe_allow_html=True)

    @st.fragment(run_every=3)
    def equity_sparkline() -> None:
        eq_list = list(st.session_state["equity_history"])
        if len(eq_list) >= 2:
            eq_df = pd.DataFrame(eq_list)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=eq_df["t"], y=eq_df["equity"], mode="lines",
                line=dict(color="#3b82f6", width=1.5), fill="tozeroy",
                fillcolor="rgba(59,130,246,0.06)", showlegend=False,
                hovertemplate="%{y:$,.2f}<extra></extra>",
            ))
            fig.update_layout(
                height=100, margin=dict(l=0, r=0, t=2, b=2),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8899b4", size=10),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                hovermode="x unified",
            )
            st.plotly_chart(fig, width="stretch", key="eq_spark", config={"displayModeBar": False})

    equity_sparkline()

    sid = _sid()
    history = storage.get_trade_history(sid)
    total_pnl = float(pd.DataFrame(history)["profit_loss"].sum()) if history else 0
    wins = sum(1 for t in history if t["profit_loss"] > 0) if history else 0
    wr = wins / len(history) * 100 if history else 0

    acct = storage.get_account(sid)
    bal = acct.get("balance", 0.0)
    start = st.session_state.get("session_start", time.time())
    elapsed = time.time() - start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    sc1, sc2, sc3 = st.columns([1, 1, 1])
    with sc1:
        st.markdown(f'<div class="stat-micro"><span class="stat-label">P&L</span><span class="stat-value {"green" if total_pnl>=0 else "red"}">${total_pnl:+,.2f}</span></div>', unsafe_allow_html=True)
    with sc2:
        st.markdown(f'<div class="stat-micro"><span class="stat-label">Win Rate</span><span class="stat-value {"green" if wr>=50 else "red"}">{wr:.1f}%</span></div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div class="stat-micro"><span class="stat-label">Session</span><span class="stat-value">{mins}m {secs}s</span></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── RECENT ACTIVITY (full width) ─────────────────────────────────────────
st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
st.markdown('<div class="panel" style="padding:0.75rem 1rem;">', unsafe_allow_html=True)
st.markdown('<div class="section-header" style="margin:0 0 0.5rem;">🕐 Recent Activity</div>', unsafe_allow_html=True)

@st.fragment(run_every=5)
def recent_activity() -> None:
    history = storage.get_trade_history(_sid())
    if not history:
        st.caption("No closed trades yet.")
        return
    recent = history[:8]
    hdf = pd.DataFrame(recent)
    hdf.columns = [c.replace("_", " ").title() for c in hdf.columns]
    st.dataframe(hdf, width="stretch", hide_index=True, height=180)


recent_activity()
st.markdown('</div>', unsafe_allow_html=True)
