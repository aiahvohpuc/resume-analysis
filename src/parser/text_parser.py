"""Text parser for resume content extraction."""

import re


class TextParser:
    """Parser for extracting structured data from resume text."""

    SECTION_KEYWORDS = {
        "experience": ["experience", "work history", "employment", "career"],
        "education": ["education", "academic", "degree", "university", "school"],
        "skills": ["skills", "technical skills", "competencies", "technologies"],
        "contact": ["contact", "personal information"],
        "summary": ["summary", "objective", "profile", "about"],
    }

    def parse(self, text: str) -> str:
        """Parse and clean raw text input.

        Args:
            text: Raw text content to parse.

        Returns:
            Cleaned and normalized text.
        """
        if not text:
            return ""
        return text.strip()

    def extract_sections(self, text: str) -> dict[str, str]:
        """Extract common resume sections from text.

        Args:
            text: Full resume text content.

        Returns:
            Dictionary mapping section names to their content.
        """
        sections = {}
        lines = text.split("\n")

        # Find section headers and their positions
        section_positions = []
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for section_name, keywords in self.SECTION_KEYWORDS.items():
                if any(kw in line_lower for kw in keywords):
                    section_positions.append((i, section_name))
                    break

        # If no explicit sections found, try to detect contact info at the top
        if not section_positions:
            # Assume header/contact is at the top
            sections["header"] = text.strip()
            return sections

        # Extract content between section headers
        for idx, (line_num, section_name) in enumerate(section_positions):
            if idx + 1 < len(section_positions):
                next_line_num = section_positions[idx + 1][0]
                content = "\n".join(lines[line_num:next_line_num])
            else:
                content = "\n".join(lines[line_num:])
            sections[section_name] = content.strip()

        # If contact section not found but we have content before first section
        if section_positions and section_positions[0][0] > 0:
            header_content = "\n".join(lines[: section_positions[0][0]])
            if header_content.strip():
                sections["header"] = header_content.strip()

        return sections

    def extract_contact_info(self, text: str) -> dict:
        """Extract contact information from text.

        Args:
            text: Text containing contact information.

        Returns:
            Dictionary with name, email, phone, and location.
        """
        result = {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
        }

        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

        # First non-empty line is usually the name
        if lines:
            result["name"] = lines[0]

        # Extract email using regex
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        email_match = re.search(email_pattern, text)
        if email_match:
            result["email"] = email_match.group()

        # Extract phone number (Korean and international formats)
        phone_pattern = r"(?:\+82|010|02|0\d{1,2})[-.\s]?\d{3,4}[-.\s]?\d{4}"
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            result["phone"] = phone_match.group()

        # Look for location keywords
        location_keywords = ["seoul", "busan", "korea", "서울", "부산", "대한민국"]
        for line in lines:
            if any(kw in line.lower() for kw in location_keywords):
                result["location"] = line
                break

        return result

    def extract_skills(self, text: str) -> list[str]:
        """Extract skills from text.

        Args:
            text: Text containing skills information.

        Returns:
            List of skill names.
        """
        # Remove section header if present
        lines = text.strip().split("\n")
        skill_text = ""
        for line in lines:
            line_lower = line.lower().strip()
            if not any(kw in line_lower for kw in ["skills", "기술"]):
                skill_text += line + " "

        # Split by common delimiters
        skills = re.split(r"[,;|•·]|\s{2,}", skill_text)
        skills = [s.strip() for s in skills if s.strip() and len(s.strip()) > 1]

        return skills
