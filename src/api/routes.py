"""API routes."""

import os
import tempfile
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from src.api.dependencies import (
    get_feedback_analyzer,
    get_interview_manager,
    get_organization_manager,
)
from src.data.interview_manager import InterviewManager, InterviewNotFoundError
from src.data.organization_manager import OrganizationManager, OrganizationNotFoundError
from src.parser.pdf_parser import PDFParser
from src.schemas.request import ResumeAnalysisRequest
from src.schemas.response import NewResumeAnalysisResponse, ResumeAnalysisResponse
from src.services.feedback_analyzer import FeedbackAnalyzer

PDF_MAGIC_BYTES = b"%PDF"
MAX_EXTRACTED_CHARS = 2500

router = APIRouter(prefix="/api")


@router.post("/feedback/resume", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    request: ResumeAnalysisRequest,
    analyzer: FeedbackAnalyzer = Depends(get_feedback_analyzer),
) -> ResumeAnalysisResponse:
    """Analyze resume and provide feedback (legacy v1).

    Args:
        request: Resume analysis request
        analyzer: Feedback analyzer dependency

    Returns:
        Analysis response with feedback
    """
    try:
        return await analyzer.analyze(request)
    except OrganizationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/feedback/resume/v2", response_model=NewResumeAnalysisResponse)
async def analyze_resume_v2(
    request: ResumeAnalysisRequest,
    analyzer: FeedbackAnalyzer = Depends(get_feedback_analyzer),
) -> NewResumeAnalysisResponse:
    """Analyze resume and provide feedback (v2 - redesigned).

    Provides enhanced analysis including:
    - Organization info summary (core values, talent image, recent news)
    - Structured strengths with direct quotes
    - Improvements with concrete before/after examples
    - Interview questions with tips
    - Full model answer rewrite

    Args:
        request: Resume analysis request
        analyzer: Feedback analyzer dependency

    Returns:
        New format analysis response with detailed feedback
    """
    try:
        return await analyzer.analyze_v2(request)
    except OrganizationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/organizations", response_model=list[str])
async def list_organizations(
    org_manager: OrganizationManager = Depends(get_organization_manager),
) -> list[str]:
    """List all available organizations.

    Args:
        org_manager: Organization manager dependency

    Returns:
        List of organization codes
    """
    return org_manager.list_organizations()


@router.get("/organizations/{code}")
async def get_organization(
    code: str,
    org_manager: OrganizationManager = Depends(get_organization_manager),
) -> dict[str, Any]:
    """Get organization details.

    Args:
        code: Organization code
        org_manager: Organization manager dependency

    Returns:
        Organization details

    Raises:
        HTTPException: If organization not found
    """
    try:
        return org_manager.get_organization(code)
    except OrganizationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile) -> dict[str, str]:
    """Upload PDF file and extract text.

    Args:
        file: Uploaded PDF file

    Returns:
        Extracted text from PDF

    Raises:
        HTTPException: If file is not a PDF or extraction fails
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")

    tmp_path = None
    try:
        content = await file.read()

        if not content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=400,
                detail="유효한 PDF 파일이 아닙니다."
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        parser = PDFParser()
        extracted_text = parser.extract_text(tmp_path)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="PDF에서 텍스트를 추출할 수 없습니다."
            )

        if len(extracted_text) > MAX_EXTRACTED_CHARS:
            raise HTTPException(
                status_code=400,
                detail=f"텍스트가 {MAX_EXTRACTED_CHARS}자를 초과합니다. "
                       f"(현재: {len(extracted_text)}자)"
            )

        return {"text": extracted_text}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 처리 중 오류가 발생했습니다: {str(e)}"
        ) from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============== Interview Routes ==============


@router.get("/interviews", response_model=list[str])
async def list_interviews(
    interview_manager: InterviewManager = Depends(get_interview_manager),
) -> list[str]:
    """List all organizations with interview data.

    Returns:
        List of organization codes with interview data
    """
    return interview_manager.list_interviews()


@router.get("/interviews/{code}")
async def get_interview(
    code: str,
    interview_manager: InterviewManager = Depends(get_interview_manager),
) -> dict[str, Any]:
    """Get interview data for an organization.

    Args:
        code: Organization code

    Returns:
        Complete interview data including format and questions

    Raises:
        HTTPException: If interview data not found
    """
    try:
        return interview_manager.get_interview(code)
    except InterviewNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/interviews/{code}/questions")
async def get_interview_questions(
    code: str,
    question_type: str | None = Query(None, description="Filter by type (personality, job_competency, etc.)"),
    category: str | None = Query(None, description="Filter by category (지원동기, 자기소개, etc.)"),
    difficulty: int | None = Query(None, ge=1, le=5, description="Filter by difficulty (1-5)"),
    limit: int | None = Query(None, ge=1, le=100, description="Max questions to return"),
    interview_manager: InterviewManager = Depends(get_interview_manager),
) -> list[dict[str, Any]]:
    """Get filtered interview questions for an organization.

    Args:
        code: Organization code
        question_type: Filter by question type
        category: Filter by category
        difficulty: Filter by difficulty level (1-5)
        limit: Maximum number of questions

    Returns:
        List of matching interview questions
    """
    try:
        return interview_manager.get_questions(
            code=code,
            question_type=question_type,
            category=category,
            difficulty=difficulty,
            limit=limit,
        )
    except InterviewNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/interviews/{code}/format")
async def get_interview_format(
    code: str,
    interview_manager: InterviewManager = Depends(get_interview_manager),
) -> dict[str, Any]:
    """Get interview format information for an organization.

    Args:
        code: Organization code

    Returns:
        Interview format details (type, stages, duration, etc.)
    """
    try:
        return interview_manager.get_interview_format(code)
    except InterviewNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/interviews/{code}/stats")
async def get_interview_stats(
    code: str,
    interview_manager: InterviewManager = Depends(get_interview_manager),
) -> dict[str, Any]:
    """Get statistics for interview questions.

    Args:
        code: Organization code

    Returns:
        Statistics (total, by type, by category, by difficulty, by NCS)
    """
    try:
        return interview_manager.get_statistics(code)
    except InterviewNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
