from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

import config
import matching_engine
import storage
from components.theme import inject_theme
from components.layout import render_sidebar, render_page_header
from utils.session import ensure_initialized


def _sid() -> str:
    return st.session_state.get("session_id", "")


from utils.metrics import (
    sharpe_ratio, sortino_ratio, max_drawdown, win_rate,
    profit_factor, expectancy, value_at_risk, consecutive_streaks,
)

inject_theme()
render_sidebar()
ensure_initialized()
render_page_header("Analytics", "Deep performance & risk metrics")


# ── Live equity history (ensure it exists) ──────────────────────────────────
if "equity_history" not in st.session_state:
    st.session_state["equity_history"] = []


def _trade_pnl_series(trades: list[dict]) -> list[float]:
    return [t.get("profit_loss", 0.0) for t in trades]


# ───────────────────────────────────────────────────────────────────────────────
# OVERVIEW METRICS
# ───────────────────────────────────────────────────────────────────────────────
@st.fragment(run_every=3)
def analytics_overview() -> None:
    history = storage.get_trade_history(_sid())
    equity_curve = [e["equity"] for e in st.session_state["equity_history"]]

    if not history:
        st.info("No closed trades yet. Place some trades to see analytics here.")
        return

    returns = _trade_pnl_series(history)
    eq_list = list(st.session_state["equity_history"])
    eq_values = [e["equity"] for e in eq_list]

    sr = sharpe_ratio(returns)
    sor = sortino_ratio(returns)
    mdd = max_drawdown(eq_values) if eq_values else 0.0
    wr = win_rate(history)
    pf = profit_factor(history)
    exp = expectancy(history)
    var_95 = value_at_risk(returns, 0.95)
    streaks = consecutive_streaks(history)

    m1, m2, m3, m4 = st.columns(4)
    metrics_data = [
        (m1, "Sharpe Ratio", f"{sr:.2f}", "green" if sr >= 1 else ("red" if sr < 0 else "")),
        (m2, "Sortino Ratio", f"{sor:.2f}", "green" if sor >= 1 else ("red" if sor < 0 else "")),
        (m3, "Win Rate", f"{wr:.1f}%", "green" if wr >= 50 else "red"),
        (m4, "Profit Factor", f"{pf:.2f}", "green" if pf >= 1.5 else ("red" if pf < 1 else "")),
    ]
    for col, lbl, val, cls in metrics_data:
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="label">{lbl}</div>'
                f'<div class="value {cls}">{val}</div></div>',
                unsafe_allow_html=True,
            )

    m5, m6, m7, m8 = st.columns(4)
    metrics_data2 = [
        (m5, "Max Drawdown", f"{mdd:.2%}", "red" if mdd > 0.1 else "green"),
        (m6, "Avg. Expectancy", f"${exp:+.2f}", "green" if exp >= 0 else "red"),
        (m7, "VaR (95%)", f"${var_95:+.2f}", "red"),
        (m8, "Best Streak / Worst", f"{streaks['max_win_streak']}W / {streaks['max_loss_streak']}L", "accent"),
    ]
    for col, lbl, val, cls in metrics_data2:
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="label">{lbl}</div>'
                f'<div class="value {cls}">{val}</div></div>',
                unsafe_allow_html=True,
            )


analytics_overview()

st.markdown("<br>", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# CHARTS
# ───────────────────────────────────────────────────────────────────────────────
tab_dist, tab_equity_detail, tab_timeline = st.tabs(["📊 P&L Distribution", "📈 Equity & Drawdown", "🕐 Trade Timeline"])


# ── Tab 1: P&L Distribution ─────────────────────────────────────────────────
with tab_dist:
    @st.fragment(run_every=5)
    def pnl_distribution() -> None:
        history = storage.get_trade_history(_sid())
        if not history:
            st.info("No data yet.")
            return

        df = pd.DataFrame(history)
        pnls = df["profit_loss"]

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=pnls,
            nbinsx=20,
            marker_color="#3b82f6",
            marker_line_color="#1e3a5f",
            marker_line_width=1,
            opacity=0.85,
            name="Trades",
        ))
        fig.update_layout(
            title="Trade P&L Distribution",
            height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,33,0.6)",
            font=dict(color="#8899b4", family="Inter", size=11),
            xaxis=dict(title="Profit / Loss ($)", gridcolor="rgba(59,130,246,0.06)"),
            yaxis=dict(title="Frequency", gridcolor="rgba(59,130,246,0.06)"),
            margin=dict(l=8, r=8, t=32, b=8),
            bargap=0.15,
        )
        st.plotly_chart(fig, width="stretch", key="pnl_dist")

        # Cumulative P&L
        df_sorted = df.sort_values("timestamp")
        df_sorted["cumulative"] = df_sorted["profit_loss"].cumsum()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=list(range(len(df_sorted))), y=df_sorted["cumulative"],
            mode="lines", name="Cumulative P&L",
            line=dict(color="#22c55e", width=2), fill="tozeroy",
            fillcolor="rgba(34,197,94,0.06)",
        ))
        fig2.update_layout(
            title="Cumulative P&L (ordered by close time)",
            height=280,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,33,0.6)",
            font=dict(color="#8899b4", family="Inter", size=11),
            xaxis=dict(title="Trade #", gridcolor="rgba(59,130,246,0.06)"),
            yaxis=dict(title="Cumulative P&L ($)", gridcolor="rgba(59,130,246,0.06)"),
            margin=dict(l=8, r=8, t=32, b=8),
        )
        st.plotly_chart(fig2, width="stretch", key="cum_pnl")

    pnl_distribution()


# ── Tab 2: Equity & Drawdown ─────────────────────────────────────────────────
with tab_equity_detail:
    @st.fragment(run_every=3)
    def equity_drawdown() -> None:
        eq_list = list(st.session_state["equity_history"])
        if len(eq_list) < 5:
            st.info("Collecting equity data…")
            return

        eq_df = pd.DataFrame(eq_list)
        eq_vals = eq_df["equity"].tolist()
        peak = eq_vals[0]
        dd_vals = []
        for v in eq_vals:
            if v > peak:
                peak = v
            dd_vals.append((peak - v) / peak * 100 if peak > 0 else 0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eq_df["t"], y=eq_vals, mode="lines", name="Equity",
            line=dict(color="#3b82f6", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=eq_df["t"], y=dd_vals, mode="lines", name="Drawdown %",
            line=dict(color="#ef4444", width=1.5, dash="dot"),
            yaxis="y2",
        ))
        fig.update_layout(
            height=340,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,33,0.6)",
            font=dict(color="#8899b4", family="Inter", size=11),
            xaxis=dict(gridcolor="rgba(59,130,246,0.06)"),
            yaxis=dict(title="Equity ($)", gridcolor="rgba(59,130,246,0.06)"),
            yaxis2=dict(title="Drawdown %", overlaying="y", side="right",
                        gridcolor="rgba(239,68,68,0.06)",
                        tickformat=".1f"),
            margin=dict(l=8, r=8, t=8, b=8),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            uirevision="lock",
        )
        st.plotly_chart(fig, width="stretch", key="eq_dd")

    equity_drawdown()


# ── Tab 3: Trade Timeline ───────────────────────────────────────────────────
with tab_timeline:
    @st.fragment(run_every=5)
    def trade_timeline() -> None:
        history = storage.get_trade_history(_sid())
        if not history:
            st.info("No trades yet.")
            return

        df = pd.DataFrame(history)
        df = df.sort_values("timestamp").reset_index(drop=True)
        df["trade_num"] = range(1, len(df) + 1)

        colors = ["#22c55e" if p >= 0 else "#ef4444" for p in df["profit_loss"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["trade_num"], y=df["profit_loss"],
            marker_color=colors,
            text=[f"${p:+.0f}" for p in df["profit_loss"]],
            textposition="outside",
            textfont=dict(size=9, color="#8899b4"),
        ))
        fig.update_layout(
            title="P&L per Trade (ordered by close time)",
            height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,20,33,0.6)",
            font=dict(color="#8899b4", family="Inter", size=11),
            xaxis=dict(title="Trade #", gridcolor="rgba(59,130,246,0.06)", dtick=1),
            yaxis=dict(title="P&L ($)", gridcolor="rgba(59,130,246,0.06)"),
            margin=dict(l=8, r=8, t=32, b=8),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch", key="timeline_bar")

        # Win/Loss pie
        wins = int((df["profit_loss"] > 0).sum())
        losses = int((df["profit_loss"] <= 0).sum())
        fig2 = go.Figure(go.Pie(
            labels=["Wins", "Losses"],
            values=[wins, losses],
            marker=dict(colors=["#22c55e", "#ef4444"]),
            hole=0.55,
            textinfo="label+percent",
            textfont=dict(color="#e8edf5", size=12),
        ))
        fig2.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8899b4"),
            margin=dict(l=6, r=6, t=6, b=6),
            showlegend=False,
        )
        st.plotly_chart(fig2, width="stretch", key="winloss_pie_analytics")

    trade_timeline()
