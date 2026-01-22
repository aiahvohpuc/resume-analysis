"""Tests for Resume data models."""

from src.models.resume import (
    ContactInfo,
    Education,
    Experience,
    Resume,
    Skill,
)


class TestContactInfo:
    """Tests for ContactInfo model."""

    def test_create_contact_info_with_required_fields(self):
        """Should create contact info with name only."""
        contact = ContactInfo(name="John Doe")
        assert contact.name == "John Doe"
        assert contact.email is None
        assert contact.phone is None

    def test_create_contact_info_with_all_fields(self):
        """Should create contact info with all fields."""
        contact = ContactInfo(
            name="Jane Smith",
            email="jane@example.com",
            phone="010-1234-5678",
            location="Seoul, Korea",
        )
        assert contact.name == "Jane Smith"
        assert contact.email == "jane@example.com"
        assert contact.phone == "010-1234-5678"
        assert contact.location == "Seoul, Korea"


class TestEducation:
    """Tests for Education model."""

    def test_create_education(self):
        """Should create education entry."""
        edu = Education(
            institution="Seoul National University",
            degree="Bachelor of Science",
            field="Computer Science",
            start_date="2015-03",
            end_date="2019-02",
        )
        assert edu.institution == "Seoul National University"
        assert edu.degree == "Bachelor of Science"
        assert edu.field == "Computer Science"

    def test_education_with_current_status(self):
        """Should handle currently enrolled status."""
        edu = Education(
            institution="KAIST",
            degree="Master of Science",
            field="AI",
            start_date="2023-03",
            is_current=True,
        )
        assert edu.is_current is True
        assert edu.end_date is None


class TestExperience:
    """Tests for Experience model."""

    def test_create_experience(self):
        """Should create work experience entry."""
        exp = Experience(
            company="Tech Corp",
            position="Software Engineer",
            start_date="2020-01",
            end_date="2023-12",
            description="Developed web applications",
            achievements=["Improved performance by 50%"],
        )
        assert exp.company == "Tech Corp"
        assert exp.position == "Software Engineer"
        assert len(exp.achievements) == 1

    def test_experience_current_job(self):
        """Should handle current employment."""
        exp = Experience(
            company="Startup Inc",
            position="Senior Developer",
            start_date="2024-01",
            is_current=True,
        )
        assert exp.is_current is True
        assert exp.end_date is None


class TestSkill:
    """Tests for Skill model."""

    def test_create_skill(self):
        """Should create skill entry."""
        skill = Skill(name="Python", category="Programming Language")
        assert skill.name == "Python"
        assert skill.category == "Programming Language"

    def test_skill_with_proficiency(self):
        """Should create skill with proficiency level."""
        skill = Skill(
            name="FastAPI",
            category="Framework",
            proficiency="Advanced",
        )
        assert skill.proficiency == "Advanced"


class TestResume:
    """Tests for Resume model."""

    def test_create_minimal_resume(self):
        """Should create resume with contact info only."""
        contact = ContactInfo(name="Test User")
        resume = Resume(contact=contact)
        assert resume.contact.name == "Test User"
        assert resume.education == []
        assert resume.experience == []
        assert resume.skills == []

    def test_create_full_resume(self):
        """Should create resume with all sections."""
        contact = ContactInfo(
            name="Full Resume User",
            email="user@test.com",
        )
        education = [
            Education(
                institution="University",
                degree="BS",
                field="CS",
                start_date="2015-03",
                end_date="2019-02",
            )
        ]
        experience = [
            Experience(
                company="Company",
                position="Developer",
                start_date="2019-03",
                is_current=True,
            )
        ]
        skills = [
            Skill(name="Python", category="Language"),
            Skill(name="FastAPI", category="Framework"),
        ]

        resume = Resume(
            contact=contact,
            education=education,
            experience=experience,
            skills=skills,
            summary="Experienced developer",
        )

        assert resume.contact.name == "Full Resume User"
        assert len(resume.education) == 1
        assert len(resume.experience) == 1
        assert len(resume.skills) == 2
        assert resume.summary == "Experienced developer"

    def test_resume_to_dict(self):
        """Should convert resume to dictionary."""
        contact = ContactInfo(name="Dict Test")
        resume = Resume(contact=contact)
        result = resume.model_dump()

        assert isinstance(result, dict)
        assert result["contact"]["name"] == "Dict Test"
