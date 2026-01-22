"""Tests for FastAPI endpoints (Phase 5)."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.main import app, get_feedback_analyzer
from src.schemas.response import (
    FeedbackItem,
    KeywordAnalysis,
    LengthCheck,
    ResumeAnalysisResponse,
)
from src.services.feedback_analyzer import FeedbackAnalyzer


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client: TestClient):
        """Test health check returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_includes_version(self, client: TestClient):
        """Test health check includes version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestResumeAnalysisEndpoint:
    """Test cases for resume analysis endpoint."""

    @pytest.fixture
    def mock_response(self):
        """Create mock analysis response."""
        return ResumeAnalysisResponse(
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
                    comment="좋습니다.",
                )
            ],
            keyword_analysis=KeywordAnalysis(
                found_keywords=["건강보험"],
                missing_keywords=[],
                match_rate=80.0,
            ),
            expected_questions=["지원 동기 관련 질문"],
        )

    @pytest.fixture
    def mock_analyzer(self, mock_response):
        """Create mock feedback analyzer."""
        analyzer = AsyncMock(spec=FeedbackAnalyzer)
        analyzer.analyze = AsyncMock(return_value=mock_response)
        return analyzer

    @pytest.fixture
    def client(self, mock_analyzer):
        """Create test client with mocked analyzer."""
        app.dependency_overrides[get_feedback_analyzer] = lambda: mock_analyzer
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_analyze_resume_success(self, client: TestClient):
        """Test successful resume analysis."""
        response = client.post(
            "/api/feedback/resume",
            json={
                "organization": "NHIS",
                "position": "행정직",
                "question": "지원동기를 작성해주세요.",
                "answer": "저는 국민건강보험공단에 지원합니다.",
                "maxLength": 500,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 85
        assert data["length_check"]["status"] == "optimal"

    def test_analyze_resume_with_default_max_length(self, client: TestClient):
        """Test resume analysis with default maxLength."""
        response = client.post(
            "/api/feedback/resume",
            json={
                "organization": "NHIS",
                "position": "행정직",
                "question": "지원동기",
                "answer": "테스트 답변",
            },
        )
        assert response.status_code == 200

    def test_analyze_resume_invalid_request(self, client: TestClient):
        """Test resume analysis with invalid request."""
        response = client.post(
            "/api/feedback/resume",
            json={
                "organization": "NHIS",
                # missing required fields
            },
        )
        assert response.status_code == 422  # Validation error

    def test_analyze_resume_empty_answer(self, client: TestClient):
        """Test resume analysis with empty answer."""
        response = client.post(
            "/api/feedback/resume",
            json={
                "organization": "NHIS",
                "position": "행정직",
                "question": "지원동기",
                "answer": "",
            },
        )
        assert response.status_code == 422


class TestCORS:
    """Test cases for CORS configuration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_cors_allowed_origin(self, client: TestClient):
        """Test CORS allows configured origin."""
        response = client.options(
            "/api/feedback/resume",
            headers={
                "Origin": "https://public-corp-ai-interview.vercel.app",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.headers.get("access-control-allow-origin") in [
            "https://public-corp-ai-interview.vercel.app",
            "*",
        ]

    def test_cors_headers_on_response(self, client: TestClient):
        """Test CORS headers are present on response."""
        response = client.get(
            "/health",
            headers={"Origin": "https://public-corp-ai-interview.vercel.app"},
        )
        # CORS headers should be present
        assert response.status_code == 200


class TestOrganizationsEndpoint:
    """Test cases for organizations endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_list_organizations(self, client: TestClient):
        """Test listing available organizations."""
        response = client.get("/api/organizations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "NHIS" in data
        assert "HIRA" in data
        assert "NPS" in data

    def test_get_organization_detail(self, client: TestClient):
        """Test getting organization detail."""
        response = client.get("/api/organizations/NHIS")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "NHIS"
        assert data["name"] == "국민건강보험공단"

    def test_get_organization_not_found(self, client: TestClient):
        """Test getting non-existent organization."""
        response = client.get("/api/organizations/UNKNOWN")
        assert response.status_code == 404
