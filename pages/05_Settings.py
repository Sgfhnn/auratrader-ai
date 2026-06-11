from __future__ import annotations

import streamlit as st

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
render_page_header("Settings", "Platform configuration & account management")

# ───────────────────────────────────────────────────────────────────────────────
# ACCOUNT
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">💰 Virtual Account</div>', unsafe_allow_html=True)

acct = storage.get_account(_sid())
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f'<div class="metric-card"><div class="label">Account ID</div>'
        f'<div class="value accent">#{acct.get("account_id", 1)}</div></div>',
        unsafe_allow_html=True,
    )
with c2:
    init_bal = st.session_state.get("starting_balance", config.STARTING_BALANCE)
    st.markdown(
        f'<div class="metric-card"><div class="label">Initial Balance</div>'
        f'<div class="value">${init_bal:,.2f}</div></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="metric-card"><div class="label">Current Balance</div>'
        f'<div class="value">${acct.get("balance", 0):,.2f}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄 Reset Account", type="primary", width="content"):
    sid = st.session_state.get("session_id")
    if sid:
        storage.remove_session(sid)
    for k in ["session_id", "session_store", "session_start", "db_init",
              "engine_started", "equity_history", "pending_trade",
              "sentiment_cache", "auto_log", "last_trade", "auto_active"]:
        st.session_state.pop(k, None)
    st.success("Account reset. Return to Home to start a new simulation.")
    st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# DATA SOURCE
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📡 Data Source</div>', unsafe_allow_html=True)

data_src = matching_engine.get_data_source()
st.markdown(
    f'<div class="panel" style="display:flex;align-items:center;justify-content:space-between;">'
    f'<div><div style="font-size:0.85rem;font-weight:600;">Current Feed</div>'
    f'<div style="font-size:0.75rem;color:var(--text-muted);">{data_src}</div></div>'
    f'<span class="badge badge-blue">AUTO</span></div>',
    unsafe_allow_html=True,
)



st.markdown("<hr>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# TRADING PARAMETERS
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">⚙️ Trading Parameters</div>', unsafe_allow_html=True)

params = [
    ("Starting Balance", f"${st.session_state.get('starting_balance', config.STARTING_BALANCE):,.2f}", "Virtual account initial capital"),
    ("Spread", f"{config.DEFAULT_SPREAD_PIPS} pips", "Spread added to every execution"),
    ("Max Slippage", f"{config.MAX_SLIPPAGE_PIPS} pips", "Random slippage range per trade"),
    ("Margin Rate", f"{config.MARGIN_RATE:.0%}", "Margin requirement (50:1 leverage)"),
    ("Lot Size", f"{config.LOT_SIZE:,} units", "Standard lot contract size"),
    ("Pip Size", f"{config.PIP_SIZE}", "Minimum price movement"),
    ("Tick Interval", f"{config.TICK_INTERVAL_SECONDS}s", "Time between mock ticks"),
    ("SMA Fast Period", f"{config.SMA_FAST_PERIOD} ticks", "Autonomous fast MA window"),
    ("SMA Slow Period", f"{config.SMA_SLOW_PERIOD} ticks", "Autonomous slow MA window"),
    ("Auto SL Distance", f"{config.AUTO_SL_PIPS} pips", "Default stop-loss for auto trades"),
    ("Auto TP Distance", f"{config.AUTO_TP_PIPS} pips", "Default take-profit for auto trades"),
]

for label, value, desc in params:
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:0.5rem 0;border-bottom:1px solid rgba(30,58,95,0.3);">'
        f'<div><span style="font-size:0.82rem;color:var(--text-primary);">{label}</span>'
        f'<br><span style="font-size:0.7rem;color:var(--text-muted);">{desc}</span></div>'
        f'<span style="font-family:var(--mono);font-size:0.85rem;color:var(--accent-hover);">{value}</span></div>',
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# INSTRUMENTS
# ───────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Tradable Instruments</div>', unsafe_allow_html=True)

for inst in config.INSTRUMENTS:
    display = inst.replace("_", "/")
    lp = matching_engine.get_latest_prices().get(inst, {})
    bid = lp.get("bid", 0.0)
    ask = lp.get("ask", 0.0)
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:0.4rem 0.75rem;background:var(--bg-card);border-radius:var(--radius-sm);'
        f'margin:0.2rem 0;border:1px solid var(--border);">'
        f'<span style="font-weight:600;font-size:0.85rem;">{display}</span>'
        f'<span style="font-family:var(--mono);font-size:0.8rem;color:var(--text-secondary);">'
        f'Bid {bid:.5f} &nbsp;·&nbsp; Ask {ask:.5f}</span></div>',
        unsafe_allow_html=True,
    )
