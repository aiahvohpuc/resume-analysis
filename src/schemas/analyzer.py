"""Request and response schemas for analyzer API endpoints."""

from pydantic import BaseModel, Field


class SkillAnalysisRequest(BaseModel):
    """Request schema for skill analysis endpoint."""

    text: str = Field(
        ...,
        description="분석할 텍스트",
        min_length=1,
    )
    requirements: list[str] | None = Field(
        default=None,
        description="매칭할 직무 요구사항 목록",
    )


class SkillItem(BaseModel):
    """Individual skill item in response."""

    name: str = Field(..., description="스킬 이름")
    category: str = Field(..., description="스킬 카테고리")


class SkillMatchResult(BaseModel):
    """Skill matching result schema."""

    matched: list[str] = Field(..., description="매칭된 스킬 목록")
    missing: list[str] = Field(..., description="누락된 스킬 목록")
    score: float = Field(..., description="매칭 점수 (%)")


class SkillAnalysisResponse(BaseModel):
    """Response schema for skill analysis endpoint."""

    skills: list[SkillItem] = Field(..., description="추출된 스킬 목록")
    summary: dict[str, list[str]] = Field(..., description="카테고리별 스킬 요약")
    match_result: SkillMatchResult | None = Field(
        default=None,
        description="직무 요구사항 매칭 결과",
    )


class SectionClassificationRequest(BaseModel):
    """Request schema for section classification endpoint."""

    text: str = Field(
        ...,
        description="분류할 이력서 텍스트",
        min_length=1,
    )


class SectionItem(BaseModel):
    """Individual section item in response."""

    type: str = Field(..., description="섹션 타입")
    content: str = Field(..., description="섹션 내용")


class SectionClassificationResponse(BaseModel):
    """Response schema for section classification endpoint."""

    sections: list[SectionItem] = Field(..., description="분류된 섹션 목록")


class ResumeParseRequest(BaseModel):
    """Request schema for complete resume parsing endpoint."""

    text: str = Field(
        ...,
        description="파싱할 이력서 텍스트",
        min_length=1,
    )
    job_requirements: list[str] | None = Field(
        default=None,
        description="매칭할 직무 요구사항 목록",
    )


class ResumeParseResponse(BaseModel):
    """Response schema for complete resume parsing endpoint."""

    sections: list[SectionItem] = Field(..., description="분류된 섹션 목록")
    skills: list[SkillItem] = Field(..., description="추출된 스킬 목록")
    skill_summary: dict[str, list[str]] = Field(..., description="카테고리별 스킬 요약")
    match_result: SkillMatchResult | None = Field(
        default=None,
        description="직무 요구사항 매칭 결과",
    )
