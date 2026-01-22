"""Tests for Analyzer API endpoints (Phase 3)."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestSkillAnalysisEndpoint:
    """Test cases for skill analysis endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_analyze_skills_success(self, client: TestClient):
        """Test successful skill analysis."""
        response = client.post(
            "/api/analyze/skills",
            json={
                "text": "Python, JavaScript, React, PostgreSQL, AWS, Docker",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "summary" in data
        assert len(data["skills"]) > 0

    def test_analyze_skills_returns_categories(self, client: TestClient):
        """Test skill analysis returns categories."""
        response = client.post(
            "/api/analyze/skills",
            json={
                "text": "Python, React, PostgreSQL, AWS",
            },
        )
        data = response.json()
        categories = {skill["category"] for skill in data["skills"]}
        assert "programming_language" in categories
        assert "framework" in categories

    def test_analyze_skills_empty_text(self, client: TestClient):
        """Test skill analysis with empty text."""
        response = client.post(
            "/api/analyze/skills",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_analyze_skills_no_skills_found(self, client: TestClient):
        """Test skill analysis when no skills are found."""
        response = client.post(
            "/api/analyze/skills",
            json={"text": "안녕하세요. 저는 열심히 일하겠습니다."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == []

    def test_analyze_skills_with_requirements(self, client: TestClient):
        """Test skill analysis with job requirements matching."""
        response = client.post(
            "/api/analyze/skills",
            json={
                "text": "Python, FastAPI, PostgreSQL, Docker",
                "requirements": ["Python", "FastAPI", "Kubernetes", "AWS"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "match_result" in data
        assert "matched" in data["match_result"]
        assert "missing" in data["match_result"]
        assert "score" in data["match_result"]

    def test_analyze_skills_match_score_calculation(self, client: TestClient):
        """Test skill match score is correctly calculated."""
        response = client.post(
            "/api/analyze/skills",
            json={
                "text": "Python, FastAPI, PostgreSQL",
                "requirements": ["Python", "FastAPI", "PostgreSQL", "Kubernetes"],
            },
        )
        data = response.json()
        # 3 out of 4 matched = 75%
        assert data["match_result"]["score"] == 75.0


class TestSectionClassificationEndpoint:
    """Test cases for section classification endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_classify_sections_success(self, client: TestClient):
        """Test successful section classification."""
        response = client.post(
            "/api/analyze/sections",
            json={
                "text": """
                Professional Summary
                Experienced software engineer with 5 years of experience.

                Work Experience
                Software Engineer at TechCorp
                2020-2023

                Education
                BS Computer Science, Seoul National University

                Skills
                Python, JavaScript, Docker
                """,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert len(data["sections"]) > 0

    def test_classify_sections_returns_types(self, client: TestClient):
        """Test section classification returns correct types."""
        response = client.post(
            "/api/analyze/sections",
            json={
                "text": """
                Experience
                Developer at Company

                Education
                University Degree

                Skills
                Python
                """,
            },
        )
        data = response.json()
        section_types = [s["type"] for s in data["sections"]]
        assert "experience" in section_types
        assert "education" in section_types
        assert "skills" in section_types

    def test_classify_sections_empty_text(self, client: TestClient):
        """Test section classification with empty text."""
        response = client.post(
            "/api/analyze/sections",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_classify_sections_includes_content(self, client: TestClient):
        """Test section classification includes content."""
        response = client.post(
            "/api/analyze/sections",
            json={
                "text": """
                Experience
                Software Engineer at TechCorp for 3 years.
                """,
            },
        )
        data = response.json()
        assert len(data["sections"]) > 0
        assert "content" in data["sections"][0]
        assert "TechCorp" in data["sections"][0]["content"]


class TestResumeParseEndpoint:
    """Test cases for complete resume parsing endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_parse_resume_success(self, client: TestClient):
        """Test successful resume parsing."""
        response = client.post(
            "/api/analyze/resume",
            json={
                "text": """
                John Doe
                john.doe@email.com
                010-1234-5678

                Professional Summary
                Experienced developer with Python and React expertise.

                Work Experience
                Senior Developer at TechCorp
                2020-Present

                Education
                BS Computer Science, Seoul National University
                2015-2019

                Skills
                Python, JavaScript, React, FastAPI, PostgreSQL, Docker, AWS
                """,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert "skills" in data
        assert "skill_summary" in data

    def test_parse_resume_extracts_skills(self, client: TestClient):
        """Test resume parsing extracts skills."""
        response = client.post(
            "/api/analyze/resume",
            json={
                "text": """
                Skills
                Python, React, PostgreSQL, AWS, Docker
                """,
            },
        )
        data = response.json()
        skill_names = [s["name"].lower() for s in data["skills"]]
        assert "python" in skill_names
        assert "react" in skill_names

    def test_parse_resume_with_requirements(self, client: TestClient):
        """Test resume parsing with job requirements."""
        response = client.post(
            "/api/analyze/resume",
            json={
                "text": """
                Skills
                Python, FastAPI, PostgreSQL
                """,
                "job_requirements": ["Python", "FastAPI", "Kubernetes"],
            },
        )
        data = response.json()
        assert "match_result" in data
        assert data["match_result"]["score"] > 0

    def test_parse_resume_empty_text(self, client: TestClient):
        """Test resume parsing with empty text."""
        response = client.post(
            "/api/analyze/resume",
            json={"text": ""},
        )
        assert response.status_code == 422
