"""Tests for SkillExtractor module."""


from src.analyzer.skill_extractor import SkillCategory, SkillExtractor


class TestSkillCategory:
    """Tests for SkillCategory enum."""

    def test_skill_categories_exist(self):
        """Should have all required skill categories."""
        assert SkillCategory.PROGRAMMING_LANGUAGE is not None
        assert SkillCategory.FRAMEWORK is not None
        assert SkillCategory.DATABASE is not None
        assert SkillCategory.CLOUD is not None
        assert SkillCategory.TOOL is not None
        assert SkillCategory.SOFT_SKILL is not None
        assert SkillCategory.OTHER is not None


class TestSkillExtractor:
    """Tests for SkillExtractor class."""

    def test_create_extractor(self):
        """Should create an extractor instance."""
        extractor = SkillExtractor()
        assert extractor is not None

    def test_extract_programming_languages(self):
        """Should extract programming languages from text."""
        extractor = SkillExtractor()
        text = "Proficient in Python, JavaScript, and TypeScript"

        skills = extractor.extract(text)

        skill_names = [s["name"].lower() for s in skills]
        assert "python" in skill_names
        assert "javascript" in skill_names
        assert "typescript" in skill_names

    def test_extract_frameworks(self):
        """Should extract frameworks from text."""
        extractor = SkillExtractor()
        text = "Experience with React, FastAPI, Django, and Node.js"

        skills = extractor.extract(text)

        skill_names = [s["name"].lower() for s in skills]
        assert "react" in skill_names
        assert "fastapi" in skill_names
        assert "django" in skill_names

    def test_extract_databases(self):
        """Should extract database technologies from text."""
        extractor = SkillExtractor()
        text = "Database: PostgreSQL, MySQL, MongoDB, Redis"

        skills = extractor.extract(text)

        skill_names = [s["name"].lower() for s in skills]
        assert "postgresql" in skill_names
        assert "mongodb" in skill_names

    def test_extract_cloud_services(self):
        """Should extract cloud services from text."""
        extractor = SkillExtractor()
        text = "Cloud: AWS, GCP, Azure, Docker, Kubernetes"

        skills = extractor.extract(text)

        skill_names = [s["name"].lower() for s in skills]
        assert "aws" in skill_names
        assert "docker" in skill_names
        assert "kubernetes" in skill_names

    def test_extract_returns_category(self):
        """Should return category for each skill."""
        extractor = SkillExtractor()
        text = "Python, React, PostgreSQL, AWS"

        skills = extractor.extract(text)

        for skill in skills:
            assert "category" in skill
            assert isinstance(skill["category"], SkillCategory)

    def test_categorize_skill(self):
        """Should correctly categorize individual skills."""
        extractor = SkillExtractor()

        assert extractor.categorize("Python") == SkillCategory.PROGRAMMING_LANGUAGE
        assert extractor.categorize("React") == SkillCategory.FRAMEWORK
        assert extractor.categorize("PostgreSQL") == SkillCategory.DATABASE
        assert extractor.categorize("AWS") == SkillCategory.CLOUD
        assert extractor.categorize("Git") == SkillCategory.TOOL

    def test_extract_from_comma_separated(self):
        """Should extract skills from comma-separated list."""
        extractor = SkillExtractor()
        text = "Python, Java, C++, Go, Rust"

        skills = extractor.extract(text)

        assert len(skills) >= 5

    def test_extract_from_bullet_list(self):
        """Should extract skills from bullet point list."""
        extractor = SkillExtractor()
        text = """
        • Python
        • JavaScript
        • Docker
        • Kubernetes
        """

        skills = extractor.extract(text)

        skill_names = [s["name"].lower() for s in skills]
        assert "python" in skill_names
        assert "javascript" in skill_names
        assert "docker" in skill_names

    def test_extract_handles_duplicates(self):
        """Should not return duplicate skills."""
        extractor = SkillExtractor()
        text = "Python, Python, python, PYTHON"

        skills = extractor.extract(text)

        python_count = sum(
            1 for s in skills if s["name"].lower() == "python"
        )
        assert python_count == 1

    def test_extract_korean_skills(self):
        """Should handle Korean skill descriptions."""
        extractor = SkillExtractor()
        text = "프로그래밍: Python, Java / 프레임워크: Spring, FastAPI"

        skills = extractor.extract(text)

        skill_names = [s["name"].lower() for s in skills]
        assert "python" in skill_names
        assert "java" in skill_names

    def test_match_skills_with_job_requirements(self):
        """Should match extracted skills with job requirements."""
        extractor = SkillExtractor()
        resume_text = "Python, FastAPI, PostgreSQL, Docker, AWS"
        job_requirements = ["Python", "FastAPI", "PostgreSQL", "Kubernetes", "CI/CD"]

        result = extractor.match_requirements(resume_text, job_requirements)

        assert "matched" in result
        assert "missing" in result
        assert "python" in [s.lower() for s in result["matched"]]
        assert "kubernetes" in [s.lower() for s in result["missing"]]

    def test_calculate_skill_match_score(self):
        """Should calculate skill match percentage."""
        extractor = SkillExtractor()
        resume_text = "Python, FastAPI, PostgreSQL"
        job_requirements = ["Python", "FastAPI", "PostgreSQL", "Kubernetes"]

        result = extractor.match_requirements(resume_text, job_requirements)

        assert "score" in result
        assert result["score"] == 75.0  # 3 out of 4 matched

    def test_get_skill_summary(self):
        """Should return skill summary by category."""
        extractor = SkillExtractor()
        text = "Python, JavaScript, React, Django, PostgreSQL, AWS, Docker"

        summary = extractor.get_summary(text)

        assert isinstance(summary, dict)
        assert SkillCategory.PROGRAMMING_LANGUAGE in summary
        assert SkillCategory.FRAMEWORK in summary
        assert SkillCategory.DATABASE in summary
        assert SkillCategory.CLOUD in summary
