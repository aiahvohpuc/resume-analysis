"""API routes for analyzer endpoints."""

from fastapi import APIRouter

from src.analyzer.section_classifier import SectionClassifier
from src.analyzer.skill_extractor import SkillExtractor
from src.schemas.analyzer import (
    ResumeParseRequest,
    ResumeParseResponse,
    SectionClassificationRequest,
    SectionClassificationResponse,
    SectionItem,
    SkillAnalysisRequest,
    SkillAnalysisResponse,
    SkillItem,
    SkillMatchResult,
)

router = APIRouter(prefix="/api/analyze")


@router.post("/skills", response_model=SkillAnalysisResponse)
async def analyze_skills(request: SkillAnalysisRequest) -> SkillAnalysisResponse:
    """Analyze skills from text.

    Args:
        request: Skill analysis request

    Returns:
        Analysis response with extracted skills
    """
    extractor = SkillExtractor()

    # Extract skills
    raw_skills = extractor.extract(request.text)
    skills = [
        SkillItem(name=s["name"], category=s["category"].value)
        for s in raw_skills
    ]

    # Get summary by category
    raw_summary = extractor.get_summary(request.text)
    summary = {cat.value: names for cat, names in raw_summary.items()}

    # Match with requirements if provided
    match_result = None
    if request.requirements:
        raw_match = extractor.match_requirements(request.text, request.requirements)
        match_result = SkillMatchResult(
            matched=raw_match["matched"],
            missing=raw_match["missing"],
            score=raw_match["score"],
        )

    return SkillAnalysisResponse(
        skills=skills,
        summary=summary,
        match_result=match_result,
    )


@router.post("/sections", response_model=SectionClassificationResponse)
async def classify_sections(
    request: SectionClassificationRequest,
) -> SectionClassificationResponse:
    """Classify resume sections.

    Args:
        request: Section classification request

    Returns:
        Classification response with identified sections
    """
    classifier = SectionClassifier()

    # Split text into lines and classify
    lines = request.text.split("\n")
    raw_sections = classifier.classify_document(lines)

    sections = [
        SectionItem(type=s["type"].value, content=s["content"])
        for s in raw_sections
    ]

    return SectionClassificationResponse(sections=sections)


@router.post("/resume", response_model=ResumeParseResponse)
async def parse_resume(request: ResumeParseRequest) -> ResumeParseResponse:
    """Parse complete resume text.

    Args:
        request: Resume parse request

    Returns:
        Complete parsing response with sections and skills
    """
    classifier = SectionClassifier()
    extractor = SkillExtractor()

    # Classify sections
    lines = request.text.split("\n")
    raw_sections = classifier.classify_document(lines)
    sections = [
        SectionItem(type=s["type"].value, content=s["content"])
        for s in raw_sections
    ]

    # Extract skills
    raw_skills = extractor.extract(request.text)
    skills = [
        SkillItem(name=s["name"], category=s["category"].value)
        for s in raw_skills
    ]

    # Get skill summary
    raw_summary = extractor.get_summary(request.text)
    skill_summary = {cat.value: names for cat, names in raw_summary.items()}

    # Match with requirements if provided
    match_result = None
    if request.job_requirements:
        raw_match = extractor.match_requirements(
            request.text, request.job_requirements
        )
        match_result = SkillMatchResult(
            matched=raw_match["matched"],
            missing=raw_match["missing"],
            score=raw_match["score"],
        )

    return ResumeParseResponse(
        sections=sections,
        skills=skills,
        skill_summary=skill_summary,
        match_result=match_result,
    )
