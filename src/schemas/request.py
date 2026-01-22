"""Request schemas for resume analysis API."""

from pydantic import BaseModel, Field, field_validator


class ResumeAnalysisRequest(BaseModel):
    """Request schema for resume analysis endpoint."""

    organization: str = Field(
        ...,
        description="기관 코드 (예: NHIS, HIRA, NPS)",
        min_length=1,
    )
    position: str = Field(
        ...,
        description="지원 직렬 (예: 행정직, 전산직)",
        min_length=1,
    )
    question: str = Field(
        default="자기소개서",
        description="자기소개서 문항",
    )
    answer: str = Field(
        ...,
        description="자기소개서 답변 내용",
        min_length=1,
    )
    maxLength: int = Field(  # noqa: N815
        default=1000,
        description="최대 글자 수",
        gt=0,
    )

    @field_validator("organization", "position", "answer", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v
