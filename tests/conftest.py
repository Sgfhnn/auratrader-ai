from __future__ import annotations

import pytest

import config
import storage


@pytest.fixture(autouse=True)
def _fresh_session() -> None:
    """Clear all sessions before each test and create a fresh one."""
    storage._sessions.clear()
    sd = storage.create_session(config.STARTING_BALANCE)
    storage._session_for_test = sd
    yield
    storage._sessions.clear()
    if hasattr(storage, "_session_for_test"):
        del storage._session_for_test


@pytest.fixture
def sid(_fresh_session: None) -> str:
    """Return the session_id of the test session."""
    return storage._session_for_test.session_id
