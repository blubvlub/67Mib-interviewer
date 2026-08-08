"""
In-memory session manager for tracking interview state.
Each session stores candidate data, conversation history, and interview progress.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from app.models import CandidateProfile

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Holds all state for a single interview session."""
    session_id: str
    candidate: CandidateProfile
    conversation_history: list[dict] = field(default_factory=list)
    question_plan: list[dict] = field(default_factory=list)
    questions_asked: int = 0
    topics_covered: set = field(default_factory=set)
    current_topic_index: int = 0
    candidate_analysis: str = ""
    curriculum_context: str = ""
    is_complete: bool = False


class SessionManager:
    """Thread-safe in-memory session store."""

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        session_id: str,
        candidate: CandidateProfile,
    ) -> SessionState:
        """Create a new interview session."""
        async with self._lock:
            if session_id in self._sessions:
                logger.info("Session %s already exists, resetting", session_id)

            session = SessionState(
                session_id=session_id,
                candidate=candidate,
            )
            self._sessions[session_id] = session
            logger.info("Created session %s for candidate %s", session_id, candidate.member.name)
            return session

    async def get_session(self, session_id: str) -> SessionState | None:
        """Retrieve an existing session."""
        async with self._lock:
            return self._sessions.get(session_id)

    async def update_session(self, session: SessionState) -> None:
        """Update a session in the store."""
        async with self._lock:
            self._sessions[session.session_id] = session

    async def delete_session(self, session_id: str) -> None:
        """Remove a session."""
        async with self._lock:
            self._sessions.pop(session_id, None)
            logger.info("Deleted session %s", session_id)

    async def list_sessions(self) -> list[str]:
        """List all active session IDs."""
        async with self._lock:
            return list(self._sessions.keys())
