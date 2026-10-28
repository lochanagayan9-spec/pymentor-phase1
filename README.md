# ?? PyMentor: Domain-Restricted Python Code Understanding Chatbot

PyMentor is an intelligent virtual assistant and senior pedagogical tutor built specifically for understanding, analyzing, and explaining Python code. Powered by Google Gemini API and FastAPI, PyMentor enforces strict domain boundaries, maintains multi-turn conversation memory, dynamically injects an external knowledge base, provides honest "I don't know" grounding, and logs every interaction with latency telemetry to a local SQLite database.

---

## ?? Key Features & Requirements Coverage

| # | Requirement | Implementation in PyMentor |
|---|---|---|
| **1** | **Chat Interface** | Modern, responsive Web UI with syntax highlighting (`highlight.js`), Markdown parsing (`marked.js`), one-click "Copy Code" buttons, latency badges, and SQLite log drawer. |
| **2** | **Backend** | Fast, asynchronous Python backend using **FastAPI** + **Uvicorn**, calling Google Gemini API via the official `google-genai` SDK. |
| **3** | **System Prompt** | Modular 4-layer prompt architecture: Persona & Role, Curated Knowledge Base, Task Instructions & Boundaries, and Output Formatting. |
| **4** | **Custom Knowledge Base** | Domain knowledge stored in an external file (`data/knowledge.md`) and loaded dynamically into the prompt at runtime—never hardcoded in Python code. |
| **5** | **Conversation Memory** | In-memory session manager (`ConversationMemory`) maintaining multi-turn context with sliding-window protection and session reset. |
| **6** | **Out-of-Scope Handling** | Dual-tier guardrail system (heuristics + system prompt) that politely declines non-Python queries (cooking, politics, Java, movies) and restates allowed Python capabilities. |
| **7** | **"I Don'\''t Know" Behavior** | Grounded response policy: for undocumented third-party or fictitious libraries (`quantum_teleporter_v9`), the assistant explicitly admits lack of verified knowledge rather than hallucinating. |
| **8** | **Error Handling** | Robust error handling for empty messages, rate limits (`ResourceExhausted`), invalid API keys, and connection timeouts with user-friendly error banners. |
| **9** | **Secure Key Handling** | API key lives in `.env` (loaded via `python-dotenv`) and is protected by `.gitignore` so secrets are never committed. |
| **10** | **Chat Logging** | SQLite database (`data/pymentor_logs.db`) logging session ID, user message, assistant response, response time (ms), token usage, status, and timestamps. |

---

## ?? Persona & Tone: *The Patient Python Senior Architect*

* **Core Identity:** An approachable, highly experienced senior Python software engineer and mentor.
* **Tone:** Patient, encouraging, mechanically rigorous, and strictly PEP 8 compliant.
* **Pedagogical Structure:** PyMentor structures every code explanation into four clear parts:
  1. **Quick Insight (TL;DR):** Immediate 1-2 sentence conceptual takeaway.
  2. **Code Walkthrough:** Clean, runnable snippet with inline comments.
  3. **Under the Hood:** CPython execution mechanics (memory allocation, scope binding, iteration protocol, or bytecode).
  4. **Pythonic Tip / Gotcha:** A practical PEP 8 suggestion or common pitfall to avoid (e.g. mutable default arguments, late-binding closures).

---

## ??? Project Architecture

```
pymentor/
+-- .env.example              # Template for environment variables
+-- .env                      # Local secret file (gitignored)
+-- .gitignore                # Protects secrets, caches, and databases
+-- requirements.txt          # Python dependencies
+-- README.md                 # Project documentation and guide
¦
+-- data/
¦   +-- knowledge.md          # External domain knowledge base (Layer 2)
¦   +-- pymentor_logs.db      # SQLite chat logging database
¦
+-- app/
¦   +-- __init__.py
¦   +-- config.py             # Settings, paths, and environment loader
¦   +-- database.py           # SQLite connection, logging, and analytics
¦   +-- memory.py             # Conversation session memory manager
¦   +-- prompt_builder.py     # 4-layer system prompt assembler & guardrails
¦   +-- agent.py              # PyMentor agent core (Gemini API & test mock)
¦   +-- main.py               # FastAPI application & REST endpoints
¦   +-- static/               # Frontend Single Page Application
¦       +-- index.html        # Responsive Chat UI & SQLite Log Modal
¦       +-- css/style.css     # Dark-mode styling, badges, and layout
¦       +-- js/app.js         # Chat client, syntax highlighting, and copy buttons
¦
+-- docs/
¦   +-- limitations.md        # Documented system limitations & failure modes
¦   +-- test_report.md        # Detailed report of 22 automated test scenarios
¦
+-- tests/
    +-- test_prompt_and_kb.py # Tests for knowledge loading & prompt layers
    +-- test_memory.py        # Tests for multi-turn history & sliding window
    +-- test_guardrails.py    # Tests for out-of-scope refusals & 'I don't know'
    +-- test_database.py      # Tests for SQLite logging & latency metrics
    +-- test_api_endpoints.py # Tests for FastAPI endpoints & input validation
```

---

## ?? Quick Start Guide

### 1. Installation
Clone or navigate to the project directory and install dependencies:
```bash
cd pymentor
pip install -r requirements.txt
```

### 2. Configure Environment Secrets
Create your `.env` file from the example template:
```bash
cp .env.example .env
```
Open `.env` and add your Google Gemini API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
```
*(Note: If no API key is provided, PyMentor automatically runs in its intelligent offline test simulation mode!)*

### 3. Launch the Application
Run the FastAPI server using Uvicorn:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Open the Web UI
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## ?? Systematic Testing

Run the automated test suite with pytest:
```bash
python -m pytest tests/ -v
```
All 22 unit and integration tests verify:
- Dynamic knowledge base file loading
- 4-layer system prompt composition
- In-memory multi-turn conversation tracking
- Strict out-of-scope heuristic and prompt rejections
- Grounded "I don't know" handling for unverified packages
- SQLite log creation, timestamping, and latency recording
- FastAPI request validation and error responses

---

## ?? SQLite Chat Inspector

Click the **"?? DB Logs"** button in the top right of the Web UI to open the real-time SQLite analytics and log inspector drawer. It displays:
- Total interactions count
- Average response time in milliseconds
- Total tokens processed
- Breakdown of in-scope vs out-of-scope queries
- Live table of queries, responses, and timestamps directly from `data/pymentor_logs.db`.

---

## ?? Documentation

- [System Limitations Document](docs/limitations.md): Detailed analysis of operational boundaries, safety rules, and failure modes.
- [Systematic Test Report](docs/test_report.md): Breakdown of the 22 automated test scenarios and results.
