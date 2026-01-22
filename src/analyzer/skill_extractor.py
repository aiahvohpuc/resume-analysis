"""Skill extractor for resume analysis."""

import re
from enum import Enum


class SkillCategory(Enum):
    """Categories for technical and soft skills."""

    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"
    OTHER = "other"


class SkillExtractor:
    """Extractor for identifying and categorizing skills from text."""

    SKILL_DATABASE: dict[SkillCategory, list[str]] = {
        SkillCategory.PROGRAMMING_LANGUAGE: [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "c#",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "r",
            "matlab",
            "perl",
            "lua",
            "dart",
            "elixir",
            "haskell",
            "clojure",
        ],
        SkillCategory.FRAMEWORK: [
            "react",
            "vue",
            "angular",
            "svelte",
            "next.js",
            "nuxt",
            "fastapi",
            "django",
            "flask",
            "spring",
            "spring boot",
            "express",
            "nest.js",
            "node.js",
            "rails",
            "laravel",
            "asp.net",
            ".net",
            "pytorch",
            "tensorflow",
            "keras",
        ],
        SkillCategory.DATABASE: [
            "postgresql",
            "mysql",
            "mariadb",
            "mongodb",
            "redis",
            "elasticsearch",
            "cassandra",
            "dynamodb",
            "sqlite",
            "oracle",
            "sql server",
            "neo4j",
            "cockroachdb",
            "influxdb",
        ],
        SkillCategory.CLOUD: [
            "aws",
            "gcp",
            "azure",
            "docker",
            "kubernetes",
            "terraform",
            "ansible",
            "jenkins",
            "github actions",
            "gitlab ci",
            "circleci",
            "heroku",
            "vercel",
            "netlify",
            "cloudflare",
        ],
        SkillCategory.TOOL: [
            "git",
            "github",
            "gitlab",
            "bitbucket",
            "jira",
            "confluence",
            "slack",
            "notion",
            "figma",
            "postman",
            "insomnia",
            "vscode",
            "intellij",
            "vim",
            "linux",
            "bash",
            "powershell",
        ],
        SkillCategory.SOFT_SKILL: [
            "leadership",
            "communication",
            "teamwork",
            "problem solving",
            "critical thinking",
            "time management",
            "agile",
            "scrum",
            "project management",
        ],
    }

    def __init__(self):
        """Initialize the skill extractor with a reverse lookup map."""
        self._skill_to_category: dict[str, SkillCategory] = {}
        for category, skills in self.SKILL_DATABASE.items():
            for skill in skills:
                self._skill_to_category[skill.lower()] = category

    def categorize(self, skill: str) -> SkillCategory:
        """Categorize a single skill.

        Args:
            skill: Skill name to categorize.

        Returns:
            The skill category.
        """
        skill_lower = skill.lower().strip()
        return self._skill_to_category.get(skill_lower, SkillCategory.OTHER)

    def extract(self, text: str) -> list[dict]:
        """Extract skills from text.

        Args:
            text: Text containing skill information.

        Returns:
            List of dictionaries with skill name and category.
        """
        text_lower = text.lower()
        found_skills: dict[str, dict] = {}

        # Search for each known skill in the text
        for category, skills in self.SKILL_DATABASE.items():
            for skill in skills:
                # Use lookahead/lookbehind for boundary matching
                # Works better with special characters like C++
                escaped = re.escape(skill)
                pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
                if re.search(pattern, text_lower, re.IGNORECASE):
                    skill_key = skill.lower()
                    if skill_key not in found_skills:
                        found_skills[skill_key] = {
                            "name": skill.title() if len(skill) > 3 else skill.upper(),
                            "category": category,
                        }

        return list(found_skills.values())

    def match_requirements(
        self, resume_text: str, requirements: list[str]
    ) -> dict:
        """Match extracted skills against job requirements.

        Args:
            resume_text: Resume text to analyze.
            requirements: List of required skills.

        Returns:
            Dictionary with matched, missing skills and score.
        """
        # Extract skills from resume
        extracted = self.extract(resume_text)
        extracted_names = {s["name"].lower() for s in extracted}

        # Also add raw text matching for requirements not in database
        resume_lower = resume_text.lower()

        matched = []
        missing = []

        for req in requirements:
            req_lower = req.lower()
            # Check if requirement is in extracted skills or raw text
            if req_lower in extracted_names or req_lower in resume_lower:
                matched.append(req)
            else:
                missing.append(req)

        score = (len(matched) / len(requirements) * 100) if requirements else 0.0

        return {
            "matched": matched,
            "missing": missing,
            "score": score,
        }

    def get_summary(self, text: str) -> dict[SkillCategory, list[str]]:
        """Get a summary of skills grouped by category.

        Args:
            text: Text to analyze.

        Returns:
            Dictionary mapping categories to skill lists.
        """
        skills = self.extract(text)
        summary: dict[SkillCategory, list[str]] = {}

        for skill in skills:
            category = skill["category"]
            if category not in summary:
                summary[category] = []
            summary[category].append(skill["name"])

        return summary
