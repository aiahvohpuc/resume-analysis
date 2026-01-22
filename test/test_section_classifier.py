"""Tests for SectionClassifier module."""

from src.analyzer.section_classifier import SectionClassifier, SectionType


class TestSectionType:
    """Tests for SectionType enum."""

    def test_section_types_exist(self):
        """Should have all required section types."""
        assert SectionType.CONTACT is not None
        assert SectionType.SUMMARY is not None
        assert SectionType.EXPERIENCE is not None
        assert SectionType.EDUCATION is not None
        assert SectionType.SKILLS is not None
        assert SectionType.UNKNOWN is not None

    def test_section_type_values(self):
        """Should have correct string values."""
        assert SectionType.CONTACT.value == "contact"
        assert SectionType.EXPERIENCE.value == "experience"
        assert SectionType.EDUCATION.value == "education"
        assert SectionType.SKILLS.value == "skills"


class TestSectionClassifier:
    """Tests for SectionClassifier class."""

    def test_create_classifier(self):
        """Should create a classifier instance."""
        classifier = SectionClassifier()
        assert classifier is not None

    def test_classify_experience_section(self):
        """Should classify experience-related text."""
        classifier = SectionClassifier()
        texts = [
            "Work Experience",
            "Professional Experience",
            "Employment History",
            "경력사항",
            "경력",
        ]
        for text in texts:
            result = classifier.classify(text)
            assert result == SectionType.EXPERIENCE, f"Failed for: {text}"

    def test_classify_education_section(self):
        """Should classify education-related text."""
        classifier = SectionClassifier()
        texts = [
            "Education",
            "Academic Background",
            "학력",
            "학력사항",
        ]
        for text in texts:
            result = classifier.classify(text)
            assert result == SectionType.EDUCATION, f"Failed for: {text}"

    def test_classify_skills_section(self):
        """Should classify skills-related text."""
        classifier = SectionClassifier()
        texts = [
            "Skills",
            "Technical Skills",
            "Core Competencies",
            "기술스택",
            "보유기술",
        ]
        for text in texts:
            result = classifier.classify(text)
            assert result == SectionType.SKILLS, f"Failed for: {text}"

    def test_classify_contact_section(self):
        """Should classify contact-related text."""
        classifier = SectionClassifier()
        texts = [
            "Contact Information",
            "Personal Information",
            "연락처",
            "인적사항",
        ]
        for text in texts:
            result = classifier.classify(text)
            assert result == SectionType.CONTACT, f"Failed for: {text}"

    def test_classify_summary_section(self):
        """Should classify summary-related text."""
        classifier = SectionClassifier()
        texts = [
            "Summary",
            "Professional Summary",
            "Objective",
            "Career Objective",
            "자기소개",
            "요약",
        ]
        for text in texts:
            result = classifier.classify(text)
            assert result == SectionType.SUMMARY, f"Failed for: {text}"

    def test_classify_unknown_section(self):
        """Should return UNKNOWN for unrecognized text."""
        classifier = SectionClassifier()
        result = classifier.classify("Random Text Here")
        assert result == SectionType.UNKNOWN

    def test_classify_case_insensitive(self):
        """Should classify regardless of case."""
        classifier = SectionClassifier()
        assert classifier.classify("EXPERIENCE") == SectionType.EXPERIENCE
        assert classifier.classify("experience") == SectionType.EXPERIENCE
        assert classifier.classify("Experience") == SectionType.EXPERIENCE

    def test_classify_document_sections(self):
        """Should classify all sections in a document."""
        classifier = SectionClassifier()
        document_lines = [
            "John Doe",
            "john@email.com",
            "",
            "Professional Summary",
            "Experienced developer...",
            "",
            "Work Experience",
            "Software Engineer at TechCorp",
            "",
            "Education",
            "BS in Computer Science",
            "",
            "Skills",
            "Python, JavaScript",
        ]

        sections = classifier.classify_document(document_lines)

        assert len(sections) > 0
        section_types = [s["type"] for s in sections]
        assert SectionType.SUMMARY in section_types
        assert SectionType.EXPERIENCE in section_types
        assert SectionType.EDUCATION in section_types
        assert SectionType.SKILLS in section_types

    def test_classify_document_returns_content(self):
        """Should return section content with classification."""
        classifier = SectionClassifier()
        document_lines = [
            "Work Experience",
            "Software Engineer at TechCorp",
            "2020-2023",
        ]

        sections = classifier.classify_document(document_lines)

        assert len(sections) == 1
        assert sections[0]["type"] == SectionType.EXPERIENCE
        assert "content" in sections[0]
        assert "Software Engineer" in sections[0]["content"]
