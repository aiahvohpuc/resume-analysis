"""Interview data management module."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class InterviewNotFoundError(Exception):
    """Raised when interview data is not found."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Interview data not found: {code}")


class InterviewManager:
    """Manages interview question data from JSON files."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize interview manager.

        Args:
            data_dir: Directory containing interview JSON files.
                     Defaults to config/interviews/ relative to project root.
        """
        if data_dir is None:
            # Find project root by looking for pyproject.toml
            current = Path(__file__).resolve()
            for parent in current.parents:
                if (parent / "pyproject.toml").exists():
                    data_dir = parent / "config" / "interviews"
                    break
            else:
                data_dir = Path(__file__).parent.parent.parent / "config" / "interviews"

        self._data_dir = data_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def list_interviews(self) -> list[str]:
        """List all available organization codes with interview data.

        Returns:
            List of organization codes (e.g., ["KEPCO", "NHIS", "KORAIL"])
        """
        orgs = []
        if not self._data_dir.exists():
            return orgs
        for file_path in self._data_dir.glob("*.json"):
            if file_path.stem.startswith("_"):
                continue  # Skip template files
            orgs.append(file_path.stem)
        return sorted(orgs)

    def get_interview(self, code: str) -> dict[str, Any]:
        """Get interview data by organization code.

        Args:
            code: Organization code (case insensitive)

        Returns:
            Interview data dictionary

        Raises:
            InterviewNotFoundError: If interview data not found
        """
        code_upper = code.upper()

        # Check cache first
        if code_upper in self._cache:
            return self._cache[code_upper]

        # Load from file
        file_path = self._data_dir / f"{code_upper}.json"
        if not file_path.exists():
            raise InterviewNotFoundError(code_upper)

        data = self._load_json(file_path)
        self._cache[code_upper] = data
        return data

    def get_questions(
        self,
        code: str,
        question_type: str | None = None,
        category: str | None = None,
        difficulty: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get filtered interview questions for an organization.

        Args:
            code: Organization code
            question_type: Filter by question type (e.g., "personality", "job_competency")
            category: Filter by category (e.g., "지원동기", "자기소개")
            difficulty: Filter by difficulty level (1-5)
            limit: Maximum number of questions to return

        Returns:
            List of matching questions
        """
        interview_data = self.get_interview(code)
        questions = interview_data.get("questions", [])

        # Apply filters
        if question_type:
            questions = [q for q in questions if q.get("type") == question_type]
        if category:
            questions = [q for q in questions if q.get("category") == category]
        if difficulty is not None:
            questions = [q for q in questions if q.get("difficulty") == difficulty]

        # Apply limit
        if limit:
            questions = questions[:limit]

        return questions

    def get_interview_format(self, code: str) -> dict[str, Any]:
        """Get interview format information for an organization.

        Args:
            code: Organization code

        Returns:
            Interview format information
        """
        interview_data = self.get_interview(code)
        return interview_data.get("interview_format", {})

    def get_statistics(self, code: str) -> dict[str, Any]:
        """Get statistics for interview questions.

        Args:
            code: Organization code

        Returns:
            Statistics dictionary
        """
        interview_data = self.get_interview(code)
        questions = interview_data.get("questions", [])

        # Count by type
        type_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        difficulty_counts: dict[int, int] = {}
        ncs_counts: dict[str, int] = {}

        for q in questions:
            # Type
            q_type = q.get("type", "unknown")
            type_counts[q_type] = type_counts.get(q_type, 0) + 1

            # Category
            cat = q.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

            # Difficulty
            diff = q.get("difficulty", 3)
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

            # NCS competencies
            for ncs in q.get("ncs_competencies", []):
                ncs_counts[ncs] = ncs_counts.get(ncs, 0) + 1

        return {
            "total_questions": len(questions),
            "by_type": type_counts,
            "by_category": category_counts,
            "by_difficulty": difficulty_counts,
            "by_ncs": ncs_counts,
        }

    @staticmethod
    @lru_cache(maxsize=64)
    def _load_json(file_path: Path) -> dict[str, Any]:
        """Load and cache JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
