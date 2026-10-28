import pytest
import sqlite3
from pathlib import Path
from app.database import (
    init_db,
    log_interaction,
    get_recent_logs,
    get_session_logs,
    get_analytics_summary
)

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_logs.db"
    init_db(db_file)
    return db_file

def test_database_initialization(temp_db):
    """Verify that table and indexes are initialized correctly in SQLite."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_logs';")
    assert cursor.fetchone() is not None, "chat_logs table was not created"
    conn.close()

def test_log_interaction_and_retrieval(temp_db):
    """Verify logging interaction with timestamp and response time."""
    row_id = log_interaction(
        session_id="session-xyz",
        user_message="What is a generator?",
        bot_response="A generator yields values lazily.",
        response_time_ms=145.67,
        tokens_used=42,
        status="success",
        db_path=temp_db
    )
    assert row_id > 0

    logs = get_recent_logs(limit=10, db_path=temp_db)
    assert len(logs) == 1
    assert logs[0]["session_id"] == "session-xyz"
    assert logs[0]["response_time_ms"] == 145.67
    assert logs[0]["status"] == "success"
    assert "T" in logs[0]["timestamp"] # ISO format timestamp check

def test_session_specific_logs(temp_db):
    """Verify filtering logs by session ID."""
    log_interaction("s1", "Q1", "A1", 100.0, db_path=temp_db)
    log_interaction("s2", "Q2", "A2", 150.0, db_path=temp_db)
    log_interaction("s1", "Q3", "A3", 120.0, db_path=temp_db)

    s1_logs = get_session_logs("s1", db_path=temp_db)
    assert len(s1_logs) == 2
    assert s1_logs[0]["user_message"] == "Q1"
    assert s1_logs[1]["user_message"] == "Q3"

def test_analytics_summary(temp_db):
    """Verify aggregated metrics calculation."""
    log_interaction("s1", "In-scope", "Ans", 100.0, tokens_used=10, status="success", db_path=temp_db)
    log_interaction("s1", "Out-scope", "Refuse", 50.0, tokens_used=5, status="out_of_scope", db_path=temp_db)
    log_interaction("s1", "Bad input", "Err", 10.0, tokens_used=0, status="error", db_path=temp_db)

    metrics = get_analytics_summary(db_path=temp_db)
    assert metrics["total_messages"] == 3
    assert metrics["success_count"] == 1
    assert metrics["out_of_scope_count"] == 1
    assert metrics["error_count"] == 1
    assert metrics["avg_latency_ms"] == round((100.0 + 50.0 + 10.0) / 3, 2)
