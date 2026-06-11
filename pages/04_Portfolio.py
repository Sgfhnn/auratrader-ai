from __future__ import annotations

import io

import pandas as pd
import streamlit as st

import config
import matching_engine
import storage
from components.theme import inject_theme
from components.layout import render_sidebar, render_page_header, render_metric_row
from utils.session import ensure_initialized


def _sid() -> str:
    return st.session_state.get("session_id", "")

inject_theme()
render_sidebar()
ensure_initialized()
render_page_header("Portfolio", "Open positions, trade history & risk overview")


# ───────────────────────────────────────────────────────────────────────────────
# OPEN POSITIONS
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Open Positions</div>', unsafe_allow_html=True)


@st.fragment(run_every=2)
def live_positions() -> None:
    positions = storage.get_open_positions(_sid())
    prices_latest = matching_engine.get_latest_prices()

    if not positions:
        st.info("No open positions.")
        return

    pos_df = pd.DataFrame(positions)
    pos_df["floating_pnl"] = pos_df.apply(
        lambda r: (
            (r["current_price"] - r["entry_price"]) * r["volume_lots"] * config.LOT_SIZE
            if r["direction"] == "BUY"
            else (r["entry_price"] - r["current_price"]) * r["volume_lots"] * config.LOT_SIZE
        ), axis=1,
    )

    display_cols = ["ticket_id", "instrument", "direction", "volume_lots",
                    "entry_price", "current_price", "stop_loss", "take_profit", "floating_pnl"]
    pos_df = pos_df[[c for c in display_cols if c in pos_df.columns]]
    pos_df.columns = [c.replace("_", " ").title() for c in pos_df.columns]

    st.dataframe(pos_df, width="stretch", hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    for pos in positions:
        tid = pos["ticket_id"]
        cf_flag = f"pcf_{tid}"
        c1, c2 = st.columns([0.12, 0.88])
        with c1:
            st.markdown(f'<span style="font-size:0.78rem;font-family:var(--mono);color:var(--text-muted);">#{tid}</span>', unsafe_allow_html=True)
        with c2:
            if st.session_state.get(cf_flag, False):
                cc1, cc2 = st.columns([1, 1])
                if cc1.button("✓ Confirm", key=f"pdoc_{tid}", type="primary"):
                    lp = prices_latest.get(pos["instrument"], {})
                    exit_p = lp.get("bid" if pos["direction"] == "BUY" else "ask", pos["current_price"])
                    storage.close_position(_sid(), tid, exit_p, "MANUAL")
                    st.session_state[cf_flag] = False
                    st.success(f"Position #{tid} closed.")
                    st.rerun()
                if cc2.button("✕ Cancel", key=f"pnoc_{tid}"):
                    st.session_state[cf_flag] = False
                    st.rerun()
            else:
                if st.button("✕ Close", key=f"pclo_{tid}"):
                    st.session_state[cf_flag] = True
                    st.rerun()


live_positions()

st.markdown("<hr>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# TRADE HISTORY
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📚 Trade History</div>', unsafe_allow_html=True)


@st.fragment(run_every=5)
def live_history() -> None:
    history = storage.get_trade_history(_sid())

    if not history:
        st.info("No closed trades yet.")
        return

    hdf = pd.DataFrame(history)
    hdf.columns = [c.replace("_", " ").title() for c in hdf.columns]
    st.dataframe(hdf, width="stretch", hide_index=True)

    # Summary stats
    total_pnl = float(hdf["Profit Loss"].sum())
    wins = int((hdf["Profit Loss"] > 0).sum())
    losses = int((hdf["Profit Loss"] <= 0).sum())
    wr = wins / (wins + losses) * 100 if (wins + losses) else 0
    best = float(hdf["Profit Loss"].max())
    worst = float(hdf["Profit Loss"].min())
    avg_win = float(hdf[hdf["Profit Loss"] > 0]["Profit Loss"].mean()) if wins else 0
    avg_loss = float(hdf[hdf["Profit Loss"] <= 0]["Profit Loss"].mean()) if losses else 0

    st.markdown("<br>", unsafe_allow_html=True)
    render_metric_row([
        {"label": "Total P&L", "value": f"${total_pnl:+,.2f}", "cls": "green" if total_pnl >= 0 else "red"},
        {"label": "Win Rate", "value": f"{wr:.1f}%", "cls": "green" if wr >= 50 else "red"},
        {"label": "Best Trade", "value": f"${best:+,.2f}", "cls": "green"},
        {"label": "Worst Trade", "value": f"${worst:+,.2f}", "cls": "red"},
        {"label": "Avg Win", "value": f"${avg_win:+,.2f}", "cls": "green"},
        {"label": "Avg Loss", "value": f"${avg_loss:+,.2f}", "cls": "red"},
    ])


live_history()

# ── CSV export ────────────────────────────────────────────────────────
if storage.get_trade_history(_sid()):
    all_trades = pd.DataFrame(storage.get_trade_history(_sid()))
    all_trades.columns = [c.replace("_", " ").title() for c in all_trades.columns]
    buf = io.StringIO()
    all_trades.to_csv(buf, index=False)
    st.download_button(
        "📥 Download Trade History (CSV)",
        data=buf.getvalue(),
        file_name="aura_trader_history.csv",
        mime="text/csv",
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# RISK OVERVIEW
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">⚠️ Risk Overview</div>', unsafe_allow_html=True)

acct = storage.get_account(_sid())
bal = acct.get("balance", 0.0)
eq = acct.get("equity", 0.0)
um = acct.get("used_margin", 0.0)
fm = acct.get("free_margin", 0.0)

margin_level = (eq / um * 100) if um > 0 else float("inf")
positions = storage.get_open_positions(_sid())
total_risk = 0.0
for pos in positions:
    if pos["stop_loss"] > 0:
        risk_per_lot = abs(pos["entry_price"] - pos["stop_loss"]) * config.LOT_SIZE
        total_risk += risk_per_lot * pos["volume_lots"]
risk_pct = (total_risk / bal * 100) if bal > 0 and total_risk > 0 else 0.0

render_metric_row([
    {"label": "Account Balance", "value": f"${bal:,.2f}"},
    {"label": "Used Margin", "value": f"${um:,.2f}", "cls": "accent"},
    {"label": "Free Margin", "value": f"${fm:,.2f}", "cls": "green" if fm > 0 else "red"},
    {"label": "Margin Level", "value": f"{margin_level:.1f}%" if margin_level != float("inf") else "∞",
     "cls": "green" if margin_level > 200 else ("red" if margin_level < 100 else "amber")},
    {"label": "Risk at Stake", "value": f"${total_risk:,.2f}", "cls": "red" if total_risk > 0 else ""},
    {"label": "Risk / Balance", "value": f"{risk_pct:.2f}%", "cls": "red" if risk_pct > 5 else ("green" if risk_pct < 2 else "amber")},
])
