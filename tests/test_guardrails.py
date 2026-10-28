import pytest
from app.prompt_builder import check_out_of_scope_heuristic
from app.agent import PyMentorAgent

@pytest.fixture
def agent():
    return PyMentorAgent()

def test_heuristic_out_of_scope_detection():
    """Verify that blatantly non-Python topics are flagged by heuristic guardrails."""
    oos_queries = [
        ("Can you give me a recipe for chocolate cake?", "culinary recipes and cooking"),
        ("What is the weather forecast in Tokyo today?", "weather and meteorological forecasts"),
        ("Who won the last presidential election?", "politics and government"),
        ("Write a Java Spring Boot microservice controller", "non-Python programming languages"),
        ("Recommend a good horror movie to watch tonight", "movies and entertainment"),
    ]
    for query, expected_topic in oos_queries:
        is_oos, topic = check_out_of_scope_heuristic(query)
        assert is_oos is True, f"Failed to detect out-of-scope query: {query}"
        assert topic == expected_topic

def test_in_scope_queries_pass_guardrails():
    """Verify that Python queries are not incorrectly flagged as out-of-scope."""
    in_scope_queries = [
        "Explain how Python list comprehensions work",
        "Why does def func(x=[]) cause bugs in Python?",
        "How does the LEGB scope rule resolve variables?",
        "Difference between __new__ and __init__",
        "How do I fix a TypeError: unsupported operand type(s) for +?",
        "Can you compare Python lists with Java ArrayLists?", # explicitly mentions Python
    ]
    for query in in_scope_queries:
        is_oos, _ = check_out_of_scope_heuristic(query)
        assert is_oos is False, f"In-scope query was incorrectly blocked: {query}"

def test_agent_out_of_scope_polite_refusal(agent):
    """Verify that out-of-scope questions return a polite refusal explaining allowed scope."""
    res = agent.process_message(
        session_id="test-oos",
        user_message="How do I bake sourdough bread?",
        force_mock=True
    )
    assert res["status"] == "out_of_scope"
    assert "PyMentor" in res["response"]
    assert "cannot assist with queries outside Python" in res["response"]
    assert "Here is what I can help you with:" in res["response"]
    assert res["response_time_ms"] >= 0

def test_agent_i_dont_know_behavior(agent):
    """Verify that unverified or fictitious packages trigger honest 'I don't know' response."""
    res = agent.process_message(
        session_id="test-idk",
        user_message="How do I configure the fictitious quantum_teleporter_v9 package in Python?",
        force_mock=True
    )
    assert res["status"] == "success"
    assert "do not have verified information" in res["response"]
    assert "docs.python.org" in res["response"]

def test_agent_in_scope_explanation(agent):
    """Verify in-scope Python answers follow the 4-part pedagogical structure."""
    res = agent.process_message(
        session_id="test-in-scope",
        user_message="Explain mutable default arguments bug with def func(x=[])",
        force_mock=True
    )
    assert res["status"] == "success"
    assert "Quick Insight (TL;DR)" in res["response"]
    assert "Code Walkthrough" in res["response"]
    assert "Under the Hood" in res["response"]
    assert "Pythonic Tip" in res["response"]
    assert "```python" in res["response"]
