from __future__ import annotations

import streamlit as st

from components.theme import inject_theme

st.set_page_config(page_title="AuraTrader AI", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

inject_theme()

st.markdown(
    """
    <style>
      section[data-testid="stSidebar"] { display: none !important; }
      #MainMenu { visibility: hidden; }
      footer { visibility: hidden; }
      .stApp { background: #0b0f19; }
      .feature-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.4);
        border-radius: 10px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: border-color 0.2s;
      }
      .feature-card:hover { border-color: rgba(96, 165, 250, 0.4); }
      .feature-icon {
        width: 40px; height: 40px; border-radius: 8px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.1rem; margin-bottom: 0.75rem;
        background: rgba(96, 165, 250, 0.1);
      }
      .feature-title {
        font-size: 0.82rem; font-weight: 600; color: #e2e8f0;
        margin-bottom: 0.35rem; letter-spacing: 0.01em;
      }
      .feature-desc {
        font-size: 0.7rem; color: #64748b; line-height: 1.45;
      }
      .stat-label { font-size: 0.65rem; color: #475569; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.2rem; }
      .stat-value { font-size: 1.1rem; font-weight: 600; color: #e2e8f0; font-family: var(--mono); }
    </style>
    """,
    unsafe_allow_html=True,
)

has_session = "session_id" in st.session_state

# ── Header ────────────────────────────────────────────────────────────
st.markdown(
    '<div style="padding:4rem 0 0.5rem;text-align:center;">'
    '<div style="font-size:0.65rem;font-weight:500;color:#3b82f6;letter-spacing:0.12em;'
    'text-transform:uppercase;margin-bottom:0.75rem;">Trading Platform</div>'
    '<div style="font-size:2.2rem;font-weight:700;color:#f1f5f9;letter-spacing:-0.02em;">'
    'AuraTrader AI</div>'
    '<div style="width:32px;height:2px;background:#3b82f6;margin:1rem auto;border-radius:1px;"></div>'
    '<div style="font-size:0.82rem;color:#64748b;max-width:360px;margin:0 auto;line-height:1.5;">'
    'AI-driven forex simulation with real-time matching engine and autonomous strategy execution.</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Session or Balance Selector ───────────────────────────────────────
st.markdown('<div style="height:2.5rem;"></div>', unsafe_allow_html=True)

if has_session:
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">'
        'Active Session</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1.2, 1.6, 1.2])
    with c2:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Continue", type="primary", width="stretch", use_container_width=True):
                st.switch_page("pages/01_Dashboard.py")
        with b2:
            if st.button("New Session", width="stretch", use_container_width=True):
                import storage
                sid = st.session_state.get("session_id")
                if sid:
                    storage.remove_session(sid)
                for k in ["session_id", "session_store", "session_start", "db_init",
                          "engine_started", "equity_history", "pending_trade",
                          "sentiment_cache", "auto_log", "last_trade", "auto_active"]:
                    st.session_state.pop(k, None)
                st.rerun()
else:
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:1rem;">'
        'Initial Capital</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    presets = [1_000, 10_000, 50_000, 100_000, 1_000_000]
    preset_labels = ["$1K", "$10K", "$50K", "$100K", "$1M"]

    pcols = st.columns(len(presets))
    chosen = st.session_state.get("starting_balance", 10_000)
    for i, (val, label) in enumerate(zip(presets, preset_labels)):
        with pcols[i]:
            if st.button(label, key=f"preset_{i}",
                         type="primary" if chosen == val else "secondary",
                         width="stretch", use_container_width=True):
                st.session_state["starting_balance"] = val

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)

    def _sync_bal() -> None:
        st.session_state["starting_balance"] = st.session_state["custom_bal_input"]

    custom_bal = st.number_input(
        "Custom amount",
        min_value=1_000, max_value=1_000_000,
        value=st.session_state.get("starting_balance", 10_000),
        step=1_000, format="%d", key="custom_bal_input",
        on_change=_sync_bal,
        label_visibility="collapsed",
    )

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)

    bal = st.session_state.get("starting_balance", 10_000)
    st.markdown(
        f'<div style="text-align:center;padding:0.5rem 0;">'
        f'<span style="font-size:1.8rem;font-weight:700;color:#f1f5f9;font-family:var(--mono);">'
        f'${int(bal):,}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2, 1.6, 1.2])
    with c2:
        if st.button("Start Simulation", type="primary", width="stretch", use_container_width=True):
            st.switch_page("pages/01_Dashboard.py")


# ── Features ──────────────────────────────────────────────────────────
st.markdown('<div style="height:3rem;"></div>', unsafe_allow_html=True)

st.markdown(
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;max-width:720px;margin:0 auto;">'
    + ''.join(
        f'<div class="feature-card">'
        f'<div class="feature-icon">{icon}</div>'
        f'<div class="feature-title">{title}</div>'
        f'<div class="feature-desc">{desc}</div>'
        f'</div>'
        for icon, title, desc in [
            ("⚡", "Live Engine", "Real-time tick processing with spread & slippage simulation"),
            ("🤖", "Auto Trading", "SMA crossover with news sentiment signal integration"),
            ("💬", "Co-Pilot", "Natural language trade parsing via LLM with human approval"),
            ("📊", "Analytics", "Sharpe, Sortino, drawdown, equity curve & trade history"),
        ]
    )
    + '</div>',
    unsafe_allow_html=True,
)

# ── Footer ────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:4rem 0 1.5rem;">'
    '<div style="font-size:0.65rem;color:#334155;letter-spacing:0.04em;">'
    'AuraTrader AI &middot; Streamlit + Plotly</div>'
    '</div>',
    unsafe_allow_html=True,
)
