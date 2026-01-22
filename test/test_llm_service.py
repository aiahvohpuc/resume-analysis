"""Tests for LLM service (Phase 3)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.services.llm_service import LLMService
from src.services.openai_client import OpenAIClient


class TestOpenAIClient:
    """Test cases for OpenAIClient."""

    @pytest.fixture
    def mock_openai_response(self):
        """Create mock OpenAI response."""
        mock_choice = MagicMock()
        mock_choice.message.content = '{"test": "response"}'

        # Mock token usage with cache details
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        mock_usage.prompt_tokens_details = MagicMock()
        mock_usage.prompt_tokens_details.cached_tokens = 50

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        return mock_response

    @pytest.fixture
    def client(self):
        """Create OpenAI client with test API key."""
        return OpenAIClient(api_key="test-api-key", model="gpt-4o-mini")

    def test_client_initialization(self, client: OpenAIClient):
        """Test client initialization."""
        assert client.model == "gpt-4o-mini"

    def test_client_initialization_default_model(self):
        """Test client initialization with default model."""
        client = OpenAIClient(api_key="test-api-key")
        assert client.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_complete_success(self, client: OpenAIClient, mock_openai_response):
        """Test successful completion."""
        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_openai_response,
        ):
            result = await client.complete(
                system_prompt="You are a helpful assistant.",
                user_prompt="Test prompt",
            )
            assert result == '{"test": "response"}'

    @pytest.mark.asyncio
    async def test_complete_with_json_mode(self, client: OpenAIClient, mock_openai_response):
        """Test completion with JSON response format."""
        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_openai_response,
        ) as mock_create:
            await client.complete(
                system_prompt="You are a helpful assistant.",
                user_prompt="Test prompt",
                json_mode=True,
            )
            # Verify JSON mode was set
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs.get("response_format") == {"type": "json_object"}


class TestLLMService:
    """Test cases for LLMService abstraction layer."""

    @pytest.fixture
    def mock_client(self):
        """Create mock LLM client."""
        client = AsyncMock()
        client.complete = AsyncMock(return_value='{"analysis": "test"}')
        return client

    @pytest.fixture
    def service(self, mock_client):
        """Create LLM service with mock client."""
        return LLMService(client=mock_client)

    @pytest.mark.asyncio
    async def test_analyze_resume(self, service: LLMService):
        """Test resume analysis."""
        result = await service.analyze(
            system_prompt="Analyze this resume.",
            user_prompt="Resume content here.",
        )
        assert result == '{"analysis": "test"}'

    @pytest.mark.asyncio
    async def test_analyze_with_json_mode(self, service: LLMService, mock_client):
        """Test analysis with JSON mode enabled."""
        await service.analyze(
            system_prompt="Analyze this.",
            user_prompt="Content.",
            json_mode=True,
        )
        mock_client.complete.assert_called_once()
        call_kwargs = mock_client.complete.call_args.kwargs
        assert call_kwargs.get("json_mode") is True

    @pytest.mark.asyncio
    async def test_analyze_returns_string(self, service: LLMService):
        """Test that analyze returns string response."""
        result = await service.analyze(
            system_prompt="Test",
            user_prompt="Test",
        )
        assert isinstance(result, str)
