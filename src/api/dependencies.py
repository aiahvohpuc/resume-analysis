"""FastAPI dependencies."""

from functools import lru_cache

from src.core.config import get_settings
from src.data.interview_manager import InterviewManager
from src.data.organization_manager import OrganizationManager
from src.data.position_manager import PositionManager
from src.services.feedback_analyzer import FeedbackAnalyzer
from src.services.llm_service import LLMService
from src.services.openai_client import OpenAIClient


@lru_cache
def get_organization_manager() -> OrganizationManager:
    """Get cached organization manager instance."""
    return OrganizationManager()


@lru_cache
def get_interview_manager() -> InterviewManager:
    """Get cached interview manager instance."""
    return InterviewManager()


@lru_cache
def get_position_manager() -> PositionManager:
    """Get cached position manager instance."""
    return PositionManager()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    settings = get_settings()
    client = OpenAIClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
    )
    return LLMService(client=client)


def get_feedback_analyzer() -> FeedbackAnalyzer:
    """Get feedback analyzer instance."""
    return FeedbackAnalyzer(
        llm_service=get_llm_service(),
        org_manager=get_organization_manager(),
        interview_manager=get_interview_manager(),
        position_manager=get_position_manager(),
    )
