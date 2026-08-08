"""
Groq LLM client wrapper.
Handles API calls, retries, and error management.
"""

import logging
from groq import AsyncGroq, APIError, RateLimitError
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around the Groq SDK for LLM inference."""

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set. Add it to your .env file. "
                "Get a free key at https://console.groq.com"
            )
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL_NAME

    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: The system-level instruction.
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            The assistant's response text.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature or settings.MODEL_TEMPERATURE,
                max_tokens=max_tokens or settings.MODEL_MAX_TOKENS,
            )
            content = response.choices[0].message.content
            
            # Strip out DeepSeek reasoning tags if using a thinking model
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
            logger.debug(
                "LLM response: model=%s, tokens_used=%d",
                self.model,
                response.usage.total_tokens if response.usage else 0,
            )
            return content

        except RateLimitError as e:
            logger.warning("Groq rate limit hit: %s", e)
            raise RuntimeError(
                "The AI model is temporarily rate-limited. Please wait a moment and try again."
            ) from e

        except APIError as e:
            logger.error("Groq API error: %s", e)
            raise RuntimeError(
                "Failed to get a response from the AI model. Please try again."
            ) from e

    async def generate_json(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a JSON response from the LLM using JSON mode.
        Returns raw JSON string for the caller to parse.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature or settings.MODEL_TEMPERATURE,
                max_tokens=max_tokens or settings.MODEL_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            
            # Strip out DeepSeek reasoning tags if using a thinking model
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
            logger.debug(
                "LLM JSON response: model=%s, tokens_used=%d",
                self.model,
                response.usage.total_tokens if response.usage else 0,
            )
            return content

        except RateLimitError as e:
            logger.warning("Groq rate limit hit: %s", e)
            raise RuntimeError(
                "The AI model is temporarily rate-limited. Please wait a moment and try again."
            ) from e

        except APIError as e:
            logger.error("Groq API error: %s", e)
            raise RuntimeError(
                "Failed to get a response from the AI model. Please try again."
            ) from e
