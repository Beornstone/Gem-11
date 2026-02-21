from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_PAYEES = [
    "James (Son)",
    "Pete (Doctor)",
    "Sarah (Landlord)",
    "Aisha (Friend)",
]


@dataclass
class SessionState:
    payees_allowed: list[str] = field(default_factory=lambda: DEFAULT_PAYEES[:10])
    pending_transfer: dict | None = None
    screen: str = "home"


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState()
        return self._sessions[session_id]


session_store = SessionStore()
