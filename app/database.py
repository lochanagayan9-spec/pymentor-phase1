import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import DATABASE_FILE

def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Creates a connection to SQLite database with Row factory and ensures schema exists."""
    path = db_path or DATABASE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                response_time_ms REAL NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                status TEXT NOT NULL CHECK(status IN ('success', 'out_of_scope', 'error')),
                error_message TEXT
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON chat_logs(session_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_logs(timestamp);")
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    """Explicitly initializes the database schema."""
    conn = get_db_connection(db_path)
    conn.close()

def log_interaction(
    session_id: str,
    user_message: str,
    bot_response: str,
    response_time_ms: float,
    tokens_used: int = 0,
    status: str = "success",
    error_message: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Stores a user-assistant dialogue turn in the database with timestamps and metrics."""
    conn = get_db_connection(db_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_logs (
                    session_id, timestamp, user_message, bot_response,
                    response_time_ms, tokens_used, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    timestamp,
                    user_message,
                    bot_response,
                    round(response_time_ms, 2),
                    tokens_used,
                    status,
                    error_message,
                ),
            )
            return cursor.lastrowid
    finally:
        conn.close()

def get_recent_logs(limit: int = 50, offset: int = 0, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieves recent chat logs ordered by newest first."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, session_id, timestamp, user_message, bot_response,
                   response_time_ms, tokens_used, status, error_message
            FROM chat_logs
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_session_logs(session_id: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieves all chat logs for a specific session ID."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, session_id, timestamp, user_message, bot_response,
                   response_time_ms, tokens_used, status, error_message
            FROM chat_logs
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_analytics_summary(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Calculates aggregate metrics for monitoring chat performance."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COALESCE(AVG(response_time_ms), 0.0) as avg_latency_ms,
                COALESCE(SUM(tokens_used), 0) as total_tokens,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'out_of_scope' THEN 1 ELSE 0 END) as out_of_scope_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM chat_logs
        """)
        row = cursor.fetchone()
        return {
            "total_messages": row["total_messages"] or 0,
            "avg_latency_ms": round(row["avg_latency_ms"], 2),
            "total_tokens": row["total_tokens"] or 0,
            "success_count": row["success_count"] or 0,
            "out_of_scope_count": row["out_of_scope_count"] or 0,
            "error_count": row["error_count"] or 0,
        }
    finally:
        conn.close()
