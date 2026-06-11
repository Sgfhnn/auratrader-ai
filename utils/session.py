"""Session initialisation — shared across pages so engine/DB init happens once."""

from collections import deque

import streamlit as st

import time as _time

import matching_engine
import storage


def ensure_initialized() -> None:
    if "session_start" not in st.session_state:
        st.session_state["session_start"] = _time.time()

    if "session_id" not in st.session_state:
        balance = float(st.session_state.get("starting_balance", 100_000.0))
        st.session_state["starting_balance"] = balance
        sd = storage.create_session(balance)
        st.session_state["session_id"] = sd.session_id
        st.session_state["session_store"] = sd

    if "engine_started" not in st.session_state:
        matching_engine.start_engine_thread()
        st.session_state["engine_started"] = True

    if "equity_history" not in st.session_state:
        st.session_state["equity_history"] = deque(maxlen=400)

    if "pending_trade" not in st.session_state:
        st.session_state["pending_trade"] = None

    if "sentiment_cache" not in st.session_state:
        st.session_state["sentiment_cache"] = {"sentiment": "NEUTRAL", "headlines": ""}

    if "auto_log" not in st.session_state:
        st.session_state["auto_log"] = []

    if "last_trade" not in st.session_state:
        st.session_state["last_trade"] = None

    if "auto_active" not in st.session_state:
        st.session_state["auto_active"] = False
