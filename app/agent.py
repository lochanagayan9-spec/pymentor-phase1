import time
import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types, errors

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MODEL_FALLBACK_CASCADE,
    is_api_key_valid,
)
from app.database import log_interaction
from app.memory import memory_manager
from app.prompt_builder import (
    OUT_OF_SCOPE_DECLINE_TEMPLATE,
    build_system_prompt,
    check_out_of_scope_heuristic,
)

logger = logging.getLogger("pymentor.agent")

class PyMentorAgent:
    """
    Intelligent Agent for Python Code Understanding.
    Features:
    - Persona & pedagogical four-part structure
    - Domain boundary guardrails & 'I don't know' grounding
    - Conversation memory tracking
    - Resilient Multi-Model Fallback Engine (cascades across models upon error/deprecation)
    - SQLite interaction logging with latency telemetry
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        self._system_prompt = build_system_prompt()
        self._client: Optional[genai.Client] = None

        if is_api_key_valid():
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self._client = None

    def refresh_knowledge(self) -> None:
        """Reloads the external knowledge base into the active system prompt."""
        self._system_prompt = build_system_prompt()

    def process_message(
        self,
        session_id: str,
        user_message: str,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a dialogue turn with multi-model fallback resilience.
        """
        start_time = time.perf_counter()
        clean_input = user_message.strip()

        # 1. Validation: Empty or whitespace input
        if not clean_input:
            latency = (time.perf_counter() - start_time) * 1000
            err_msg = "Message cannot be empty. Please enter a Python question or code snippet."
            log_interaction(
                session_id=session_id,
                user_message=user_message,
                bot_response=err_msg,
                response_time_ms=latency,
                status="error",
                error_message="Empty input"
            )
            return {
                "session_id": session_id,
                "response": err_msg,
                "response_time_ms": round(latency, 2),
                "tokens_used": 0,
                "status": "error",
                "model_used": "none"
            }

        # 2. Fast-tier Guardrail: Heuristic out-of-scope check
        is_oos, topic = check_out_of_scope_heuristic(clean_input)
        if is_oos:
            latency = (time.perf_counter() - start_time) * 1000
            refusal = OUT_OF_SCOPE_DECLINE_TEMPLATE.format(topic=topic or "unrelated non-Python topics")
            
            memory_manager.add_user_message(session_id, clean_input)
            memory_manager.add_assistant_message(session_id, refusal)
            tokens_est = len(clean_input.split()) + len(refusal.split())
            log_interaction(
                session_id=session_id,
                user_message=clean_input,
                bot_response=refusal,
                response_time_ms=latency,
                tokens_used=tokens_est,
                status="out_of_scope"
            )
            return {
                "session_id": session_id,
                "response": refusal,
                "response_time_ms": round(latency, 2),
                "tokens_used": tokens_est,
                "status": "out_of_scope",
                "model_used": "guardrails"
            }

        # 3. Execution via Gemini API or Mock Simulator
        if force_mock or not self._client or not is_api_key_valid():
            return self._simulate_mock_turn(session_id, clean_input, start_time)

        # Build conversation memory contents
        history = memory_manager.get_history(session_id)
        contents: List[types.Content] = []
        for turn in history:
            contents.append(
                types.Content(
                    role=turn["role"],
                    parts=[types.Part.from_text(text=turn["text"])]
                )
            )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=clean_input)]
            )
        )

        config = types.GenerateContentConfig(
            system_instruction=self._system_prompt,
            temperature=0.2,
            max_output_tokens=2048,
        )

        # Multi-Model Fallback Engine:
        # Tries the primary model, then cascades through available fallback models
        models_to_try: List[str] = [self.model]
        for candidate in MODEL_FALLBACK_CASCADE:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        successful_response = None
        successful_model = None
        last_error = None

        for candidate_model in models_to_try:
            try:
                logger.info(f"PyMentor querying Gemini with model: {candidate_model}")
                response = self._client.models.generate_content(
                    model=candidate_model,
                    contents=contents,
                    config=config,
                )
                if response and response.text:
                    successful_response = response
                    successful_model = candidate_model
                    break
            except errors.APIError as e:
                err_text = str(e)
                logger.warning(f"Model {candidate_model} failed ({err_text[:100]}). Falling back...")
                last_error = e
                # If API key itself is invalid, stop trying other models
                if "API_KEY_INVALID" in err_text or "401" in err_text:
                    break
                continue
            except Exception as e:
                logger.warning(f"Model {candidate_model} error: {e}. Falling back...")
                last_error = e
                continue

        # If a model succeeded
        if successful_response and successful_response.text:
            latency = (time.perf_counter() - start_time) * 1000
            reply_text = successful_response.text

            tokens_used = 0
            if hasattr(successful_response, "usage_metadata") and successful_response.usage_metadata:
                tokens_used = getattr(successful_response.usage_metadata, "total_token_count", 0) or 0
            if tokens_used == 0:
                tokens_used = len(clean_input.split()) + len(reply_text.split())

            status = "success"
            if "outside my domain" in reply_text.lower() or "cannot assist with queries outside python" in reply_text.lower():
                status = "out_of_scope"

            memory_manager.add_user_message(session_id, clean_input)
            memory_manager.add_assistant_message(session_id, reply_text)
            log_interaction(
                session_id=session_id,
                user_message=clean_input,
                bot_response=reply_text,
                response_time_ms=latency,
                tokens_used=tokens_used,
                status=status
            )

            return {
                "session_id": session_id,
                "response": reply_text,
                "response_time_ms": round(latency, 2),
                "tokens_used": tokens_used,
                "status": status,
                "model_used": successful_model
            }

        # If all models failed, handle the error gracefully
        latency = (time.perf_counter() - start_time) * 1000
        err_str = str(last_error) if last_error else "All fallback models were unavailable."
        
        if "ResourceExhausted" in err_str or "429" in err_str:
            err_msg = "Gemini API rate limit exceeded across fallback models. Please wait a moment before sending another message."
        elif "API_KEY_INVALID" in err_str or "401" in err_str:
            err_msg = "Invalid Gemini API Key. Please verify your GEMINI_API_KEY in the .env file."
        else:
            err_msg = f"Gemini API Error: {err_str}"

        log_interaction(
            session_id=session_id,
            user_message=clean_input,
            bot_response=err_msg,
            response_time_ms=latency,
            status="error",
            error_message=err_str
        )
        return {
            "session_id": session_id,
            "response": err_msg,
            "response_time_ms": round(latency, 2),
            "tokens_used": 0,
            "status": "error",
            "model_used": "none"
        }

    def _simulate_mock_turn(
        self, session_id: str, user_message: str, start_time: float
    ) -> Dict[str, Any]:
        """Intelligent offline pedagogical simulation fallback."""
        time.sleep(0.04)
        latency = (time.perf_counter() - start_time) * 1000
        msg_lower = user_message.lower()

        if "teleport" in msg_lower or "fictitious" in msg_lower or "quantum_v9" in msg_lower or "unknown_lib" in msg_lower:
            reply = (
                "Based on my current Python knowledge base and official documentation, "
                "I do not have verified information regarding this specific library or module. "
                "To ensure accuracy and prevent hallucinated code, please consult the official "
                "documentation at [docs.python.org](https://docs.python.org) or the package's "
                "official PyPI repository rather than relying on unverified estimates."
            )
            status = "success"

        elif "tuple" in msg_lower and ("mutate" in msg_lower or "append" in msg_lower):
            reply = (
                "### 1. Quick Insight (TL;DR)\n"
                "A tuple itself is **immutable**, meaning its fixed sequence of references cannot change. "
                "However, if a tuple contains a reference to a **mutable object** (like a `list`), that nested object "
                "can still be mutated in place!\n\n"
                "### 2. Code Walkthrough\n"
                "```python\n"
                "t = (1, 2, [3, 4])\n\n"
                "# 1. This succeeds because we mutate the list object, not the tuple's reference:\n"
                "t[2].append(5)\n"
                "print(t)  # Output: (1, 2, [3, 4, 5])\n\n"
                "# 2. This modifies the list BUT THEN raises a TypeError:\n"
                "# t[2] += [6]\n"
                "# TypeError: 'tuple' object does not support item assignment\n"
                "```\n\n"
                "### 3. Under the Hood (Why `+=` raises an error but modifies the list)\n"
                "The augmented assignment `t[2] += [6]` executes two distinct bytecode operations:\n"
                "1. **In-place extend**: Calls `list.__iadd__` on the list at `t[2]`, which mutates the list in place.\n"
                "2. **Assignment**: Tries to assign the result back to `t[2]` via `STORE_SUBSCR`. Because `t` is a tuple, "
                "Python forbids item assignment and raises a `TypeError`!\n"
                "Result: The list *was* modified, but an exception was still thrown!\n\n"
                "### 4. Pythonic Tip / Best Practice\n"
                "Avoid placing mutable collections (lists, dicts, sets) inside tuples. If you need an immutable composite structure, "
                "use nested tuples or a `frozen=True` dataclass."
            )
            status = "success"

        elif "mutable default" in msg_lower or "def func(x=[])" in msg_lower or "basket=[]" in msg_lower:
            reply = (
                "### 1. Quick Insight (TL;DR)\n"
                "In Python, default parameter values are evaluated **once at function definition time**, "
                "not each time the function is called. If you use a mutable default (like a `list` or `dict`), "
                "all calls share that exact same object in memory!\n\n"
                "### 2. Code Walkthrough\n"
                "```python\n"
                "# Anti-pattern: Mutating the shared default parameter\n"
                "def append_item(item, basket=[]):\n"
                "    basket.append(item)\n"
                "    return basket\n\n"
                "# The Idiomatic Solution:\n"
                "def append_item_safe(item, basket=None):\n"
                "    if basket is None:\n"
                "        basket = []  # A fresh list is created on every invocation\n"
                "    basket.append(item)\n"
                "    return basket\n"
                "```\n\n"
                "### 3. Under the Hood\n"
                "When CPython defines a function, it compiles the code object and attaches default "
                "arguments to the function's `__defaults__` tuple. Mutating `basket` mutates `append_item.__defaults__[0]` directly.\n\n"
                "### 4. Pythonic Tip / Best Practice\n"
                "Always use `None` as a sentinel for mutable defaults, and assign a fresh collection inside the function body."
            )
            status = "success"

        elif "legb" in msg_lower or "scope" in msg_lower:
            reply = (
                "### 1. Quick Insight (TL;DR)\n"
                "Python resolves variable names using the **LEGB rule**, searching four scopes sequentially: "
                "**L**ocal -> **E**nclosing -> **G**lobal -> **B**uilt-in. If the name is not found in any of them, Python raises `NameError`.\n\n"
                "### 2. Code Walkthrough\n"
                "```python\n"
                "x = 'Global'  # Global scope (G)\n\n"
                "def outer():\n"
                "    x = 'Enclosing'  # Enclosing scope (E)\n"
                "    def inner():\n"
                "        x = 'Local'  # Local scope (L)\n"
                "        print(x)     # Resolves to 'Local'\n"
                "    inner()\n"
                "```\n\n"
                "### 3. Under the Hood\n"
                "CPython optimizes local variable lookups into `LOAD_FAST` bytecode instructions using an array indexed by variable offset, "
                "whereas global lookups use `LOAD_GLOBAL` searching the module's `__dict__`.\n\n"
                "### 4. Pythonic Tip / Best Practice\n"
                "Minimize `global` and `nonlocal` variables. Functions with explicit inputs and return values are cleaner and easier to test."
            )
            status = "success"

        elif "__new__" in msg_lower or "__init__" in msg_lower:
            reply = (
                "### 1. Quick Insight (TL;DR)\n"
                "`__new__` is the constructor that **allocates** and returns the object instance, while "
                "`__init__` is the initializer that configures attributes on the already-created instance.\n\n"
                "### 2. Code Walkthrough\n"
                "```python\n"
                "class Singleton:\n"
                "    _instance = None\n"
                "    def __new__(cls, *args, **kwargs):\n"
                "        if cls._instance is None:\n"
                "            cls._instance = super().__new__(cls)\n"
                "        return cls._instance\n\n"
                "    def __init__(self, value):\n"
                "        self.value = value\n"
                "```\n\n"
                "### 3. Under the Hood\n"
                "When you evaluate `obj = MyClass()`, Python executes `instance = MyClass.__new__(MyClass)`. If it returns an instance "
                "of `MyClass`, Python then calls `instance.__init__()`.\n\n"
                "### 4. Pythonic Tip / Best Practice\n"
                "Implement `__init__` for 99% of classes. Only override `__new__` when subclassing immutable types or creating singletons."
            )
            status = "success"

        elif "list comprehension" in msg_lower or "comprehension" in msg_lower:
            reply = (
                "### 1. Quick Insight (TL;DR)\n"
                "List comprehensions provide a concise, readable, and computationally efficient syntax for transforming or filtering iterables into new lists.\n\n"
                "### 2. Code Walkthrough\n"
                "```python\n"
                "numbers = [1, 2, 3, 4, 5, 6]\n"
                "squared_evens = [n ** 2 for n in numbers if n % 2 == 0]\n"
                "# Result: [4, 16, 36]\n"
                "```\n\n"
                "### 3. Under the Hood\n"
                "CPython optimizes list comprehensions using the `LIST_APPEND` bytecode instruction, avoiding repeated `list.append` attribute lookups.\n\n"
                "### 4. Pythonic Tip / Best Practice\n"
                "Keep comprehensions readable. Avoid nesting more than two loops or conditions inside a single comprehension."
            )
            status = "success"

        else:
            reply = (
                f"### 1. Quick Insight (TL;DR)\n"
                f"Here is the analysis for your Python inquiry: **\"{user_message}\"**.\n\n"
                f"### 2. Code Walkthrough\n"
                f"```python\n"
                f"def explain_concept():\n"
                f"    \"\"\"Demonstrates clean idiomatic Python.\"\"\"\n"
                f"    return [x for x in range(5)]\n"
                f"```\n\n"
                f"### 3. Under the Hood\n"
                f"Variables in Python bind names to heap objects. Python handles memory automatically through reference counting and cyclic garbage collection.\n\n"
                f"### 4. Pythonic Tip / Best Practice\n"
                f"Always follow PEP 8 and The Zen of Python: *Readability counts. Simple is better than complex.*"
            )
            status = "success"

        memory_manager.add_user_message(session_id, user_message)
        memory_manager.add_assistant_message(session_id, reply)
        tokens_used = len(user_message.split()) + len(reply.split())
        log_interaction(
            session_id=session_id,
            user_message=user_message,
            bot_response=reply,
            response_time_ms=latency,
            tokens_used=tokens_used,
            status=status
        )

        return {
            "session_id": session_id,
            "response": reply,
            "response_time_ms": round(latency, 2),
            "tokens_used": tokens_used,
            "status": status,
            "model_used": "mock_simulator"
        }

# Global agent singleton
pymentor_agent = PyMentorAgent()
