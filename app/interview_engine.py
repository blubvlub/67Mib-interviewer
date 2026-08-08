"""
Interview Engine — the core orchestrator.
Manages the full interview lifecycle: start, conversation turns, and feedback generation.
"""

from __future__ import annotations

import json
import logging
from app.models import CandidateProfile, InterviewResponse, Feedback
from app.session import SessionManager, SessionState
from app.candidate_analyzer import CandidateAnalyzer
from app.question_generator import QuestionGenerator
from app.llm_client import LLMClient
from app.prompts import (
    build_system_prompt,
    build_welcome_prompt,
    build_feedback_prompt,
)
from app.config import settings

logger = logging.getLogger(__name__)


class InterviewEngine:
    """Core interview orchestration engine."""

    def __init__(self):
        self.session_manager = SessionManager()
        self.llm = LLMClient()

    async def start_interview(
        self,
        session_id: str,
        candidate: CandidateProfile,
    ) -> InterviewResponse:
        """
        Initialize a new interview session.
        Analyzes the candidate, builds a question plan, and generates the welcome + first question.
        """
        # Analyze the candidate
        analyzer = CandidateAnalyzer(candidate)
        analysis = analyzer.analyze()
        curriculum_context = analyzer.get_curriculum_context()

        # Generate question plan
        question_gen = QuestionGenerator(analyzer, self.llm)
        question_plan = await question_gen.generate_plan()

        # Create session
        session = await self.session_manager.create_session(session_id, candidate)
        session.candidate_analysis = analysis
        session.curriculum_context = curriculum_context
        session.question_plan = question_plan

        # Generate welcome message + first question
        system_prompt = build_system_prompt(analysis, curriculum_context)
        welcome_prompt = build_welcome_prompt(
            candidate.member.name,
            candidate.member.jobRole,
        )

        reply = await self.llm.generate(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": welcome_prompt}],
            temperature=0.7,
        )

        # Track state
        session.conversation_history.append({"role": "assistant", "content": reply})
        session.questions_asked = 1

        # Track the first topic
        if question_plan:
            first_topic = question_plan[0]
            session.topics_covered.add(first_topic.get("day", 0))
            session.current_topic_index = 0

        await self.session_manager.update_session(session)

        logger.info(
            "Interview started: session=%s, candidate=%s, topics_planned=%d",
            session_id,
            candidate.member.name,
            len(question_plan),
        )

        return InterviewResponse(reply=reply, done=False)

    async def handle_turn(
        self,
        session_id: str,
        message: str,
    ) -> InterviewResponse:
        """
        Handle a conversation turn — process candidate's answer and generate next question.
        """
        session = await self.session_manager.get_session(session_id)
        if session is None:
            return InterviewResponse(
                reply="Session not found. Please start a new interview.",
                done=True,
            )

        if session.is_complete:
            return InterviewResponse(
                reply="This interview has already been completed.",
                done=True,
            )

        # Handle early termination from frontend
        if message.strip() == "FORCE_END_INTERVIEW":
            return await self._end_interview(session)

        # Add candidate's message to history
        session.conversation_history.append({"role": "user", "content": message})

        # Check if we should wrap up
        should_end = self._should_end_interview(session)

        if should_end:
            return await self._end_interview(session)

        # Generate next question
        system_prompt = build_system_prompt(
            session.candidate_analysis,
            session.curriculum_context,
        )

        # Build guidance for the next question
        guidance = self._build_turn_guidance(session)
        session.conversation_history.append(
            {"role": "user", "content": f"[INTERNAL — not from candidate]: {guidance}"}
        )

        reply = await self.llm.generate(
            system_prompt=system_prompt,
            messages=session.conversation_history,
            temperature=0.7,
        )

        # Remove the internal guidance from history and add the actual exchange
        session.conversation_history.pop()  # Remove guidance
        session.conversation_history.append({"role": "assistant", "content": reply})

        # Update tracking
        session.questions_asked += 1
        self._advance_topic(session)

        await self.session_manager.update_session(session)

        logger.info(
            "Turn completed: session=%s, questions=%d/%d, topics=%d",
            session_id,
            session.questions_asked,
            settings.MAX_QUESTIONS,
            len(session.topics_covered),
        )

        return InterviewResponse(reply=reply, done=False)

    async def _end_interview(self, session: SessionState) -> InterviewResponse:
        """Generate feedback and end the interview."""
        system_prompt = build_system_prompt(
            session.candidate_analysis,
            session.curriculum_context,
        )
        feedback_prompt = build_feedback_prompt()

        # Add feedback generation instruction
        messages = session.conversation_history + [
            {"role": "user", "content": feedback_prompt}
        ]

        feedback_json = await self.llm.generate_json(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
        )

        # Parse feedback
        try:
            feedback_data = json.loads(feedback_json)
            feedback = Feedback(
                summary=feedback_data.get("summary", "Interview completed."),
                strengths=feedback_data.get("strengths", []),
                gaps=feedback_data.get("gaps", []),
                next=feedback_data.get("next", []),
            )
        except (json.JSONDecodeError, Exception) as e:
            logger.error("Failed to parse feedback JSON: %s", e)
            feedback = Feedback(
                summary="Thank you for completing the interview. Your responses have been recorded.",
                strengths=["Completed the full interview"],
                gaps=["Unable to generate detailed feedback at this time"],
                next=["Review the curriculum materials", "Practice explaining technical concepts"],
            )

        # Generate a natural closing message
        closing = (
            f"Thank you for your time, {session.candidate.member.name}. "
            f"That concludes our interview. {feedback.summary}"
        )

        # Mark session complete
        session.is_complete = True
        session.conversation_history.append({"role": "assistant", "content": closing})
        await self.session_manager.update_session(session)

        logger.info(
            "Interview ended: session=%s, total_questions=%d, topics_covered=%d",
            session.session_id,
            session.questions_asked,
            len(session.topics_covered),
        )

        return InterviewResponse(reply=closing, done=True, feedback=feedback)

    def _should_end_interview(self, session: SessionState) -> bool:
        """Determine if the interview should end."""
        # Must have asked minimum questions
        if session.questions_asked < settings.MIN_QUESTIONS:
            return False

        # Must have covered minimum topics
        if len(session.topics_covered) < settings.MIN_TOPICS:
            return False

        # End if we've hit max questions
        if session.questions_asked >= settings.MAX_QUESTIONS:
            return True

        # End if we've covered all planned topics and met minimums
        if session.current_topic_index >= len(session.question_plan):
            return True

        return False

    def _build_turn_guidance(self, session: SessionState) -> str:
        """Build internal guidance for the LLM about what to ask next."""
        questions_left = settings.MAX_QUESTIONS - session.questions_asked
        topics_covered = len(session.topics_covered)
        min_topics_left = max(0, settings.MIN_TOPICS - topics_covered)

        guidance_parts = [
            f"Questions asked so far: {session.questions_asked}",
            f"Questions remaining: {questions_left}",
            f"Topics covered: {topics_covered}",
        ]

        # Suggest next topic if available
        if session.current_topic_index < len(session.question_plan):
            next_topic = session.question_plan[session.current_topic_index]
            guidance_parts.append(
                f"Suggested next topic: {next_topic.get('title', 'Unknown')} "
                f"(Priority: {next_topic.get('priority', 'medium')}, "
                f"Reason: {next_topic.get('reason', 'N/A')})"
            )
            suggested_qs = next_topic.get("suggested_questions", [])
            if suggested_qs:
                guidance_parts.append(f"Suggested questions: {suggested_qs[0]}")

        if min_topics_left > 0:
            guidance_parts.append(
                f"IMPORTANT: Still need to cover {min_topics_left} more different topics."
            )

        if questions_left <= 2:
            guidance_parts.append(
                "IMPORTANT: This is one of the last questions. "
                "Begin wrapping up the interview naturally."
            )

        return (
            "Based on the candidate's previous response, react naturally and ask your next question. "
            + " | ".join(guidance_parts)
        )

    def _advance_topic(self, session: SessionState) -> None:
        """
        Advance to the next topic if appropriate.
        Move on every 2 questions or if topic is exhausted.
        """
        if session.questions_asked % 2 == 0 and session.current_topic_index < len(session.question_plan):
            # Mark current topic as covered
            current = session.question_plan[session.current_topic_index]
            session.topics_covered.add(current.get("day", session.current_topic_index))
            session.current_topic_index += 1

            # Also mark new topic as covered
            if session.current_topic_index < len(session.question_plan):
                next_topic = session.question_plan[session.current_topic_index]
                session.topics_covered.add(next_topic.get("day", session.current_topic_index))
