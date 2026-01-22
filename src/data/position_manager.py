"""Position data management module."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class PositionNotFoundError(Exception):
    """Raised when position is not found."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Position not found: {code}")


class PositionManager:
    """Manages position data from JSON files."""

    # Position name to code mapping
    POSITION_NAME_MAP: dict[str, str] = {
        "경영기획": "BIZ_PLAN",
        "사업관리": "BIZ_MGMT",
        "인사/총무": "HR_GA",
        "인사총무": "HR_GA",
        "재무/회계/감사": "FIN_ACCT",
        "재무회계": "FIN_ACCT",
        "회계": "FIN_ACCT",
        "법무": "LEGAL",
        "법률": "LEGAL",
        "고객지원": "CS",
        "고객상담": "CS",
        "교육/연수": "TRAINING",
        "교육": "TRAINING",
        "마케팅/홍보": "MARKETING",
        "마케팅": "MARKETING",
        "홍보": "MARKETING",
        "금융": "FINANCE",
        "통계": "STATS",
        "컨설팅": "CONSULTING",
        "조사/연구": "RESEARCH",
        "연구": "RESEARCH",
        "토목": "CIVIL",
        "건축": "ARCH",
        "전기": "ELEC",
        "기계": "MECH",
        "화학": "CHEM",
        "통신": "COMM",
        "소방": "FIRE",
        "조경": "LANDSCAPE",
        "도시계획": "URBAN",
        "측량": "SURVEY",
        "원자력": "NUCLEAR",
        "수자원": "WATER",
        "환경": "ENV",
        "IT": "IT",
        "IT/ICT": "IT",
        "ICT": "IT",
        "전산": "IT",
        "정보통신": "IT",
        "안전관리": "SAFETY",
        "안전": "SAFETY",
        "보건": "HEALTH",
        "시설관리": "FACILITY",
        "시설": "FACILITY",
        "사무행정": "BIZ_MGMT",
        "행정": "BIZ_MGMT",
        "일반사무": "BIZ_MGMT",
    }

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize position manager.

        Args:
            data_dir: Directory containing position JSON files.
        """
        if data_dir is None:
            # Try knowledge-db path first
            current = Path(__file__).resolve()
            for parent in current.parents:
                knowledge_db_path = parent / "resume-knowledge-db" / "data" / "positions"
                if knowledge_db_path.exists():
                    data_dir = knowledge_db_path
                    break
            else:
                # Fallback to sibling project
                data_dir = Path(__file__).parent.parent.parent.parent / "resume-knowledge-db" / "data" / "positions"

        self._data_dir = data_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def get_position_code(self, position_name: str) -> str | None:
        """Convert position name to code.

        Args:
            position_name: Position name in Korean

        Returns:
            Position code or None if not found
        """
        # Direct match
        if position_name in self.POSITION_NAME_MAP:
            return self.POSITION_NAME_MAP[position_name]

        # Partial match
        for name, code in self.POSITION_NAME_MAP.items():
            if name in position_name or position_name in name:
                return code

        return None

    def get_position(self, code_or_name: str) -> dict[str, Any] | None:
        """Get position data by code or name.

        Args:
            code_or_name: Position code or name

        Returns:
            Position data dictionary or None if not found
        """
        # Try as code first
        code = code_or_name.upper()

        # If it's a name, convert to code
        if not self._data_dir or not (self._data_dir / f"{code}.json").exists():
            converted_code = self.get_position_code(code_or_name)
            if converted_code:
                code = converted_code

        # Check cache
        if code in self._cache:
            return self._cache[code]

        # Load from file
        if not self._data_dir:
            return None

        file_path = self._data_dir / f"{code}.json"
        if not file_path.exists():
            return None

        try:
            data = self._load_json(file_path)
            self._cache[code] = data
            return data
        except Exception:
            return None

    @staticmethod
    @lru_cache(maxsize=32)
    def _load_json(file_path: Path) -> dict[str, Any]:
        """Load and cache JSON file."""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def list_positions(self) -> list[str]:
        """List all available position codes."""
        if not self._data_dir or not self._data_dir.exists():
            return []

        positions = []
        for file_path in self._data_dir.glob("*.json"):
            if not file_path.stem.startswith("_"):
                positions.append(file_path.stem)
        return sorted(positions)
