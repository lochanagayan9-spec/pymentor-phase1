from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.config import MAX_MEMORY_TURNS

class ConversationMemory:
    """In-memory session manager that maintains conversation history with sliding window."""

    def __init__(self, max_turns: int = MAX_MEMORY_TURNS):
        self.max_turns = max_turns
        # Maps session_id to list of turn dicts: {"role": "user"|"model", "text": str, "timestamp": str}
        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Returns the conversation history for a given session."""
        return list(self._sessions.get(session_id, []))

    def add_user_message(self, session_id: str, text: str) -> None:
        """Appends a user message to the session's history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": "user",
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._trim_history(session_id)

    def add_assistant_message(self, session_id: str, text: str) -> None:
        """Appends an assistant (model) message to the session's history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": "model",
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._trim_history(session_id)

    def _trim_history(self, session_id: str) -> None:
        """Trims old messages if history exceeds 2 * max_turns (pairs of user + model turns)."""
        history = self._sessions.get(session_id, [])
        max_messages = self.max_turns * 2
        if len(history) > max_messages:
            # Keep the most recent messages
            self._sessions[session_id] = history[-max_messages:]

    def clear_session(self, session_id: str) -> None:
        """Clears the session history completely."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_turn_count(self, session_id: str) -> int:
        """Returns total messages in current session."""
        return len(self._sessions.get(session_id, []))

# Global memory singleton instance
memory_manager = ConversationMemory()
