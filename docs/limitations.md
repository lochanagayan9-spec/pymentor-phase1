# PyMentor System Limitations & Architectural Boundaries

This document provides an explicit, transparent assessment of PyMentor's capabilities, operational boundaries, and architectural limitations in accordance with professional AI engineering standards.

---

## 1. Domain Scope Limitations

### 1.1 Python-Only Restriction
* **Limitation:** PyMentor is strictly restricted to Python programming concepts, syntax, execution mechanics, tracebacks, and standard library modules.
* **Failure Mode / Behavior:** Queries concerning other programming languages (e.g. JavaScript, C++, Rust, Go, Java, Swift) or non-technical topics (cooking, movies, medical advice, politics) are politely declined.
* **Exception:** PyMentor will discuss non-Python languages only when directly contrasting a language mechanism to aid a Python learner (e.g. *"Unlike C arrays which are fixed memory buffers, Python lists are dynamic arrays of object pointers"*).

### 1.2 Knowledge Base Boundaries ("I Don't Know" Grounding)
* **Limitation:** PyMentor relies on its curated knowledge base (`data/knowledge.md`) and standard Python 3.x language documentation. It does not possess internal knowledge of proprietary corporate internal libraries or undocumented packages.
* **Failure Mode / Behavior:** If asked about fictitious, unverified, or unreleased packages (e.g., `quantum_teleporter_v9`), PyMentor is instructed **never to hallucinate** imaginary APIs, functions, or arguments. It explicitly states: *"Based on my current Python knowledge base and documentation, I don't have verified information regarding this package."*

---

## 2. Execution & Safety Boundaries

### 2.1 No Arbitrary Remote Code Execution (RCE)
* **Design Decision:** PyMentor acts as a static pedagogical code explainer and reasoning agent. It intentionally does **NOT** run an untrusted `eval()` or `exec()` sandbox on user inputs.
* **Rationale:** Executing arbitrary Python code from untrusted web clients introduces extreme security hazards (arbitrary file read/write, fork bombs, network exfiltration).
* **Limitation:** PyMentor traces and mental-models execution through AST and conceptual semantics rather than executing live CPython binaries on the host machine.

### 2.2 Malicious Code Refusal
* **Design Decision:** PyMentor strictly refuses requests to generate malware, remote access trojans (RATs), keyloggers, credential harvesters, or automated vulnerability exploit scripts.
* **Mitigation:** When asked about security topics, PyMentor redirects towards defensive concepts (e.g., secure deserialization with `json` instead of `pickle`, input sanitization, and timing attack mitigation).

---

## 3. Conversation Memory & Context Windows

### 3.1 Sliding Window Memory
* **Limitation:** PyMentor maintains conversational memory using a sliding window of recent dialogue turns (configured by `MAX_MEMORY_TURNS`, default: 10 turns).
* **Implication:** If a dialogue extends beyond 20 total messages (10 user turns and 10 assistant turns), the earliest turns are pruned from working memory to prevent token exhaustion and maintain low latency.
* **Session Lifetime:** In-memory session context is volatile and resets when the server process restarts, although complete chat logs remain permanently stored in SQLite (`data/pymentor_logs.db`).

### 3.2 Single File / Snippet Focus
* **Limitation:** PyMentor is optimized for single modules, functions, classes, and code snippets up to ~2,000 lines of code. It is not designed to ingest whole multi-gigabyte repositories in a single prompt.

---

## 4. API & Network Dependencies

### 4.1 Dependency on Upstream Gemini API
* **Limitation:** When live mode is active, PyMentor requires network connectivity to Google's Gemini API endpoints (`https://generativelanguage.googleapis.com`).
* **Error Handling:** In the event of network disruption, rate limits (`ResourceExhausted`), or missing API keys, PyMentor gracefully logs the error to SQLite with an `"error"` status code and presents a clear, actionable toast message to the user rather than crashing.
* **Offline Mock Fallback:** PyMentor includes an intelligent offline simulation mode allowing complete test suite execution and persona verification even without an active internet connection.

---

## 5. Summary Matrix

| Capability | Supported | Limitation / Mitigation |
|---|---|---|
| Python Code Explanation | Yes | Step-by-step 4-layer pedagogical breakdown |
| Memory Across Multi-turn Sessions | Yes | Retained per `session_id` up to `MAX_MEMORY_TURNS` |
| Non-Python Query Handling | Refused | Polite refusal message defining permitted scope |
| Unknown / Hallucinated Libraries | Refused | Explicit "I don't know" grounded response |
| SQLite Logging & Response Latency | Yes | Stored in `data/pymentor_logs.db` with millisecond precision |
| Live Arbitrary Code Execution | No | Static analysis only to prevent RCE vulnerabilities |
| Secret Key Protection | Yes | Loaded from `.env` on server-side only; never committed |
