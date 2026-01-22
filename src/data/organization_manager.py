"""Organization data management module."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class OrganizationNotFoundError(Exception):
    """Raised when organization is not found."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Organization not found: {code}")


class OrganizationManager:
    """Manages organization data from JSON files."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize organization manager.

        Args:
            data_dir: Directory containing organization JSON files.
                     Defaults to config/organizations/ relative to project root.
        """
        if data_dir is None:
            # Find project root by looking for pyproject.toml
            current = Path(__file__).resolve()
            for parent in current.parents:
                if (parent / "pyproject.toml").exists():
                    data_dir = parent / "config" / "organizations"
                    break
            else:
                data_dir = Path(__file__).parent.parent.parent / "config" / "organizations"

        self._data_dir = data_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def list_organizations(self) -> list[str]:
        """List all available organization codes.

        Returns:
            List of organization codes (e.g., ["NHIS", "HIRA", "NPS"])
        """
        orgs = []
        for file_path in self._data_dir.glob("*.json"):
            if file_path.stem.startswith("_"):
                continue  # Skip template files
            orgs.append(file_path.stem)
        return sorted(orgs)

    def get_organization(self, code: str) -> dict[str, Any]:
        """Get organization data by code.

        Args:
            code: Organization code (case insensitive)

        Returns:
            Organization data dictionary

        Raises:
            OrganizationNotFoundError: If organization not found
        """
        code_upper = code.upper()

        # Check cache first
        if code_upper in self._cache:
            return self._cache[code_upper]

        # Load from file
        file_path = self._data_dir / f"{code_upper}.json"
        if not file_path.exists():
            raise OrganizationNotFoundError(code_upper)

        data = self._load_json(file_path)
        self._cache[code_upper] = data
        return data

    @staticmethod
    @lru_cache(maxsize=32)
    def _load_json(file_path: Path) -> dict[str, Any]:
        """Load and cache JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
