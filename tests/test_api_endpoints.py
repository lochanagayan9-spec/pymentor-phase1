import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.memory import memory_manager

client = TestClient(app)

def test_serve_frontend_index():
    """Verify that root URL returns the single-page HTML interface."""
    res = client.get("/")
    assert res.status_code == 200
    assert "PyMentor" in res.text
    assert "text/html" in res.headers["content-type"]

def test_chat_endpoint_in_scope():
    """Verify processing an in-scope Python question."""
    payload = {
        "message": "Explain how list comprehensions work in Python",
        "session_id": "test-api-session-1",
        "force_mock": True
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "test-api-session-1"
    assert data["status"] == "success"
    assert "Quick Insight" in data["response"]
    assert data["response_time_ms"] > 0

def test_chat_endpoint_out_of_scope():
    """Verify handling out-of-scope questions."""
    payload = {
        "message": "Give me a recipe for chocolate cake",
        "session_id": "test-api-session-2",
        "force_mock": True
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "out_of_scope"
    assert "cannot assist with queries outside Python" in data["response"]

def test_chat_endpoint_empty_message():
    """Verify that empty input returns HTTP 400 Bad Request."""
    payload = {
        "message": "   ",
        "session_id": "test-empty"
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 400
    assert "Message cannot be empty" in res.json()["detail"]

def test_session_reset_endpoint():
    """Verify resetting session memory via API."""
    session_id = "test-reset-session"
    # Add a message first
    client.post("/api/chat", json={
        "message": "What is LEGB?",
        "session_id": session_id,
        "force_mock": True
    })

    # Verify history is populated
    hist_res = client.get(f"/api/session/{session_id}/history")
    assert hist_res.json()["count"] > 0

    # Reset session
    reset_res = client.post("/api/session/reset", json={"session_id": session_id})
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"

    # Verify history is now cleared
    hist_after = client.get(f"/api/session/{session_id}/history")
    assert hist_after.json()["count"] == 0

def test_logs_and_analytics_endpoints():
    """Verify endpoints for retrieving SQLite chat logs and metrics."""
    res_logs = client.get("/api/logs?limit=10")
    assert res_logs.status_code == 200
    assert "logs" in res_logs.json()

    res_analytics = client.get("/api/logs/analytics")
    assert res_analytics.status_code == 200
    analytics = res_analytics.json()
    assert "total_messages" in analytics
    assert "avg_latency_ms" in analytics

def test_knowledge_and_health_endpoints():
    """Verify knowledge summary and health check endpoints."""
    res_kb = client.get("/api/knowledge")
    assert res_kb.status_code == 200
    kb_data = res_kb.json()
    assert kb_data["status"] == "loaded"
    assert len(kb_data["sections"]) > 0

    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    health = res_health.json()
    assert health["status"] == "online"
    assert health["database"] == "sqlite_ready"
