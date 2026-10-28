import pytest
from app.memory import ConversationMemory

def test_session_conversation_memory():
    """Verify that multi-turn dialogue history is retained in session memory."""
    mem = ConversationMemory(max_turns=5)
    session_id = "test-session-123"

    assert mem.get_turn_count(session_id) == 0

    mem.add_user_message(session_id, "What is a decorator?")
    mem.add_assistant_message(session_id, "A decorator is a callable that wraps another function.")

    history = mem.get_history(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["text"] == "What is a decorator?"
    assert history[1]["role"] == "model"
    assert "wraps another function" in history[1]["text"]

def test_session_isolation():
    """Verify that different sessions maintain isolated conversation histories."""
    mem = ConversationMemory(max_turns=5)
    s1, s2 = "session-alice", "session-bob"

    mem.add_user_message(s1, "Hello from Alice")
    mem.add_user_message(s2, "Hello from Bob")

    assert len(mem.get_history(s1)) == 1
    assert mem.get_history(s1)[0]["text"] == "Hello from Alice"
    assert len(mem.get_history(s2)) == 1
    assert mem.get_history(s2)[0]["text"] == "Hello from Bob"

def test_sliding_window_trimming():
    """Verify that history older than max_turns is trimmed cleanly."""
    mem = ConversationMemory(max_turns=2)
    session = "test-sliding"

    # Add 4 turns (8 messages)
    for i in range(4):
        mem.add_user_message(session, f"Question {i}")
        mem.add_assistant_message(session, f"Answer {i}")

    history = mem.get_history(session)
    # max_turns=2 allows 2 * 2 = 4 messages max
    assert len(history) == 4
    # Earliest retained should be Question 2
    assert history[0]["text"] == "Question 2"
    assert history[-1]["text"] == "Answer 3"

def test_clear_session():
    """Verify that clearing session drops memory."""
    mem = ConversationMemory(max_turns=5)
    session = "test-clear"
    mem.add_user_message(session, "Remember this")
    assert mem.get_turn_count(session) == 1

    mem.clear_session(session)
    assert mem.get_turn_count(session) == 0
    assert len(mem.get_history(session)) == 0
