"""Tests for Pydantic schemas (Phase 1)."""

import pytest
from pydantic import ValidationError
from src.schemas.request import ResumeAnalysisRequest
from src.schemas.response import (
    FeedbackItem,
    KeywordAnalysis,
    LengthCheck,
    ResumeAnalysisResponse,
)


class TestResumeAnalysisRequest:
    """Test cases for ResumeAnalysisRequest schema."""

    def test_valid_request(self):
        """Test creating a valid request."""
        request = ResumeAnalysisRequest(
            organization="NHIS",
            position="행정직",
            question="지원동기를 작성해주세요.",
            answer="저는 국민건강보험공단에 지원하게 된 이유는...",
            maxLength=500,
        )
        assert request.organization == "NHIS"
        assert request.position == "행정직"
        assert request.question == "지원동기를 작성해주세요."
        assert request.answer == "저는 국민건강보험공단에 지원하게 된 이유는..."
        assert request.maxLength == 500

    def test_request_with_default_max_length(self):
        """Test request with default maxLength value."""
        request = ResumeAnalysisRequest(
            organization="HIRA",
            position="전산직",
            question="본인의 강점을 작성해주세요.",
            answer="저의 강점은...",
        )
        assert request.maxLength == 1000  # default value

    def test_request_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ResumeAnalysisRequest(
                organization="NHIS",
                position="행정직",
                # missing question and answer
            )

    def test_request_empty_answer(self):
        """Test that empty answer raises ValidationError."""
        with pytest.raises(ValidationError):
            ResumeAnalysisRequest(
                organization="NHIS",
                position="행정직",
                question="지원동기",
                answer="",  # empty
                maxLength=500,
            )

    def test_request_max_length_validation(self):
        """Test that maxLength must be positive."""
        with pytest.raises(ValidationError):
            ResumeAnalysisRequest(
                organization="NHIS",
                position="행정직",
                question="지원동기",
                answer="테스트",
                maxLength=0,
            )

    def test_request_organization_whitespace_stripped(self):
        """Test that organization name is stripped of whitespace."""
        request = ResumeAnalysisRequest(
            organization="  NHIS  ",
            position="행정직",
            question="지원동기",
            answer="테스트 답변",
        )
        assert request.organization == "NHIS"


class TestLengthCheck:
    """Test cases for LengthCheck schema."""

    def test_length_check_valid(self):
        """Test valid length check response."""
        check = LengthCheck(
            current=450,
            max=500,
            percentage=90.0,
            status="optimal",
        )
        assert check.current == 450
        assert check.max == 500
        assert check.percentage == 90.0
        assert check.status == "optimal"

    def test_length_check_status_values(self):
        """Test different status values."""
        for status in ["short", "optimal", "over"]:
            check = LengthCheck(current=100, max=500, percentage=20.0, status=status)
            assert check.status == status


class TestFeedbackItem:
    """Test cases for FeedbackItem schema."""

    def test_feedback_item_valid(self):
        """Test valid feedback item."""
        feedback = FeedbackItem(
            category="구체성",
            score=8,
            comment="지원 동기가 구체적으로 잘 작성되었습니다.",
            suggestion="더 구체적인 사례를 추가하면 좋겠습니다.",
        )
        assert feedback.category == "구체성"
        assert feedback.score == 8
        assert feedback.comment == "지원 동기가 구체적으로 잘 작성되었습니다."
        assert feedback.suggestion == "더 구체적인 사례를 추가하면 좋겠습니다."

    def test_feedback_item_score_range(self):
        """Test that score must be between 1 and 10."""
        with pytest.raises(ValidationError):
            FeedbackItem(
                category="구체성",
                score=0,  # invalid: below 1
                comment="테스트",
            )
        with pytest.raises(ValidationError):
            FeedbackItem(
                category="구체성",
                score=11,  # invalid: above 10
                comment="테스트",
            )

    def test_feedback_item_optional_suggestion(self):
        """Test that suggestion is optional."""
        feedback = FeedbackItem(
            category="구체성",
            score=8,
            comment="좋습니다.",
        )
        assert feedback.suggestion is None


class TestKeywordAnalysis:
    """Test cases for KeywordAnalysis schema."""

    def test_keyword_analysis_valid(self):
        """Test valid keyword analysis."""
        analysis = KeywordAnalysis(
            found_keywords=["고객 중심", "디지털 혁신"],
            missing_keywords=["협업", "문제 해결"],
            match_rate=60.0,
        )
        assert analysis.found_keywords == ["고객 중심", "디지털 혁신"]
        assert analysis.missing_keywords == ["협업", "문제 해결"]
        assert analysis.match_rate == 60.0

    def test_keyword_analysis_empty_lists(self):
        """Test keyword analysis with empty lists."""
        analysis = KeywordAnalysis(
            found_keywords=[],
            missing_keywords=["협업"],
            match_rate=0.0,
        )
        assert analysis.found_keywords == []


class TestResumeAnalysisResponse:
    """Test cases for ResumeAnalysisResponse schema."""

    def test_response_valid(self):
        """Test valid complete response."""
        response = ResumeAnalysisResponse(
            overall_score=85,
            length_check=LengthCheck(
                current=450,
                max=500,
                percentage=90.0,
                status="optimal",
            ),
            feedbacks=[
                FeedbackItem(
                    category="구체성",
                    score=8,
                    comment="잘 작성되었습니다.",
                ),
            ],
            keyword_analysis=KeywordAnalysis(
                found_keywords=["고객 중심"],
                missing_keywords=[],
                match_rate=80.0,
            ),
            expected_questions=["지원 동기에 대해 더 자세히 설명해주세요."],
        )
        assert response.overall_score == 85
        assert response.length_check.current == 450
        assert len(response.feedbacks) == 1
        assert response.keyword_analysis.match_rate == 80.0
        assert len(response.expected_questions) == 1

    def test_response_overall_score_range(self):
        """Test that overall_score must be between 0 and 100."""
        with pytest.raises(ValidationError):
            ResumeAnalysisResponse(
                overall_score=-1,  # invalid
                length_check=LengthCheck(current=100, max=500, percentage=20.0, status="short"),
                feedbacks=[],
                keyword_analysis=KeywordAnalysis(
                    found_keywords=[], missing_keywords=[], match_rate=0.0
                ),
                expected_questions=[],
            )

    def test_response_serialization(self):
        """Test response serialization to dict."""
        response = ResumeAnalysisResponse(
            overall_score=75,
            length_check=LengthCheck(current=400, max=500, percentage=80.0, status="optimal"),
            feedbacks=[],
            keyword_analysis=KeywordAnalysis(
                found_keywords=[], missing_keywords=[], match_rate=0.0
            ),
            expected_questions=[],
        )
        data = response.model_dump()
        assert data["overall_score"] == 75
        assert data["length_check"]["current"] == 400
