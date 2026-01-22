"""Resume data models using Pydantic."""

from pydantic import BaseModel


class ContactInfo(BaseModel):
    """Contact information section of a resume."""

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None


class Education(BaseModel):
    """Education entry in a resume."""

    institution: str
    degree: str
    field: str
    start_date: str
    end_date: str | None = None
    is_current: bool = False


class Experience(BaseModel):
    """Work experience entry in a resume."""

    company: str
    position: str
    start_date: str
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    achievements: list[str] = []


class Skill(BaseModel):
    """Skill entry in a resume."""

    name: str
    category: str
    proficiency: str | None = None


class Resume(BaseModel):
    """Complete resume data model."""

    contact: ContactInfo
    education: list[Education] = []
    experience: list[Experience] = []
    skills: list[Skill] = []
    summary: str | None = None
