# PyMentor Systematic Test Report

## 1. Executive Summary
PyMentor was subjected to automated unit and integration testing covering all 10 mandatory functional requirements. The test suite comprises 22 automated test cases executed via `pytest`, achieving a 100% pass rate.

```
============================= 22 passed in 2.27s ==============================
```

---

## 2. Test Coverage Matrix

| Requirement | Test Function | Test File | Status |
|---|---|---|---|
| **1. Chat Interface** | `test_serve_frontend_index` | `test_api_endpoints.py` | **PASSED** |
| **2. Backend API** | `test_chat_endpoint_in_scope` | `test_api_endpoints.py` | **PASSED** |
| **3. Four-Layer System Prompt** | `test_system_prompt_four_layers` | `test_prompt_and_kb.py` | **PASSED** |
| **4. Custom Knowledge Base** | `test_knowledge_base_file_exists_and_loads` | `test_prompt_and_kb.py` | **PASSED** |
| **5. Conversation Memory** | `test_session_conversation_memory` | `test_memory.py` | **PASSED** |
| **5. Memory Sliding Window** | `test_sliding_window_trimming` | `test_memory.py` | **PASSED** |
| **5. Session Isolation** | `test_session_isolation` | `test_memory.py` | **PASSED** |
| **5. Session Reset** | `test_session_reset_endpoint` | `test_api_endpoints.py` | **PASSED** |
| **6. Out-of-Scope Heuristics** | `test_heuristic_out_of_scope_detection` | `test_guardrails.py` | **PASSED** |
| **6. In-Scope Pass-Through** | `test_in_scope_queries_pass_guardrails` | `test_guardrails.py` | **PASSED** |
| **6. Polite Refusal Format** | `test_agent_out_of_scope_polite_refusal` | `test_guardrails.py` | **PASSED** |
| **7. 'I Don'\''t Know' Grounding** | `test_agent_i_dont_know_behavior` | `test_guardrails.py` | **PASSED** |
| **8. Empty Input Validation** | `test_chat_endpoint_empty_message` | `test_api_endpoints.py` | **PASSED** |
| **9. Secure Key & Health Check** | `test_knowledge_and_health_endpoints` | `test_api_endpoints.py` | **PASSED** |
| **10. SQLite Schema Init** | `test_database_initialization` | `test_database.py` | **PASSED** |
| **10. SQLite Logging & Latency** | `test_log_interaction_and_retrieval` | `test_database.py` | **PASSED** |
| **10. Session-Filtered Logs** | `test_session_specific_logs` | `test_database.py` | **PASSED** |
| **10. Analytics Aggregation** | `test_analytics_summary` | `test_database.py` | **PASSED** |
| **10. Log API Endpoints** | `test_logs_and_analytics_endpoints` | `test_api_endpoints.py` | **PASSED** |

---

## 3. Detailed Test Scenarios & Outcomes

### Scenario A: In-Scope Python Understanding
* **Input Query:** *"Explain mutable default arguments bug with def func(x=[])"*
* **Expected Result:** Structured 4-part response (`Quick Insight`, `Code Walkthrough`, `Under the Hood`, `Pythonic Tip`), PEP 8 recommendation, and code blocks using ` ```python `.
* **Observed Result:** Matches all expected sections; logged to SQLite with status `success` and recorded latency.

### Scenario B: Out-of-Scope Polite Refusal
* **Input Query:** *"How do I bake sourdough bread?"*
* **Expected Result:** Immediate polite decline explaining that PyMentor is strictly dedicated to Python, accompanied by a bulleted summary of permitted Python topics.
* **Observed Result:** Returned status `out_of_scope`, refusal text matched persona specifications, and logged to SQLite under `out_of_scope`.

### Scenario C: Fictitious Package ("I Don't Know" Grounding)
* **Input Query:** *"How do I configure the fictitious quantum_teleporter_v9 package in Python?"*
* **Expected Result:** Refusal to hallucinate imaginary code; honest admission that the knowledge base lacks verified documentation, redirecting to official sources (`docs.python.org` / PyPI).
* **Observed Result:** Cleanly admitted uncertainty without inventing non-existent APIs.

### Scenario D: Edge Cases & Error Handling
* **Empty / Whitespace Input (`"   "`):** Rejected with HTTP 400 Bad Request and error banner.
* **Session Reset:** Clears in-memory turns for that session without affecting other concurrent sessions.
* **Database Resilience:** Automatically creates SQLite table `chat_logs` and indexes if not already present.
