"""
Analyzes a candidate's profile to personalize the interview.
Maps missions to curriculum, identifies strengths, weaknesses, and gaps.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from app.models import CandidateProfile, Mission

logger = logging.getLogger(__name__)

# Load curriculum data once at module level
_CURRICULUM_PATH = Path(__file__).parent.parent / "problem_files" / "curriculum.json"
_curriculum_data = None


def _load_curriculum() -> dict:
    """Load and cache the curriculum JSON."""
    global _curriculum_data
    if _curriculum_data is None:
        with open(_CURRICULUM_PATH, "r") as f:
            _curriculum_data = json.load(f)
    return _curriculum_data


def get_curriculum_day(day: int) -> dict | None:
    """Get curriculum info for a specific day."""
    curriculum = _load_curriculum()
    for d in curriculum["days"]:
        if d["day"] == day:
            return d
    return None


def get_module_for_day(day: int) -> dict | None:
    """Get the module that contains a specific day."""
    curriculum = _load_curriculum()
    for module in curriculum["modules"]:
        start, end = module["days"]
        if start <= day <= end:
            return module
    return None


class CandidateAnalyzer:
    """Analyzes a candidate profile to generate interview personalization data."""

    def __init__(self, candidate: CandidateProfile):
        self.candidate = candidate
        self.member = candidate.member
        self.missions = candidate.missions
        self.signals = candidate.signals

    def analyze(self) -> str:
        """
        Produce a human-readable analysis string for the LLM system prompt.
        This gives the interviewer context about who they're interviewing.
        """
        sections = [
            self._analyze_background(),
            self._analyze_overall_performance(),
            self._analyze_strong_areas(),
            self._analyze_weak_areas(),
            self._analyze_skipped_topics(),
            self._analyze_gaps(),
        ]
        return "\n\n".join(sections)

    def get_topic_priorities(self) -> list[dict]:
        """
        Return a prioritized list of topics for the interview.
        Each entry has: day, title, priority, reason, module.
        """
        priorities = []

        for mission in self.missions:
            curriculum_day = get_curriculum_day(mission.day)
            module = get_module_for_day(mission.day)
            if not curriculum_day:
                continue

            entry = {
                "day": mission.day,
                "title": mission.title,
                "module": module["title"] if module else "Unknown",
                "objectives": curriculum_day.get("objectives", []),
                "tools": curriculum_day.get("tools", []),
            }

            if mission.skipped:
                entry["priority"] = "medium"
                entry["reason"] = "Skipped — explore if they have any familiarity"
            elif mission.passed is False:
                entry["priority"] = "high"
                entry["reason"] = f"Failed after {mission.attempts} attempts — probe understanding gaps"
            elif mission.passed and mission.attempts and mission.attempts >= 4:
                entry["priority"] = "high"
                entry["reason"] = f"Passed but took {mission.attempts} attempts — verify understanding"
            elif mission.passed and mission.attempts and mission.attempts >= 2:
                entry["priority"] = "medium"
                entry["reason"] = f"Passed in {mission.attempts} attempts — solid topic to explore"
            elif mission.passed and mission.attempts == 1:
                entry["priority"] = "low"
                entry["reason"] = "Passed first try — verify depth, ask advanced questions"
            else:
                entry["priority"] = "medium"
                entry["reason"] = "Standard topic"

            priorities.append(entry)

        # Sort: high priority first, then medium, then low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        priorities.sort(key=lambda x: priority_order.get(x["priority"], 1))

        return priorities

    def get_curriculum_context(self) -> str:
        """Build a curriculum context string with only the relevant days for this candidate."""
        curriculum = _load_curriculum()
        relevant_days = {m.day for m in self.missions}
        lines = ["The candidate worked on these curriculum topics:"]

        for day_data in curriculum["days"]:
            if day_data["day"] in relevant_days:
                module = get_module_for_day(day_data["day"])
                module_name = module["title"] if module else "Unknown"
                objectives = "; ".join(day_data.get("objectives", []))
                tools = ", ".join(day_data.get("tools", []))
                lines.append(
                    f"- Day {day_data['day']}: {day_data['title']} "
                    f"(Module: {module_name}) — Objectives: {objectives} — Tools: {tools}"
                )

        return "\n".join(lines)

    def _analyze_background(self) -> str:
        return (
            f"### Candidate Background\n"
            f"- Name: {self.member.name}\n"
            f"- Role: {self.member.jobRole}\n"
            f"- Experience: {self.member.yearsExperience} years\n"
            f"- Education: {self.member.education}\n"
            f"- Status: {self.member.status}"
        )

    def _analyze_overall_performance(self) -> str:
        total_missions = len(self.missions)
        passed = sum(1 for m in self.missions if m.passed)
        failed = sum(1 for m in self.missions if m.passed is False)
        skipped = sum(1 for m in self.missions if m.skipped)
        first_try = self.signals.missionsFirstTry

        strength_level = "strong"
        if self.signals.missionsFirstTry / max(self.signals.missionsCompleted, 1) < 0.3:
            strength_level = "developing"
        elif self.signals.missionsFirstTry / max(self.signals.missionsCompleted, 1) < 0.6:
            strength_level = "moderate"

        return (
            f"### Overall Performance ({strength_level} candidate)\n"
            f"- Missions attempted: {total_missions}\n"
            f"- Passed: {passed} | Failed: {failed} | Skipped: {skipped}\n"
            f"- First-try passes: {first_try}/{self.signals.missionsCompleted}\n"
            f"- Commit days: {self.signals.commitDays}/31\n"
            f"- Overall engagement: {'High' if self.signals.commitDays >= 25 else 'Moderate' if self.signals.commitDays >= 15 else 'Low'}"
        )

    def _analyze_strong_areas(self) -> str:
        strong = [
            m for m in self.missions
            if m.passed and m.attempts is not None and m.attempts <= 2
        ]
        if not strong:
            return "### Strong Areas\nNo topics passed on first or second try."

        lines = ["### Strong Areas (passed quickly — verify depth)"]
        for m in strong:
            curriculum_day = get_curriculum_day(m.day)
            module = get_module_for_day(m.day)
            lines.append(
                f"- Day {m.day}: {m.title} (Module: {module['title'] if module else 'N/A'}) "
                f"— passed in {m.attempts} attempt(s)"
            )
        return "\n".join(lines)

    def _analyze_weak_areas(self) -> str:
        weak = [
            m for m in self.missions
            if (m.passed and m.attempts is not None and m.attempts >= 4) or m.passed is False
        ]
        if not weak:
            return "### Weak Areas\nNo significant weak areas detected."

        lines = ["### Weak Areas (struggled — probe carefully)"]
        for m in weak:
            status = "FAILED" if m.passed is False else f"passed after {m.attempts} attempts"
            lines.append(f"- Day {m.day}: {m.title} — {status}")
        return "\n".join(lines)

    def _analyze_skipped_topics(self) -> str:
        skipped = [m for m in self.missions if m.skipped]
        if not skipped:
            return "### Skipped Topics\nNo topics were skipped."

        lines = ["### Skipped Topics (explore lightly)"]
        for m in skipped:
            lines.append(f"- Day {m.day}: {m.title}")
        return "\n".join(lines)

    def _analyze_gaps(self) -> str:
        """Identify curriculum modules with no missions attempted."""
        curriculum = _load_curriculum()
        attempted_days = {m.day for m in self.missions}

        gaps = []
        for module in curriculum["modules"]:
            start, end = module["days"]
            module_days = set(range(start, end + 1))
            if not module_days & attempted_days:
                gaps.append(f"- Module {module['n']}: {module['title']} (Days {start}-{end})")

        if not gaps:
            return "### Module Gaps\nCandidate has coverage across all modules."

        return "### Module Gaps (no missions attempted)\n" + "\n".join(gaps)
