"""
Pydantic models for API request/response schemas.
Matches the technical specification exactly.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# --- Candidate Data Models ---

class Mission(BaseModel):
    """A single mission (day) from the candidate's learning journey."""
    day: int
    title: str
    passed: Optional[bool] = None
    attempts: Optional[int] = None
    skipped: Optional[bool] = None


class Signals(BaseModel):
    """Aggregate learning signals for a candidate."""
    commitDays: int
    missionsCompleted: int
    missionsFirstTry: int


class Member(BaseModel):
    """Candidate member info."""
    id: str
    name: str
    jobRole: str
    yearsExperience: int
    education: str
    status: str


class CandidateProfile(BaseModel):
    """Full candidate profile as provided in candidates.json."""
    member: Member
    missions: list[Mission]
    signals: Signals


# --- API Request Models ---

class InterviewRequest(BaseModel):
    """
    Unified request model for POST /api/interview.
    - Start: sessionId + candidate (no message)
    - Turn:  sessionId + message (no candidate)
    """
    sessionId: str = Field(..., description="Unique session identifier")
    candidate: Optional[CandidateProfile] = Field(
        None, description="Candidate profile (only on first request)"
    )
    message: Optional[str] = Field(
        None, description="Candidate's response (on subsequent requests)"
    )


# --- API Response Models ---

class Feedback(BaseModel):
    """Structured interview feedback returned at the end."""
    summary: str = Field(..., description="Overall interview summary")
    strengths: list[str] = Field(..., description="Candidate's demonstrated strengths")
    gaps: list[str] = Field(..., description="Knowledge gaps identified")
    next: list[str] = Field(..., description="Recommended next steps")


class InterviewResponse(BaseModel):
    """Response from POST /api/interview."""
    reply: str = Field(..., description="Interviewer's message")
    done: bool = Field(False, description="Whether the interview is complete")
    feedback: Optional[Feedback] = Field(
        None, description="Feedback (only when done=true)"
    )
