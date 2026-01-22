"""Section classifier for resume documents."""

from enum import Enum


class SectionType(Enum):
    """Types of resume sections."""

    CONTACT = "contact"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    UNKNOWN = "unknown"


class SectionClassifier:
    """Classifier for identifying resume section types."""

    SECTION_KEYWORDS: dict[SectionType, list[str]] = {
        SectionType.CONTACT: [
            "contact",
            "personal information",
            "연락처",
            "인적사항",
            "personal details",
        ],
        SectionType.SUMMARY: [
            "summary",
            "professional summary",
            "objective",
            "career objective",
            "profile",
            "about",
            "자기소개",
            "요약",
            "소개",
        ],
        SectionType.EXPERIENCE: [
            "experience",
            "work experience",
            "professional experience",
            "employment",
            "employment history",
            "work history",
            "career history",
            "경력",
            "경력사항",
            "직무경험",
        ],
        SectionType.EDUCATION: [
            "education",
            "academic",
            "academic background",
            "educational background",
            "학력",
            "학력사항",
        ],
        SectionType.SKILLS: [
            "skills",
            "technical skills",
            "core competencies",
            "competencies",
            "technologies",
            "tech stack",
            "기술",
            "기술스택",
            "보유기술",
            "스킬",
        ],
        SectionType.PROJECTS: [
            "projects",
            "personal projects",
            "프로젝트",
        ],
        SectionType.CERTIFICATIONS: [
            "certifications",
            "certificates",
            "licenses",
            "자격증",
        ],
    }

    def classify(self, text: str) -> SectionType:
        """Classify a single line of text as a section type.

        Args:
            text: Text to classify (usually a section header).

        Returns:
            The identified SectionType.
        """
        text_lower = text.lower().strip()

        for section_type, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return section_type

        return SectionType.UNKNOWN

    def classify_document(self, lines: list[str]) -> list[dict]:
        """Classify all sections in a document.

        Args:
            lines: List of document lines.

        Returns:
            List of dictionaries containing section type and content.
        """
        sections = []
        current_section = None
        current_content = []

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines at the start
            if not line_stripped and current_section is None:
                continue

            # Check if this line is a section header
            section_type = self.classify(line_stripped)

            if section_type != SectionType.UNKNOWN:
                # Save previous section if exists
                if current_section is not None:
                    sections.append({
                        "type": current_section,
                        "content": "\n".join(current_content).strip(),
                    })

                # Start new section
                current_section = section_type
                current_content = []
            elif current_section is not None:
                # Add content to current section
                current_content.append(line)

        # Save last section
        if current_section is not None and current_content:
            sections.append({
                "type": current_section,
                "content": "\n".join(current_content).strip(),
            })

        return sections
