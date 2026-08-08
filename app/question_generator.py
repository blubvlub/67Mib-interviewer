"""
Question generator that builds an interview plan based on
candidate analysis and curriculum data.
"""

from __future__ import annotations

import json
import logging
from app.candidate_analyzer import CandidateAnalyzer
from app.llm_client import LLMClient
from app.prompts import build_question_plan_prompt
from app.config import settings

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Generates a prioritized interview question plan.
    Uses candidate analysis to select topics and the LLM to suggest questions.
    """

    def __init__(self, analyzer: CandidateAnalyzer, llm: LLMClient):
        self.analyzer = analyzer
        self.llm = llm

    async def generate_plan(self) -> list[dict]:
        """
        Generate an interview question plan.
        Returns a list of topic dicts with suggested questions.
        """
        # Get prioritized topics from the analyzer
        topic_priorities = self.analyzer.get_topic_priorities()

        # Select topics ensuring minimum coverage
        selected = self._select_topics(topic_priorities)

        # Use LLM to generate tailored questions for selected topics
        try:
            plan = await self._llm_generate_plan(selected)
            return plan
        except Exception as e:
            logger.warning("LLM plan generation failed, using fallback: %s", e)
            return self._fallback_plan(selected)

    def _select_topics(self, priorities: list[dict]) -> list[dict]:
        """
        Select topics ensuring at least MIN_TOPICS different days
        and enough for MIN_QUESTIONS total.
        """
        selected = []
        modules_covered = set()

        # First pass: take all high-priority topics
        for topic in priorities:
            if topic["priority"] == "high":
                selected.append(topic)
                modules_covered.add(topic["module"])

        # Second pass: add medium-priority from uncovered modules
        for topic in priorities:
            if topic["priority"] == "medium" and topic["module"] not in modules_covered:
                selected.append(topic)
                modules_covered.add(topic["module"])

        # Third pass: fill up if we don't have enough topics
        for topic in priorities:
            if len(selected) >= settings.MIN_TOPICS + 2:
                break
            if topic not in selected:
                selected.append(topic)

        # Ensure minimum topics
        if len(selected) < settings.MIN_TOPICS:
            for topic in priorities:
                if topic not in selected:
                    selected.append(topic)
                    if len(selected) >= settings.MIN_TOPICS:
                        break

        return selected

    async def _llm_generate_plan(self, topics: list[dict]) -> list[dict]:
        """Use LLM to generate contextual questions for selected topics."""
        candidate_analysis = self.analyzer.analyze()
        curriculum_context = self.analyzer.get_curriculum_context()

        prompt = build_question_plan_prompt(candidate_analysis, curriculum_context)
        topics_summary = json.dumps(
            [{"day": t["day"], "title": t["title"], "priority": t["priority"],
              "reason": t["reason"]} for t in topics],
            indent=2
        )

        response = await self.llm.generate_json(
            system_prompt=prompt,
            messages=[{
                "role": "user",
                "content": f"Generate questions for these selected topics:\n{topics_summary}"
            }],
            temperature=0.8,
            max_tokens=2048,
        )

        try:
            plan = json.loads(response)
            return plan.get("topics", topics)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM question plan JSON")
            return self._fallback_plan(topics)

    def _fallback_plan(self, topics: list[dict]) -> list[dict]:
        """
        Fallback question plan if LLM generation fails.
        Uses topic objectives to create generic questions.
        """
        plan = []
        for topic in topics:
            objectives = topic.get("objectives", [])
            questions = []
            for obj in objectives[:2]:
                questions.append(f"Can you explain your understanding of: {obj}?")
            if not questions:
                questions.append(f"Tell me about your experience with {topic['title']}.")

            plan.append({
                "day": topic["day"],
                "title": topic["title"],
                "priority": topic["priority"],
                "reason": topic["reason"],
                "suggested_questions": questions,
            })
        return plan
