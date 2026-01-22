"""Tests for feedback analyzer (Phase 4)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.prompts import PromptBuilder
from src.schemas.request import ResumeAnalysisRequest
from src.schemas.response import ResumeAnalysisResponse
from src.services.feedback_analyzer import FeedbackAnalyzer


class TestPromptBuilder:
    """Test cases for PromptBuilder."""

    def test_build_system_prompt(self):
        """Test building system prompt."""
        org_data = {
            "name": "국민건강보험공단",
            "keywords": ["건강보험", "고객 중심"],
            "core_values": ["신뢰", "혁신"],
        }
        prompt = PromptBuilder.build_system_prompt(org_data)
        assert "국민건강보험공단" in prompt
        assert "건강보험" in prompt
        assert "신뢰" in prompt

    def test_build_user_prompt(self):
        """Test building user prompt."""
        request = ResumeAnalysisRequest(
            organization="NHIS",
            position="행정직",
            question="지원동기를 작성해주세요.",
            answer="저는 건강보험에 관심이 있습니다.",
            maxLength=500,
        )
        prompt = PromptBuilder.build_user_prompt(request)
        assert "행정직" in prompt
        assert "지원동기를 작성해주세요." in prompt
        assert "저는 건강보험에 관심이 있습니다." in prompt
        assert "500" in prompt

    def test_prompt_includes_json_format_instruction(self):
        """Test that system prompt includes JSON format instruction."""
        org_data = {"name": "Test", "keywords": [], "core_values": []}
        prompt = PromptBuilder.build_system_prompt(org_data)
        assert "JSON" in prompt


class TestFeedbackAnalyzer:
    """Test cases for FeedbackAnalyzer."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create mock LLM response."""
        return json.dumps(
            {
                "overall_score": 75,
                "length_check": {
                    "current": 50,
                    "max": 500,
                    "percentage": 10.0,
                    "status": "short",
                },
                "feedbacks": [
                    {
                        "category": "구체성",
                        "score": 6,
                        "comment": "더 구체적인 사례가 필요합니다.",
                        "suggestion": "실제 경험을 추가해보세요.",
                    }
                ],
                "keyword_analysis": {
                    "found_keywords": ["건강보험"],
                    "missing_keywords": ["고객 중심"],
                    "match_rate": 50.0,
                },
                "expected_questions": ["지원동기에 대해 더 설명해주세요."],
            }
        )

    @pytest.fixture
    def mock_llm_service(self, mock_llm_response):
        """Create mock LLM service."""
        service = AsyncMock()
        service.analyze = AsyncMock(return_value=mock_llm_response)
        return service

    @pytest.fixture
    def mock_org_manager(self):
        """Create mock organization manager."""
        manager = MagicMock()
        manager.get_organization = MagicMock(
            return_value={
                "code": "NHIS",
                "name": "국민건강보험공단",
                "keywords": ["건강보험", "고객 중심"],
                "core_values": ["신뢰", "혁신"],
            }
        )
        return manager

    @pytest.fixture
    def analyzer(self, mock_llm_service, mock_org_manager):
        """Create feedback analyzer."""
        return FeedbackAnalyzer(
            llm_service=mock_llm_service,
            org_manager=mock_org_manager,
        )

    @pytest.mark.asyncio
    async def test_analyze_resume(self, analyzer: FeedbackAnalyzer):
        """Test resume analysis."""
        answer = "저는 건강보험에 관심이 있습니다."
        request = ResumeAnalysisRequest(
            organization="NHIS",
            position="행정직",
            question="지원동기",
            answer=answer,
            maxLength=500,
        )
        response = await analyzer.analyze(request)
        assert isinstance(response, ResumeAnalysisResponse)
        assert response.overall_score == 75
        # Length is calculated from actual answer, not LLM response
        assert response.length_check.current == len(answer)

    @pytest.mark.asyncio
    async def test_analyze_calls_llm_with_json_mode(
        self, analyzer: FeedbackAnalyzer, mock_llm_service
    ):
        """Test that analyzer calls LLM with JSON mode."""
        request = ResumeAnalysisRequest(
            organization="NHIS",
            position="행정직",
            question="지원동기",
            answer="테스트",
        )
        await analyzer.analyze(request)
        mock_llm_service.analyze.assert_called_once()
        call_kwargs = mock_llm_service.analyze.call_args.kwargs
        assert call_kwargs.get("json_mode") is True

    @pytest.mark.asyncio
    async def test_analyze_fetches_organization_data(
        self, analyzer: FeedbackAnalyzer, mock_org_manager
    ):
        """Test that analyzer fetches organization data."""
        request = ResumeAnalysisRequest(
            organization="NHIS",
            position="행정직",
            question="지원동기",
            answer="테스트",
        )
        await analyzer.analyze(request)
        mock_org_manager.get_organization.assert_called_once_with("NHIS")

    @pytest.mark.asyncio
    async def test_calculate_length_check(self, analyzer: FeedbackAnalyzer):
        """Test length check calculation."""
        answer = "테스트 답변입니다."
        length_check = analyzer.calculate_length_check(
            answer=answer,
            max_length=100,
        )
        assert length_check.current == len(answer)  # 10 characters
        assert length_check.max == 100
        assert length_check.percentage == 10.0
        assert length_check.status == "short"

    def test_length_status_short(self, analyzer: FeedbackAnalyzer):
        """Test length status is 'short' when under 70%."""
        check = analyzer.calculate_length_check("테스트", 100)
        assert check.status == "short"

    def test_length_status_optimal(self, analyzer: FeedbackAnalyzer):
        """Test length status is 'optimal' when 70-100%."""
        check = analyzer.calculate_length_check("가" * 85, 100)
        assert check.status == "optimal"

    def test_length_status_over(self, analyzer: FeedbackAnalyzer):
        """Test length status is 'over' when over 100%."""
        check = analyzer.calculate_length_check("가" * 110, 100)
        assert check.status == "over"
