"""LLM service abstraction layer."""

from typing import Protocol


class LLMClientProtocol(Protocol):
    """Protocol for LLM client implementations."""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """Generate completion from LLM."""
        ...


class LLMService:
    """Abstraction layer for LLM operations."""

    def __init__(self, client: LLMClientProtocol) -> None:
        """Initialize LLM service.

        Args:
            client: LLM client implementation (e.g., OpenAIClient)
        """
        self._client = client

    async def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """Analyze content using LLM.

        Args:
            system_prompt: System context/instructions
            user_prompt: Content to analyze
            json_mode: Request JSON formatted response

        Returns:
            LLM generated response
        """
        return await self._client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=json_mode,
        )
