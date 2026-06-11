from __future__ import annotations

import streamlit as st

import config
import matching_engine
import storage


def _sid() -> str:
    return st.session_state.get("session_id", "")


def render_sidebar() -> None:
    """Custom sidebar: logo, nav hint, account summary, data source."""
    data_src = matching_engine.get_data_source()
    if "OANDA" in data_src:
        src_dot = "live"
    elif "REAL" in data_src or "Yahoo" in data_src:
        src_dot = "mock"
    else:
        src_dot = "mock"

    with st.sidebar:
        st.markdown(
            f'<div class="sidebar-logo">'
            f'  <span class="logo-icon">⚡</span>'
            f'  <span class="logo-text">AuraTrader</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="padding:0 0.75rem 0.75rem;font-size:0.7rem;color:var(--text-muted);letter-spacing:0.06em;">'
            f'  REAL-TIME FOREX PLATFORM · v1.0'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Live connection status
        st.markdown(
            f'<div style="padding:0 0.75rem 0.75rem;display:flex;align-items:center;gap:6px;">'
            f'  <span class="status-dot {src_dot}"></span>'
            f'  <span style="font-size:0.72rem;color:var(--text-muted);font-weight:500;">{data_src}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        # Account snapshot
        acct = storage.get_account(_sid())
        bal = acct.get("balance", 0.0)
        eq = acct.get("equity", 0.0)
        fpnl = eq - bal
        pnl_cls = "green" if fpnl >= 0 else "red"
        pnl_sign = "+" if fpnl >= 0 else ""

        st.markdown(
            f'<div class="sidebar-acct">'
            f'  <div class="acct-label">Balance</div>'
            f'  <div class="acct-value">${bal:,.2f}</div>'
            f'  <div style="display:flex;justify-content:space-between;margin-top:0.5rem;">'
            f'    <div><div class="acct-label">Equity</div><div class="acct-value" style="font-size:0.95rem;">${eq:,.2f}</div></div>'
            f'    <div style="text-align:right;"><div class="acct-label">Float P&L</div>'
            f'      <div class="acct-value {pnl_cls}" style="font-size:0.95rem;">{pnl_sign}${fpnl:,.2f}</div>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="padding:0.5rem 0.75rem 0;font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Navigation</div>',
            unsafe_allow_html=True,
        )

    # Mobile header (rendered in main body)
    st.markdown(
        '<div class="mobile-header">'
        '<button class="mobile-hamburger" onclick="'
        'document.querySelector(\'[data-testid=stSidebarCollapseButton]\')?.click()'
        '">☰</button>'
        '<span class="mobile-logo">AuraTrader</span>'
        '<a href="/?signout=1" class="mobile-signout">Sign Out</a>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:12px;padding:0.75rem 0 0.25rem;">'
        f'  <span style="font-size:1.5rem;font-weight:700;color:var(--text-primary);letter-spacing:-0.02em;">{title}</span>'
        f'  {f"<span style=\'font-size:0.8rem;color:var(--text-muted);\'>{subtitle}</span>" if subtitle else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_metric_row(metrics: list[dict]) -> None:
    """Render a row of metric cards. Each dict: label, value, cls (optional), sub (optional)."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        val_cls = m.get("cls", "")
        val_tag = f'<span class="value {val_cls}">{m["value"]}</span>'
        sub_tag = f'<div class="sub">{m.get("sub", "")}</div>' if m.get("sub") else ""
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'  <div class="label">{m["label"]}</div>'
                f'  {val_tag}'
                f'  {sub_tag}'
                f'</div>',
                unsafe_allow_html=True,
            )
