INJECTED_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --bg-deep: #080c14;
    --bg-primary: #0d1421;
    --bg-secondary: #111b2e;
    --bg-card: #141f33;
    --bg-card-hover: #1a2844;
    --bg-elevated: #1a2a42;
    --border: #1e3a5f;
    --border-light: #2a4a7a;
    --text-primary: #e8edf5;
    --text-secondary: #8899b4;
    --text-muted: #556688;
    --accent: #3b82f6;
    --accent-hover: #60a5fa;
    --accent-subtle: rgba(59,130,246,0.12);
    --green: #22c55e;
    --green-bg: rgba(34,197,94,0.10);
    --green-border: rgba(34,197,94,0.25);
    --red: #ef4444;
    --red-bg: rgba(239,68,68,0.10);
    --red-border: rgba(239,68,68,0.25);
    --amber: #f59e0b;
    --amber-bg: rgba(245,158,11,0.10);
    --purple: #a78bfa;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --mono: 'JetBrains Mono', 'Fira Code', monospace;
    --radius: 10px;
    --radius-sm: 6px;
  }

  html, body, [class*="css"] {
    font-family: var(--font);
    color: var(--text-primary);
  }

  .stApp {
    background: var(--bg-primary);
  }

  /* ── Sidebar ───────────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background: var(--bg-deep) !important;
    border-right: 1px solid var(--border) !important;
    width: 260px !important;
  }
  section[data-testid="stSidebar"] > div {
    padding: 1rem 0.75rem !important;
  }
  section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-secondary);
    font-size: 0.8rem;
  }

  /* Sidebar nav items */
  section[data-testid="stSidebar"] a {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.15s ease;
    text-decoration: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    margin: 1px 0;
  }
  section[data-testid="stSidebar"] a:hover {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
  }
  section[data-testid="stSidebar"] a:active,
  section[data-testid="stSidebar"] a:focus {
    color: var(--accent) !important;
  }
  section[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 0.75rem 0 !important;
  }

  /* Sidebar logo area */
  .sidebar-logo {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    padding: 0 0.75rem 0.75rem;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .sidebar-logo .logo-icon {
    font-size: 1.4rem;
  }
  .sidebar-logo .logo-text {
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Sidebar account summary */
  .sidebar-acct {
    background: linear-gradient(135deg, var(--bg-card) 0%, #131d30 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
  }
  .sidebar-acct .acct-label {
    font-size: 0.65rem;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .sidebar-acct .acct-value {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    font-family: var(--mono);
  }
  .sidebar-acct .acct-change {
    font-size: 0.75rem;
    font-weight: 600;
  }

  /* ── Metric cards ──────────────────────────────────── */
  .metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.25rem;
  }
  .metric-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, color-mix(in srgb, var(--bg-card) 97%, var(--accent)) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.15rem;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.2), 0 1px 1px rgba(0,0,0,0.15);
    position: relative;
    overflow: hidden;
  }
  .metric-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius);
    background: linear-gradient(135deg, transparent 60%, rgba(255,255,255,0.015) 100%);
    pointer-events: none;
  }
  .metric-card:hover {
    border-color: var(--border-light);
    background: var(--bg-card-hover);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3), 0 2px 4px rgba(0,0,0,0.2);
    transform: translateY(-1px);
  }
  .metric-card .label {
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
    position: relative;
  }
  .metric-card .value {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    font-family: var(--mono);
    line-height: 1.3;
    position: relative;
  }
  .metric-card .sub {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
    position: relative;
  }
  .metric-card .value.green { color: var(--green); }
  .metric-card .value.red { color: var(--red); }
  .metric-card .value.accent { color: var(--accent); }

  /* ── Section headers ───────────────────────────────── */
  .section-header {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 0.75rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Data tables ───────────────────────────────────── */
  .stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  }
  .stDataFrame [data-testid="StyledDataFrameColHeader"] {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, #151e32 100%) !important;
    color: var(--text-secondary) !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 0.75rem !important;
    border-bottom: 1px solid var(--border) !important;
  }
  .stDataFrame td {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    font-size: 0.8rem !important;
    font-family: var(--mono) !important;
    padding: 0.4rem 0.75rem !important;
    border-bottom: 1px solid rgba(30,58,95,0.4) !important;
  }
  .stDataFrame tr:hover td {
    background: var(--bg-card-hover) !important;
  }

  /* ── Tabs ──────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: var(--radius) !important;
    padding: 4px !important;
    gap: 3px !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.2s ease !important;
    height: auto !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: var(--text-secondary) !important;
    background: rgba(255,255,255,0.03) !important;
  }
  .stTabs [aria-selected="true"] {
    background: var(--accent-subtle) !important;
    color: var(--accent-hover) !important;
    box-shadow: 0 1px 3px rgba(59,130,246,0.15);
  }

  /* ── Buttons ───────────────────────────────────────── */
  .stButton button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    padding: 0.4rem 1.1rem !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.15);
  }
  .stButton button:hover {
    border-color: var(--accent) !important;
    background: var(--bg-card-hover) !important;
    color: var(--accent-hover) !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.1);
    transform: translateY(-1px);
  }
  .stButton button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent) 0%, #2563eb 100%) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.25);
  }
  .stButton button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--accent-hover) 0%, #3b82f6 100%) !important;
    border-color: var(--accent-hover) !important;
    box-shadow: 0 4px 14px rgba(59,130,246,0.35);
    transform: translateY(-1px);
  }

  /* ── Toggle / Switch ───────────────────────────────── */
  .stToggle [data-testid="stWidgetLabel"] {
    font-size: 0.8rem !important;
    color: var(--text-secondary) !important;
  }

  /* ── Info / Warning / Error boxes ──────────────────── */
  .stAlert {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
  }
  .stInfo { background: var(--accent-subtle) !important; border-color: rgba(59,130,246,0.3) !important; }
  .stWarning { background: var(--amber-bg) !important; border-color: rgba(245,158,11,0.3) !important; }
  .stError { background: var(--red-bg) !important; border-color: var(--red-border) !important; }
  .stSuccess { background: var(--green-bg) !important; border-color: var(--green-border) !important; }

  /* ── Expander ──────────────────────────────────────── */
  .streamlit-expanderHeader {
    font-size: 0.8rem !important;
    color: var(--text-secondary) !important;
    background: var(--bg-card) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
  }

  /* ── Dividers ──────────────────────────────────────── */
  hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
    opacity: 0.6;
  }

  /* ── Text inputs ───────────────────────────────────── */
  .stTextInput input, .stTextArea textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 0.85rem !important;
  }
  .stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-subtle) !important;
  }

  /* ── Selectbox ─────────────────────────────────────── */
  .stSelectbox div[data-baseweb="select"] {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    border-radius: var(--radius-sm) !important;
  }

  /* ── Plotly chart area ─────────────────────────────── */
  .js-plotly-plot {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
  }

  /* ── Badge chips ───────────────────────────────────── */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .badge-green { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
  .badge-red { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
  .badge-blue { background: var(--accent-subtle); color: var(--accent-hover); border: 1px solid rgba(59,130,246,0.3); }
  .badge-amber { background: var(--amber-bg); color: var(--amber); border: 1px solid rgba(245,158,11,0.3); }
  .badge-neutral { background: rgba(100,116,139,0.15); color: var(--text-secondary); border: 1px solid rgba(100,116,139,0.25); }

  /* ── Status indicator dot ──────────────────────────── */
  .status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 5px;
  }
  .status-dot.live { background: var(--green); box-shadow: 0 0 6px rgba(34,197,94,0.5); }
  .status-dot.mock { background: var(--amber); box-shadow: 0 0 6px rgba(245,158,11,0.4); }
  .status-dot.off { background: var(--text-muted); }

  /* ── Mode indicator banner ─────────────────────────── */
  .mode-banner {
    padding: 0.5rem 1rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 1rem;
  }
  .mode-banner.copilot {
    background: var(--accent-subtle);
    border: 1px solid rgba(59,130,246,0.3);
    color: var(--accent-hover);
  }
  .mode-banner.autonomous {
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    color: var(--green);
  }

  /* ── Trade journal entry ───────────────────────────── */
  .trade-log-entry {
    font-family: var(--mono);
    font-size: 0.75rem;
    padding: 0.4rem 0.75rem;
    background: var(--bg-card);
    border-left: 2px solid var(--border);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin: 0.2rem 0;
    color: var(--text-secondary);
  }

  /* ── Sentiment chip ────────────────────────────────── */
  .sentiment-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    gap: 5px;
  }
  .sentiment-bullish { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
  .sentiment-bearish { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
  .sentiment-neutral { background: rgba(100,116,139,0.12); color: var(--text-secondary); border: 1px solid rgba(100,116,139,0.2); }

  /* ── Panel card ────────────────────────────────────── */
  .panel {
    background: linear-gradient(135deg, var(--bg-card) 0%, color-mix(in srgb, var(--bg-card) 96%, var(--accent)) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    position: relative;
    overflow: hidden;
  }
  .panel::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius);
    background: linear-gradient(135deg, transparent 50%, rgba(255,255,255,0.012) 100%);
    pointer-events: none;
  }
  .panel-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Download button ────────────────────────────────── */
  .stDownloadButton button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    padding: 0.35rem 1rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
  }
  .stDownloadButton button:hover {
    border-color: var(--accent) !important;
    background: var(--bg-card-hover) !important;
    color: var(--accent-hover) !important;
  }

  /* ── Scrollbar ─────────────────────────────────────── */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--border-light); }

  /* ── Account header bar ────────────────────────────── */
  .header-bar {
    display: flex;
    align-items: center;
    gap: 0;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.55rem 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  }
  .header-item {
    display: flex;
    align-items: baseline;
    gap: 6px;
    padding: 0 0.75rem;
  }
  .header-item:first-child { padding-left: 0; }
  .header-label {
    font-size: 0.62rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .header-value {
    font-size: 0.9rem;
    font-weight: 700;
    font-family: var(--mono);
    color: var(--text-primary);
  }
  .header-value.green { color: var(--green); }
  .header-value.red { color: var(--red); }
  .header-value.amber { color: var(--amber); }
  .header-divider {
    width: 1px;
    height: 22px;
    background: var(--border);
    flex-shrink: 0;
  }

  /* ── Market watch ──────────────────────────────────── */
  .mw-header {
    display: grid;
    grid-template-columns: 1.1fr 1fr 0.9fr;
    padding: 0.25rem 0.5rem 0.15rem;
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid rgba(30,58,95,0.3);
  }
  .mw-row {
    display: grid;
    grid-template-columns: 1.1fr 1fr 0.9fr;
    padding: 0.28rem 0.5rem;
    font-size: 0.75rem;
    font-family: var(--mono);
    border-bottom: 1px solid rgba(30,58,95,0.1);
    transition: background 0.1s;
  }
  .mw-row:hover { background: rgba(255,255,255,0.02); }
  .mw-pair { font-weight: 600; color: var(--text-primary); }
  .mw-bid { color: var(--text-secondary); text-align: right; }
  .mw-change { text-align: right; }
  .mw-change.green { color: var(--green); }
  .mw-change.red { color: var(--red); }
  .mw-change.muted { color: var(--text-muted); }

  /* ── Open positions compact rows ───────────────────── */
  .op-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.35rem 0;
    font-size: 0.78rem;
    border-bottom: 1px solid rgba(30,58,95,0.12);
    font-family: var(--mono);
  }
  .op-row:last-child { border-bottom: none; }
  .op-inst { font-weight: 600; color: var(--text-primary); min-width: 70px; }
  .op-vol { color: var(--text-muted); min-width: 45px; }
  .op-pnl { font-weight: 600; min-width: 70px; }
  .op-pnl.green { color: var(--green); }
  .op-pnl.red { color: var(--red); }
  .op-entry { color: var(--text-secondary); font-size: 0.72rem; }

  /* ── Micro stats ───────────────────────────────────── */
  .stat-micro {
    padding: 0.3rem 0;
  }
  .stat-label {
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: block;
  }
  .stat-value {
    font-size: 0.85rem;
    font-weight: 700;
    font-family: var(--mono);
    color: var(--text-primary);
  }
  .stat-value.green { color: var(--green); }
  .stat-value.red { color: var(--red); }

  /* ── Smooth transitions on page load ───────────────── */
  .main > div {
    animation: fadeIn 0.3s ease;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
"""


def inject_theme() -> None:
    import streamlit as st
    st.markdown(INJECTED_CSS, unsafe_allow_html=True)
