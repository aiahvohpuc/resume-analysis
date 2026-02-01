"""OpenAI ChatGPT API client."""

import asyncio
import logging
from dataclasses import dataclass

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        if self.prompt_tokens == 0:
            return 0.0
        return (self.cached_tokens / self.prompt_tokens) * 100


class OpenAIClient:
    """Client for OpenAI ChatGPT API with prompt caching support.

    Uses sync client with asyncio.to_thread for better serverless compatibility.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> None:
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens in response (default: 2500)
        """
        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.last_usage: TokenUsage | None = None

    def _sync_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """Synchronous completion method."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)

        # Track token usage including cache hits
        if response.usage:
            cached = 0
            if hasattr(response.usage, "prompt_tokens_details"):
                details = response.usage.prompt_tokens_details
                if details and hasattr(details, "cached_tokens"):
                    cached = details.cached_tokens or 0

            self.last_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=cached,
            )

            # Log usage with cache info
            logger.info(
                f"Token usage: {self.last_usage.prompt_tokens} prompt, "
                f"{self.last_usage.completion_tokens} completion, "
                f"{self.last_usage.cached_tokens} cached "
                f"({self.last_usage.cache_hit_rate:.1f}% cache hit)"
            )

        return response.choices[0].message.content or ""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """Generate completion from OpenAI API.

        Uses asyncio.to_thread for serverless compatibility.

        Args:
            system_prompt: System message for context
            user_prompt: User message/prompt
            json_mode: Whether to request JSON response format

        Returns:
            Generated text response
        """
        return await asyncio.to_thread(
            self._sync_complete,
            system_prompt,
            user_prompt,
            json_mode,
        )
