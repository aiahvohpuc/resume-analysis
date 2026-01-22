"""Feedback analyzer service."""

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from src.core.prompts import PromptBuilder
from src.schemas.request import ResumeAnalysisRequest
from src.schemas.response import (
    CoreValueScore,
    FeedbackItem,
    FrequentInterviewQuestion,
    ImprovementItem,
    InterviewDetailInfo,
    InterviewQuestion,
    KeywordAnalysis,
    LengthCheck,
    NCSAnalysis,
    NCSCompetencyScore,
    NCSItem,
    NewResumeAnalysisResponse,
    OrganizationInfo,
    PastQuestion,
    PositionSkillMatch,
    RecentNewsItem,
    ResumeAnalysisResponse,
    SimilarQuestion,
    StrengthItem,
    TalentAnalysis,
    WarningItem,
)

if TYPE_CHECKING:
    from src.data.interview_manager import InterviewManager
    from src.data.organization_manager import OrganizationManager
    from src.data.position_manager import PositionManager
    from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# Pre-compiled regex patterns for performance (cached at module level)
# 블라인드 채용 위반 체크용 패턴
_SCHOOL_PATTERNS = [
    (re.compile(r"[가-힣]+대학교"), "학교명이 포함되어 있습니다"),
    (re.compile(r"[가-힣]+대학"), "학교명이 포함되어 있습니다"),
    (re.compile(r"(서울|연세|고려|성균관|한양|중앙|경희|한국외국어|서강|이화|숙명|건국|동국|홍익|국민|세종|단국|인하|아주|경북|부산|전남|전북|충남|충북|강원|제주)대"), "학교명이 포함되어 있습니다"),
]
_REGION_PATTERNS = [
    (re.compile(r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)(\s)?(출신|태생|에서 태어|에서 자라)"), "출신 지역이 언급되어 있습니다"),
]
_FAMILY_KEYWORDS_SHORT = [
    (re.compile(r"\b형\b"), "형"),
    (re.compile(r"\b누나\b"), "누나"),
    (re.compile(r"\b오빠\b"), "오빠"),
    (re.compile(r"\b언니\b"), "언니"),
    (re.compile(r"(?<![가-힣])동생(?![가-힣])"), "동생"),
]
# 숫자/수치 패턴
_NUMBER_PATTERN = re.compile(r"\d+(\.\d+)?(%|배|명|건|원|만원|억|개월|주|일|시간|회|개|점|위|등)")
# 경험 키워드 패턴
_EXPERIENCE_PATTERN = re.compile(r"(프로젝트|인턴|대회|공모전|봉사|동아리|팀|리더|담당|수행|개발|분석|기획|진행)")
# 문장 분리 패턴
_SENTENCE_SPLIT_PATTERN = re.compile(r"[.!?]\s*")
# 결과/성과 표현 패턴
_RESULT_PATTERNS = [
    re.compile(r"결과[,\s]"),
    re.compile(r"성과[를가]"),
    re.compile(r"달성"),
    re.compile(r"향상"),
    re.compile(r"개선"),
    re.compile(r"증가"),
    re.compile(r"감소"),
    re.compile(r"절감"),
    re.compile(r"수상"),
    re.compile(r"선정"),
]
# 가족 맥락 체크용 패턴 - 실제 차별 요소만 체크
# 블라인드 채용에서 금지하는 것: 부모 직업/재산/학력/사회적 지위 등 차별 요소
_PERSONAL_CONTEXT_PATTERNS = [
    re.compile(r"(직업이|직업을|직업은|일을\s*하시|회사에서\s*일|사업을|운영하시|근무하시)"),  # 부모 직업
    re.compile(r"(경제적|가난했|부유했|어려운\s*환경|넉넉한\s*환경|형편이)"),  # 경제 상황
    re.compile(r"(학력|학벌|대학을\s*나오|졸업하신)"),  # 부모 학력
    re.compile(r"(재산|유산|물려받|상속)"),  # 재산/상속
    re.compile(r"(사회적\s*지위|인맥|연줄)"),  # 사회적 지위
    re.compile(r"(돌아가시|별세하|사망하)"),  # 사망 관련 (동정심 유발)
]
# 예외 패턴 - 비유적/관용적 표현 및 가치관/교훈 관련 (블라인드 위반 아님)
_EXCEPTION_PATTERNS = [
    # 비유적 표현
    re.compile(r"아버지는\s*산"),
    re.compile(r"어머니는\s*(강|바다)"),
    re.compile(r"아버지\s*같은"),
    re.compile(r"어머니\s*같은"),
    re.compile(r"부모\s*같은"),
    re.compile(r"형\s*같은"),
    re.compile(r"누나\s*같은"),
    re.compile(r"동생\s*같은"),
    re.compile(r"가족\s*(같은|처럼)"),
    re.compile(r"형제\s*(같은|처럼)"),
    re.compile(r"고향\s*(같은|처럼)"),
    # 관용적 표현
    re.compile(r"인심"),
    re.compile(r"사람\s*사는\s*정"),
    re.compile(r"정이\s*많"),
    re.compile(r"따뜻한\s*마음"),
    # 가치관/교훈 관련 (블라인드 위반 아님 - 차별 요소가 아닌 인성/가치관)
    re.compile(r"가훈"),  # 가훈
    re.compile(r"가치관"),  # 가치관
    re.compile(r"교훈"),  # 교훈
    re.compile(r"좌우명"),  # 좌우명
    re.compile(r"신념"),  # 신념
    re.compile(r"철학"),  # 철학
    re.compile(r"마음가짐"),  # 마음가짐
    re.compile(r"삶의\s*(자세|태도|방식)"),  # 삶의 자세
    re.compile(r"(사랑|봉사|나눔|배려|존중|정직|성실|책임|감사).*바탕"),  # 가치 기반
    re.compile(r"주신\s*(말씀|가르침).*바탕"),  # 가르침 바탕으로
    re.compile(r"(말씀|가르침).*따라"),  # 가르침을 따라
    re.compile(r"물려받은\s*(정신|마음|가치)"),  # 정신적 유산 (재산 아님)
]
_DIRECT_FAMILY_PATTERNS = [
    (re.compile(r"가정환경이|가정\s*형편이|집안\s*형편"), "가정환경/집안 형편에 대한 언급이 있습니다"),
]
# 기관명 체크 패턴 (IGNORECASE)
_ORG_NAME_PATTERNS = [
    (re.compile(r"한국전력|한전", re.IGNORECASE), "KEPCO"),
    (re.compile(r"한국가스공사|가스공사", re.IGNORECASE), "KOGAS"),
    (re.compile(r"한국수자원공사|수자원공사|K-water", re.IGNORECASE), "KWATER"),
    (re.compile(r"한국철도공사|코레일", re.IGNORECASE), "KORAIL"),
    (re.compile(r"한국토지주택공사|LH공사", re.IGNORECASE), "LH"),
    (re.compile(r"국민건강보험공단|건보공단", re.IGNORECASE), "NHIS"),
    (re.compile(r"국민연금공단|연금공단", re.IGNORECASE), "NPS"),
    (re.compile(r"한국산업인력공단|산인공", re.IGNORECASE), "HRDK"),
    (re.compile(r"한국농수산식품유통공사|aT|에이티", re.IGNORECASE), "AT"),
    (re.compile(r"한국도로공사|도로공사", re.IGNORECASE), "EX"),
]


class FeedbackAnalyzer:
    """Analyzer for resume feedback generation."""

    def __init__(
        self,
        llm_service: "LLMService",
        org_manager: "OrganizationManager",
        interview_manager: "InterviewManager | None" = None,
        position_manager: "PositionManager | None" = None,
    ) -> None:
        """Initialize feedback analyzer.

        Args:
            llm_service: LLM service for generating analysis
            org_manager: Organization data manager
            interview_manager: Interview data manager (optional)
            position_manager: Position data manager (optional)
        """
        self._llm_service = llm_service
        self._org_manager = org_manager
        self._interview_manager = interview_manager
        self._position_manager = position_manager

    async def analyze(self, request: ResumeAnalysisRequest) -> ResumeAnalysisResponse:
        """Analyze resume and generate feedback (legacy v1).

        Args:
            request: Resume analysis request

        Returns:
            Complete analysis response
        """
        # Get organization data
        org_data = self._org_manager.get_organization(request.organization)

        # Get interview data if available
        interview_data = self._get_interview_data(request.organization)

        # Build prompts with position and interview context
        system_prompt = PromptBuilder.build_system_prompt(
            org_data=org_data,
            position=request.position,
            interview_data=interview_data,
        )
        user_prompt = PromptBuilder.build_user_prompt(request)

        # Get LLM analysis
        llm_response = await self._llm_service.analyze(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )

        # Parse and validate response
        return self._parse_response(llm_response, request)

    async def analyze_v2(
        self, request: ResumeAnalysisRequest
    ) -> NewResumeAnalysisResponse:
        """Analyze resume and generate feedback (v2 - redesigned).

        Args:
            request: Resume analysis request

        Returns:
            New format analysis response
        """
        # Get organization data
        org_data = self._org_manager.get_organization(request.organization)

        # Get interview data if available
        interview_data = self._get_interview_data(request.organization)

        # Get past questions data
        past_questions_data = self._get_past_questions(request.organization)

        # Pre-compute analyses for prompt enhancement (기관별 맞춤형 모범답안 생성용)
        core_values = org_data.get("core_values", []) if org_data else []
        core_value_scores = self.analyze_core_values(request.answer, core_values)
        ncs_competency_scores = self.analyze_ncs_competencies(request.answer, request.position)
        position_skill_match = self.analyze_position_skills(request.answer, request.position)

        # Build prompts with new v2 format (include pre-computed analyses)
        system_prompt = PromptBuilder.build_system_prompt_v2(
            org_data=org_data,
            position=request.position,
            interview_data=interview_data,
            core_value_scores=core_value_scores,
            ncs_competency_scores=ncs_competency_scores,
            position_skill_match=position_skill_match,
        )
        user_prompt = PromptBuilder.build_user_prompt(request)

        # Get LLM analysis
        llm_response = await self._llm_service.analyze(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )

        # Parse and validate response (pass pre-computed analyses)
        return self._parse_response_v2(
            llm_response, request, org_data, interview_data, past_questions_data,
            core_value_scores, ncs_competency_scores, position_skill_match,
        )

    def _get_interview_data(self, organization: str) -> dict[str, Any] | None:
        """Get interview data for organization if available.

        Args:
            organization: Organization code

        Returns:
            Interview data or None if not available
        """
        if not self._interview_manager:
            return None

        try:
            return self._interview_manager.get_interview(organization)
        except Exception:
            # Interview data not found, return None gracefully
            return None

    def _get_past_questions(self, organization: str) -> list[dict[str, Any]]:
        """Get past essay questions for organization.

        Args:
            organization: Organization code

        Returns:
            List of past questions or empty list
        """
        # Try to load from knowledge-db questions directory
        from pathlib import Path

        questions = []
        knowledge_db_path = Path(__file__).parent.parent.parent.parent / "resume-knowledge-db" / "data" / "questions"

        if not knowledge_db_path.exists():
            return questions

        # Find question files for this organization (recent years)
        # Include both verified (past) and unverified (predicted) questions
        for year in [2026, 2025, 2024, 2023, 2022]:
            question_file = knowledge_db_path / f"{organization.upper()}_{year}.json"
            if question_file.exists():
                try:
                    import json
                    with open(question_file, encoding="utf-8") as f:
                        data = json.load(f)
                        metadata = data.get("metadata", {})
                        is_verified = metadata.get("verified", True)
                        for q in data.get("questions", [])[:2]:  # Max 2 per year
                            questions.append({
                                "year": year,
                                "half": data.get("half", ""),
                                "question": q.get("text", ""),
                                "char_limit": q.get("char_limit", 0),
                                "is_prediction": not is_verified,  # True if not verified (prediction)
                            })
                except Exception:
                    pass

        return questions[:6]  # Max 6 total

    def _parse_response(
        self,
        llm_response: str,
        request: ResumeAnalysisRequest,
    ) -> ResumeAnalysisResponse:
        """Parse LLM response into structured response.

        Args:
            llm_response: Raw LLM JSON response
            request: Original request for length calculation

        Returns:
            Validated response object
        """
        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            logger.debug(f"Raw response: {llm_response[:500]}...")
            # Return default response on parse error
            data = {
                "overall_score": 50,
                "feedbacks": [],
                "keyword_analysis": {"found_keywords": [], "missing_keywords": [], "match_rate": 0},
                "expected_questions": [],
            }

        # Calculate actual length check (override LLM values for accuracy)
        length_check = self.calculate_length_check(request.answer, request.maxLength)

        # Parse NCS analysis if available
        ncs_analysis = None
        if "ncs_analysis" in data and data["ncs_analysis"]:
            ncs_data = data["ncs_analysis"]
            ncs_analysis = NCSAnalysis(
                evaluated_competencies=[
                    NCSItem(
                        competency=item["competency"],
                        score=item["score"],
                        evidence=item["evidence"],
                        suggestion=item.get("suggestion"),
                    )
                    for item in ncs_data.get("evaluated_competencies", [])
                ],
                strongest=ncs_data.get("strongest", ""),
                weakest=ncs_data.get("weakest", ""),
                overall_comment=ncs_data.get("overall_comment", ""),
            )

        # Parse talent analysis if available
        talent_analysis = None
        if "talent_analysis" in data and data["talent_analysis"]:
            talent_data = data["talent_analysis"]
            talent_analysis = TalentAnalysis(
                match_score=talent_data.get("match_score", 5),
                matched_traits=talent_data.get("matched_traits", []),
                missing_traits=talent_data.get("missing_traits", []),
                overall_comment=talent_data.get("overall_comment", ""),
                improvement_tips=talent_data.get("improvement_tips", []),
            )

        return ResumeAnalysisResponse(
            overall_score=data["overall_score"],
            length_check=length_check,
            feedbacks=[
                FeedbackItem(
                    category=f["category"],
                    score=f["score"],
                    comment=f["comment"],
                    suggestion=f.get("suggestion"),
                )
                for f in data.get("feedbacks", [])
            ],
            keyword_analysis=KeywordAnalysis(
                found_keywords=data["keyword_analysis"]["found_keywords"],
                missing_keywords=data["keyword_analysis"]["missing_keywords"],
                match_rate=data["keyword_analysis"]["match_rate"],
            ),
            ncs_analysis=ncs_analysis,
            talent_analysis=talent_analysis,
            expected_questions=data.get("expected_questions", []),
        )

    def calculate_length_check(self, answer: str, max_length: int) -> LengthCheck:
        """Calculate length check for answer.

        Args:
            answer: Answer text
            max_length: Maximum allowed length

        Returns:
            Length check result
        """
        current = len(answer)
        percentage = (current / max_length) * 100 if max_length > 0 else 0

        if percentage > 100:
            status = "over"
        elif percentage >= 70:
            status = "optimal"
        else:
            status = "short"

        return LengthCheck(
            current=current,
            max=max_length,
            percentage=round(percentage, 1),
            status=status,
        )

    def check_warnings(self, answer: str, organization: str) -> list[WarningItem]:
        """자소서 공통 실수 체크.

        Args:
            answer: 자소서 답변 텍스트
            organization: 기관 코드

        Returns:
            경고 항목 목록
        """
        warnings: list[WarningItem] = []

        # 1. 블라인드 채용 위반 체크
        warnings.extend(self._check_blind_violations(answer))

        # 2. 추상적 표현 체크
        warnings.extend(self._check_abstract_expressions(answer))

        # 3. 수치/결과 부재 체크
        warnings.extend(self._check_missing_results(answer))

        # 4. 기관명 오류 체크
        warnings.extend(self._check_organization_name(answer, organization))

        return warnings

    def _check_blind_violations(self, answer: str) -> list[WarningItem]:
        """블라인드 채용 위반 체크."""
        warnings: list[WarningItem] = []

        # 학교명 패턴 (사전 컴파일된 패턴 사용)
        for compiled_pattern, message in _SCHOOL_PATTERNS:
            matches = compiled_pattern.findall(answer)
            if matches:
                warnings.append(WarningItem(
                    type="blind_violation",
                    severity="high",
                    message=f"⚠️ 블라인드 채용 위반: {message}",
                    detected_text=", ".join(set(matches)),
                    suggestion="학교명을 '대학교에서', '학부 과정에서' 등으로 수정하세요.",
                ))
                break

        # 가족관계 패턴 - 문맥 기반 체크
        family_warnings = self._check_family_context(answer)
        warnings.extend(family_warnings)

        # 출신 지역 패턴 (사전 컴파일된 패턴 사용)
        for compiled_pattern, message in _REGION_PATTERNS:
            match = compiled_pattern.search(answer)
            if match:
                warnings.append(WarningItem(
                    type="blind_violation",
                    severity="high",
                    message=f"⚠️ 블라인드 채용 위반: {message}",
                    detected_text=match.group(),
                    suggestion="출신 지역 언급을 삭제하세요.",
                ))
                break

        return warnings

    def _check_family_context(self, answer: str) -> list[WarningItem]:
        """가족 관계 언급을 문맥 기반으로 체크.

        단순 단어 매칭이 아닌, 실제로 개인 가족 정보를 노출하는 맥락인지 확인.
        문화적/관용적 표현은 블라인드 위반으로 간주하지 않음.
        """
        warnings: list[WarningItem] = []

        # 문장 단위로 분리 (사전 컴파일된 패턴 사용)
        sentences = _SENTENCE_SPLIT_PATTERN.split(answer)

        # 가족 관련 키워드 (긴 키워드만 - 짧은 것은 오탐 유발)
        # "형", "동생" 등은 다른 단어에 포함될 수 있어 제외
        family_keywords_long = ["아버지", "어머니", "부모님", "부친", "모친", "할아버지", "할머니"]

        # 짧은 가족 키워드는 사전 컴파일된 패턴 사용
        # _FAMILY_KEYWORDS_SHORT 모듈 레벨 상수 참조

        # 개인 정보 노출 맥락, 예외 패턴은 모듈 레벨 상수 사용
        # _PERSONAL_CONTEXT_PATTERNS, _EXCEPTION_PATTERNS 참조

        for sentence in sentences:
            if len(sentence.strip()) < 10:  # 너무 짧은 문장은 스킵
                continue

            # 예외 패턴에 해당하면 스킵 (문화적/관용적 표현) - 캐시된 패턴 사용
            is_exception = False
            for exc_pattern in _EXCEPTION_PATTERNS:
                if exc_pattern.search(sentence):
                    is_exception = True
                    break

            if is_exception:
                continue

            # 가족 키워드가 있는지 확인 (긴 키워드)
            found_family_word = None
            for family_word in family_keywords_long:
                if family_word in sentence:
                    found_family_word = family_word
                    break

            # 짧은 키워드는 사전 컴파일된 패턴으로 체크
            if not found_family_word:
                for compiled_pattern, word in _FAMILY_KEYWORDS_SHORT:
                    if compiled_pattern.search(sentence):
                        found_family_word = word
                        break

            if not found_family_word:
                continue

            # 개인 정보 노출 맥락인지 확인 - 캐시된 패턴 사용
            for context_pattern in _PERSONAL_CONTEXT_PATTERNS:
                if context_pattern.search(sentence):
                    warnings.append(WarningItem(
                        type="blind_violation",
                        severity="high",
                        message="⚠️ 블라인드 채용 위반: 가족 관계/배경이 언급되어 있습니다",
                        detected_text=sentence.strip()[:50] + ("..." if len(sentence.strip()) > 50 else ""),
                        suggestion="가족의 직업, 영향, 배경 등에 대한 언급을 삭제하거나 다른 표현으로 대체하세요.",
                    ))
                    return warnings  # 하나만 발견해도 충분

        # 직접적인 가정환경 언급은 여전히 체크 - 캐시된 패턴 사용
        for compiled_pattern, message in _DIRECT_FAMILY_PATTERNS:
            match = compiled_pattern.search(answer)
            if match:
                warnings.append(WarningItem(
                    type="blind_violation",
                    severity="high",
                    message=f"⚠️ 블라인드 채용 위반: {message}",
                    detected_text=match.group(),
                    suggestion="가정환경 관련 언급을 삭제하세요.",
                ))
                break

        return warnings

    def _check_abstract_expressions(self, answer: str) -> list[WarningItem]:
        """추상적 표현 체크."""
        warnings: list[WarningItem] = []

        abstract_patterns = [
            ("열심히 하겠습니다", "구체적인 계획이나 방법을 제시하세요"),
            ("최선을 다하겠습니다", "어떻게 최선을 다할 것인지 구체적으로 서술하세요"),
            ("열정적으로", "열정의 구체적인 증거나 경험을 제시하세요"),
            ("성실하게", "성실함을 보여주는 구체적인 경험을 추가하세요"),
            ("노력하겠습니다", "구체적인 실천 방안을 제시하세요"),
            ("귀사의 발전에 기여", "어떤 방식으로 기여할 것인지 구체화하세요"),
            ("다양한 경험", "'다양한'을 구체적인 경험 나열로 대체하세요"),
            ("많은 것을 배웠습니다", "무엇을 배웠는지 구체적으로 서술하세요"),
        ]

        found_abstracts = []
        for phrase, suggestion in abstract_patterns:
            if phrase in answer:
                found_abstracts.append((phrase, suggestion))

        if found_abstracts:
            # 최대 3개까지만 경고
            for phrase, suggestion in found_abstracts[:3]:
                warnings.append(WarningItem(
                    type="abstract_expression",
                    severity="medium",
                    message=f"💭 추상적 표현: \"{phrase}\"",
                    detected_text=phrase,
                    suggestion=suggestion,
                ))

        return warnings

    def _check_missing_results(self, answer: str) -> list[WarningItem]:
        """수치/결과 부재 체크."""
        warnings: list[WarningItem] = []

        # 수치가 있는지 확인 (%, 배, 명, 건, 원, 개월 등) - 캐시된 패턴 사용
        has_numbers = bool(_NUMBER_PATTERN.search(answer))

        # 결과 표현이 있는지 확인 - 캐시된 패턴 사용
        has_result = any(p.search(answer) for p in _RESULT_PATTERNS)

        if not has_numbers and not has_result:
            warnings.append(WarningItem(
                type="missing_result",
                severity="medium",
                message="📊 구체적인 성과/수치가 부족합니다",
                detected_text="",
                suggestion="경험의 결과를 수치로 표현해 보세요. 예: '전년 대비 20% 향상', '3개월 만에 완료'",
            ))

        return warnings

    def _check_organization_name(self, answer: str, organization: str) -> list[WarningItem]:
        """기관명 오류 체크."""
        warnings: list[WarningItem] = []

        # 다른 기관명이 들어있는지 확인 - 캐시된 패턴 사용
        for compiled_pattern, org_code in _ORG_NAME_PATTERNS:
            if org_code != organization.upper():
                match = compiled_pattern.search(answer)
                if match:
                    warnings.append(WarningItem(
                        type="wrong_organization",
                        severity="high",
                        message=f"🚨 다른 기관명 발견: \"{match.group()}\"",
                        detected_text=match.group(),
                        suggestion="지원 기관명이 맞는지 확인하세요. 복사-붙여넣기 오류일 수 있습니다.",
                    ))
                    break

        return warnings

    def analyze_core_values(
        self, answer: str, core_values: list[str]
    ) -> list[CoreValueScore]:
        """핵심가치별 반영 점수 분석.

        Args:
            answer: 자소서 답변 텍스트
            core_values: 기관의 핵심가치 목록

        Returns:
            핵심가치별 점수 목록
        """
        scores: list[CoreValueScore] = []

        # 핵심가치별 관련 키워드 매핑
        value_keywords: dict[str, list[str]] = {
            # 공통 핵심가치
            "고객중심": ["고객", "수요자", "국민", "서비스", "만족", "편의", "사용자", "이용자"],
            "고객만족": ["고객", "만족", "서비스", "편의", "이용자", "수요자"],
            "상생": ["상생", "협력", "협업", "파트너", "동반성장", "함께", "공생", "상호"],
            "협력": ["협력", "협업", "팀워크", "소통", "함께", "공동", "파트너십"],
            "혁신": ["혁신", "변화", "창의", "개선", "새로운", "도전", "발전", "디지털", "AI", "스마트"],
            "창의": ["창의", "창조", "새로운", "아이디어", "혁신", "독창"],
            "전문성": ["전문", "역량", "지식", "기술", "숙련", "경험", "노하우", "전문가"],
            "청렴": ["청렴", "윤리", "투명", "공정", "정직", "신뢰", "도덕", "준법"],
            "정직": ["정직", "진실", "성실", "신뢰", "투명"],
            "신뢰": ["신뢰", "믿음", "정직", "성실", "책임"],
            "책임": ["책임", "의무", "사명", "역할", "담당", "맡은"],
            "안전": ["안전", "보안", "예방", "사고", "리스크", "위험관리"],
            "소통": ["소통", "커뮤니케이션", "대화", "공유", "협의", "논의"],
            "도전": ["도전", "시도", "극복", "목표", "성장", "발전"],
            "열정": ["열정", "열심", "헌신", "몰입", "적극", "의지"],
            "성장": ["성장", "발전", "향상", "진보", "개발", "학습"],
            "봉사": ["봉사", "기여", "공헌", "나눔", "사회적"],
            "공익": ["공익", "공공", "국민", "사회", "기여"],
            "존중": ["존중", "배려", "이해", "포용", "다양성"],
            "효율": ["효율", "생산성", "최적화", "절감", "개선"],
        }

        answer_lower = answer.lower()

        for value in core_values:
            # 핵심가치 이름 정규화
            value_normalized = value.strip()
            keywords = value_keywords.get(value_normalized, [value_normalized])

            # 키워드 검색
            found_keywords: list[str] = []
            evidence_parts: list[str] = []

            for keyword in keywords:
                if keyword.lower() in answer_lower:
                    found_keywords.append(keyword)
                    # 해당 키워드가 포함된 문장 찾기
                    sentences = _SENTENCE_SPLIT_PATTERN.split(answer)
                    for sentence in sentences:
                        if keyword in sentence and len(sentence) > 10:
                            if sentence not in evidence_parts:
                                evidence_parts.append(sentence.strip())
                            break

            # 점수 계산
            if len(found_keywords) >= 3:
                score = 9
            elif len(found_keywords) >= 2:
                score = 7
            elif len(found_keywords) >= 1:
                score = 5
            else:
                score = 3

            # 직접 언급 보너스
            if value_normalized in answer:
                score = min(10, score + 1)

            found = len(found_keywords) > 0

            # 근거 또는 제안 생성
            evidence = ""
            suggestion = ""

            if found and evidence_parts:
                evidence = evidence_parts[0][:100] + ("..." if len(evidence_parts[0]) > 100 else "")
            elif not found:
                suggestion = f"'{value_normalized}' 관련 경험이나 가치관을 추가해 보세요."

            scores.append(CoreValueScore(
                value=value_normalized,
                score=score,
                found=found,
                evidence=evidence,
                suggestion=suggestion,
            ))

        return scores

    def analyze_ncs_competencies(
        self, answer: str, position: str
    ) -> list[NCSCompetencyScore]:
        """NCS 역량별 반영 점수 분석.

        Args:
            answer: 자소서 답변 텍스트
            position: 직무명

        Returns:
            NCS 역량별 점수 목록
        """
        if not self._position_manager:
            return []

        # 직무 데이터 가져오기
        position_data = self._position_manager.get_position(position)
        if not position_data:
            return []

        ncs_competencies = position_data.get("ncs_competencies", [])
        if not ncs_competencies:
            return []

        scores: list[NCSCompetencyScore] = []

        # NCS 역량별 관련 키워드 매핑
        ncs_keywords: dict[str, list[str]] = {
            "의사소통능력": ["의사소통", "소통", "커뮤니케이션", "발표", "보고", "문서작성", "경청", "설득", "협의", "전달"],
            "수리능력": ["수리", "계산", "통계", "데이터", "분석", "수치", "정량", "그래프", "엑셀", "숫자"],
            "문제해결능력": ["문제해결", "해결", "분석", "원인", "대안", "개선", "극복", "대처", "창의", "혁신"],
            "자기개발능력": ["자기개발", "학습", "성장", "역량", "노력", "공부", "자격증", "교육", "훈련", "발전"],
            "자원관리능력": ["자원관리", "예산", "일정", "시간관리", "인력", "물자", "효율", "관리", "배분", "조달"],
            "대인관계능력": ["대인관계", "협력", "팀워크", "갈등", "조율", "리더십", "팔로워십", "네트워크", "관계", "조정"],
            "정보능력": ["정보", "데이터", "시스템", "컴퓨터", "IT", "분석", "수집", "활용", "디지털", "DB"],
            "기술능력": ["기술", "전문", "숙련", "도구", "장비", "시스템", "개발", "설계", "구현", "운영"],
            "조직이해능력": ["조직", "기관", "회사", "문화", "비전", "미션", "전략", "목표", "부서", "업무"],
            "직업윤리": ["윤리", "청렴", "책임", "성실", "정직", "준법", "공정", "도덕", "신뢰", "윤리의식"],
        }

        answer_lower = answer.lower()

        for ncs in ncs_competencies:
            ncs_name = ncs.get("name", "")
            ncs_code = ncs.get("code", "")
            importance = ncs.get("importance", "권장")

            keywords = ncs_keywords.get(ncs_name, [ncs_name])

            # 키워드 검색
            found_keywords: list[str] = []
            evidence_parts: list[str] = []

            for keyword in keywords:
                if keyword.lower() in answer_lower or keyword in answer:
                    found_keywords.append(keyword)
                    # 해당 키워드가 포함된 문장 찾기
                    sentences = _SENTENCE_SPLIT_PATTERN.split(answer)
                    for sentence in sentences:
                        if keyword in sentence and len(sentence) > 10:
                            if sentence not in evidence_parts:
                                evidence_parts.append(sentence.strip())
                            break

            # 점수 계산 (중요도에 따라 가중치)
            base_score = 3
            if len(found_keywords) >= 3:
                base_score = 9
            elif len(found_keywords) >= 2:
                base_score = 7
            elif len(found_keywords) >= 1:
                base_score = 5

            # 중요도가 필수인데 발견되지 않으면 감점
            if importance == "필수" and len(found_keywords) == 0:
                base_score = 2

            found = len(found_keywords) > 0

            # 근거 또는 제안 생성
            evidence = ""
            suggestion = ""

            # NCS 역량별 구체적 제안 메시지
            ncs_suggestions: dict[str, str] = {
                "의사소통능력": "팀 프로젝트에서 의견 조율, 발표 경험, 보고서 작성 등 소통 역량을 보여주는 구체적 사례를 추가하세요. 예: '주간 회의에서 진행 상황을 보고하고, 팀원들의 피드백을 반영하여...'",
                "수리능력": "데이터 분석, 통계 활용, 수치 기반 의사결정 경험을 구체적으로 기술하세요. 예: '매출 데이터를 분석하여 전년 대비 15% 성장 원인을 파악하고...'",
                "문제해결능력": "어려운 상황을 극복한 경험을 상황-문제-해결-결과(STAR) 구조로 작성하세요. 예: '프로젝트 중 예상치 못한 기술적 문제가 발생했을 때, 대안을 분석하고...'",
                "자기개발능력": "자격증 취득, 교육 이수, 자기주도 학습 경험을 구체적으로 기술하세요. 예: '업무 역량 향상을 위해 Python 온라인 강좌를 수료하고, 실무에 적용하여...'",
                "자원관리능력": "예산 관리, 일정 조율, 인력 배분 등 자원을 효율적으로 관리한 경험을 추가하세요. 예: '한정된 예산 내에서 우선순위를 설정하여 핵심 과제에 집중한 결과...'",
                "대인관계능력": "팀워크, 갈등 해결, 협력 경험을 구체적으로 작성하세요. 예: '팀원 간 의견 충돌 시 각자의 입장을 경청하고 중재하여 합의점을 도출했습니다...'",
                "정보능력": "정보 수집, 데이터 활용, IT 시스템 활용 경험을 추가하세요. 예: '업무 효율화를 위해 엑셀 매크로를 활용하여 반복 작업을 자동화하고...'",
                "기술능력": "전문 기술, 도구 활용, 시스템 운영 경험을 구체적으로 기술하세요. 예: 'AutoCAD를 활용한 도면 작성, Python 데이터 분석 등 실무 기술을 적용하여...'",
                "조직이해능력": "지원 기관의 미션, 비전, 최근 사업에 대한 이해를 보여주세요. 예: '기관의 디지털 전환 전략에 공감하며, 제 IT 역량을 활용하여 기여하고 싶습니다...'",
                "직업윤리": "책임감, 성실성, 청렴성을 보여주는 경험을 추가하세요. 예: '맡은 업무에 대한 책임감으로 야근도 마다하지 않고 기한 내 완수했습니다...'",
            }

            if found and evidence_parts:
                evidence = evidence_parts[0][:100] + ("..." if len(evidence_parts[0]) > 100 else "")
            elif not found:
                specific_suggestion = ncs_suggestions.get(ncs_name, f"'{ncs_name}' 관련 구체적인 경험을 추가하세요.")
                if importance == "필수":
                    suggestion = f"[필수 역량] {specific_suggestion}"
                else:
                    suggestion = specific_suggestion

            scores.append(NCSCompetencyScore(
                code=ncs_code,
                name=ncs_name,
                importance=importance,
                score=base_score,
                found=found,
                evidence=evidence,
                suggestion=suggestion,
            ))

        return scores

    def find_similar_questions(
        self, question: str | None, organization: str
    ) -> list[SimilarQuestion]:
        """현재 질문과 유사한 기출문항 찾기.

        Args:
            question: 현재 질문 (없으면 빈 리스트 반환)
            organization: 기관 코드

        Returns:
            유사 기출문항 목록 (유사도 순)
        """
        if not question:
            return []

        from pathlib import Path

        similar: list[SimilarQuestion] = []
        knowledge_db_path = Path(__file__).parent.parent.parent.parent / "resume-knowledge-db" / "data" / "questions"

        if not knowledge_db_path.exists():
            return []

        # 현재 질문에서 키워드 추출
        question_keywords = self._extract_question_keywords(question)

        # 최근 5년간의 기출문항 확인
        for year in [2025, 2024, 2023, 2022, 2021]:
            question_file = knowledge_db_path / f"{organization.upper()}_{year}.json"
            if not question_file.exists():
                continue

            try:
                import json
                with open(question_file, encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {})
                # 예상 문항(verified=False)은 유사도 분석에서 제외
                if not metadata.get("verified", True):
                    continue

                half = data.get("half", "")

                for q in data.get("questions", []):
                    q_text = q.get("text", "")
                    q_keywords = q.get("keywords", [])
                    q_ncs = q.get("ncs_categories", [])

                    # 유사도 계산
                    similarity, matched = self._calculate_similarity(
                        question_keywords, q_text, q_keywords, q_ncs
                    )

                    if similarity >= 30:  # 30% 이상만 포함
                        similar.append(SimilarQuestion(
                            year=year,
                            half=half,
                            question=q_text,
                            similarity=similarity,
                            char_limit=q.get("char_limit", 0),
                            matched_keywords=matched,
                        ))

            except Exception:
                continue

        # 유사도 순으로 정렬, 상위 5개만 반환
        similar.sort(key=lambda x: x.similarity, reverse=True)
        return similar[:5]

    def _extract_question_keywords(self, question: str) -> set[str]:
        """질문에서 키워드 추출.

        Args:
            question: 질문 텍스트

        Returns:
            키워드 집합
        """
        # 주요 키워드 패턴
        keyword_patterns = [
            # 질문 유형
            "지원동기", "입사 후", "장단점", "강점", "약점", "경험", "사례",
            "갈등", "협력", "팀워크", "리더십", "문제해결", "성과", "실패",
            "극복", "도전", "목표", "계획", "가치관", "인재상", "직무",
            # NCS 역량
            "의사소통", "소통", "문제해결", "자기개발", "대인관계", "갈등관리",
            "조직이해", "기술", "정보", "수리", "윤리", "책임",
            # 상황/경험
            "팀", "프로젝트", "업무", "성공", "실패", "어려움", "노력",
            "결과", "성장", "학습", "개선", "혁신",
        ]

        keywords = set()
        question_lower = question.lower()

        for kw in keyword_patterns:
            if kw in question or kw.lower() in question_lower:
                keywords.add(kw)

        return keywords

    def _calculate_similarity(
        self,
        question_keywords: set[str],
        past_question: str,
        past_keywords: list[str],
        past_ncs: list[str],
    ) -> tuple[float, list[str]]:
        """유사도 계산.

        Args:
            question_keywords: 현재 질문 키워드
            past_question: 과거 질문 텍스트
            past_keywords: 과거 질문 키워드
            past_ncs: 과거 질문 NCS 카테고리

        Returns:
            (유사도, 일치 키워드 목록)
        """
        matched: list[str] = []
        total_weight = 0
        matched_weight = 0

        # 키워드 일치 확인
        all_past_keywords = set(past_keywords + past_ncs)

        for kw in question_keywords:
            total_weight += 1
            if kw in past_question or kw.lower() in past_question.lower():
                matched.append(kw)
                matched_weight += 1
            elif kw in all_past_keywords:
                matched.append(kw)
                matched_weight += 0.8  # 키워드 목록에만 있으면 80%

        # 과거 키워드가 현재 질문에 있는지도 확인
        for kw in all_past_keywords:
            if kw not in question_keywords and kw in str(question_keywords):
                # 이미 카운트되지 않은 경우
                continue

        if total_weight == 0:
            return 0, matched

        similarity = (matched_weight / max(total_weight, len(all_past_keywords) / 2)) * 100
        return min(similarity, 100), matched

    def analyze_position_skills(
        self, answer: str, position: str
    ) -> PositionSkillMatch:
        """직무별 우대사항 매칭 분석.

        Args:
            answer: 자소서 답변 텍스트
            position: 직무명

        Returns:
            직무별 스킬 매칭 결과
        """
        if not self._position_manager:
            return PositionSkillMatch()

        # 직무 데이터 가져오기
        position_data = self._position_manager.get_position(position)
        if not position_data:
            return PositionSkillMatch()

        requirements = position_data.get("common_requirements", {})
        if not requirements:
            return PositionSkillMatch()

        answer_lower = answer.lower()

        # 전공 매칭
        majors = requirements.get("majors", [])
        matched_majors: list[str] = []
        missing_majors: list[str] = []

        # 전공 관련 키워드 매핑 (전공명 + 관련 단어)
        major_keywords: dict[str, list[str]] = {
            "경영학": ["경영", "경영학", "마케팅", "인사", "조직", "재무", "회계"],
            "경제학": ["경제", "경제학", "거시", "미시", "금융"],
            "행정학": ["행정", "행정학", "공공", "정책"],
            "산업공학": ["산업공학", "IE", "품질", "생산", "물류", "SCM"],
            "통계학": ["통계", "통계학", "데이터", "분석", "확률"],
            "컴퓨터공학": ["컴퓨터", "IT", "개발", "프로그래밍", "소프트웨어", "코딩"],
            "전자공학": ["전자", "전자공학", "회로", "반도체", "임베디드"],
            "전기공학": ["전기", "전기공학", "전력", "배전", "송전"],
            "기계공학": ["기계", "기계공학", "설계", "CAD", "제조"],
            "화학공학": ["화학", "화학공학", "공정", "플랜트"],
            "토목공학": ["토목", "토목공학", "건설", "구조", "시공"],
            "건축공학": ["건축", "건축공학", "설계", "시공"],
            "환경공학": ["환경", "환경공학", "폐수", "대기", "폐기물"],
            "회계학": ["회계", "회계학", "재무", "세무", "감사"],
            "법학": ["법", "법학", "법률", "계약", "소송"],
            "심리학": ["심리", "심리학", "상담", "인사"],
            "사회학": ["사회", "사회학", "조사", "통계"],
        }

        for major in majors:
            keywords = major_keywords.get(major, [major])
            found = False
            for kw in keywords:
                if kw.lower() in answer_lower or kw in answer:
                    matched_majors.append(major)
                    found = True
                    break
            if not found:
                missing_majors.append(major)

        # 자격증 매칭
        certifications = requirements.get("certifications", [])
        matched_certs: list[str] = []
        missing_certs: list[str] = []

        # 자격증 관련 키워드 매핑
        cert_keywords: dict[str, list[str]] = {
            "경영지도사": ["경영지도사"],
            "공인회계사(CPA)": ["CPA", "공인회계사", "회계사"],
            "투자자산운용사": ["투자자산운용", "펀드매니저"],
            "재경관리사": ["재경관리사", "재경"],
            "컴퓨터활용능력": ["컴퓨터활용능력", "컴활", "엑셀", "Excel"],
            "정보처리기사": ["정보처리기사", "정처기"],
            "빅데이터분석기사": ["빅데이터", "데이터분석"],
            "SQLD": ["SQLD", "SQL", "데이터베이스"],
            "PMP": ["PMP", "프로젝트관리"],
            "전기기사": ["전기기사", "전기"],
            "전기공사기사": ["전기공사기사"],
            "전기산업기사": ["전기산업기사"],
            "소방설비기사": ["소방설비기사", "소방"],
            "건축기사": ["건축기사"],
            "토목기사": ["토목기사"],
            "산업안전기사": ["산업안전기사", "안전관리"],
            "품질관리기사": ["품질관리기사", "QC"],
            "한국사능력검정시험": ["한국사", "한능검"],
            "TOEIC": ["토익", "TOEIC"],
            "OPIC": ["오픽", "OPIC"],
            "변호사": ["변호사", "사법시험"],
            "세무사": ["세무사"],
            "노무사": ["노무사", "공인노무사"],
        }

        for cert in certifications:
            keywords = cert_keywords.get(cert, [cert])
            found = False
            for kw in keywords:
                if kw.lower() in answer_lower or kw in answer:
                    matched_certs.append(cert)
                    found = True
                    break
            if not found:
                missing_certs.append(cert)

        # 스킬 매칭
        skills = requirements.get("skills", [])
        matched_skills: list[str] = []
        missing_skills: list[str] = []

        # 스킬 관련 키워드 매핑
        skill_keywords: dict[str, list[str]] = {
            "전략적 사고": ["전략", "전략적", "기획", "분석"],
            "데이터 분석": ["데이터", "분석", "통계", "빅데이터", "AI", "머신러닝"],
            "문서 작성": ["문서", "보고서", "작성", "기획서"],
            "프레젠테이션": ["PT", "발표", "프레젠테이션"],
            "MS Office 활용": ["엑셀", "Excel", "파워포인트", "PPT", "워드", "Office"],
            "커뮤니케이션": ["소통", "커뮤니케이션", "의사소통", "협업"],
            "문제해결": ["문제해결", "해결", "개선"],
            "프로젝트 관리": ["프로젝트", "PM", "일정관리"],
            "영어": ["영어", "English", "TOEIC", "OPIC", "회화"],
            "리더십": ["리더십", "리더", "팀장"],
            "팀워크": ["팀워크", "협업", "협력", "팀"],
            "Python": ["Python", "파이썬"],
            "Java": ["Java", "자바"],
            "SQL": ["SQL", "데이터베이스", "DB"],
            "CAD": ["CAD", "설계", "AutoCAD"],
            "ERP": ["ERP", "SAP"],
            "회계": ["회계", "재무", "결산", "원가"],
            "세무": ["세무", "세금", "부가세"],
            "인사관리": ["인사", "HR", "채용", "교육"],
            "마케팅": ["마케팅", "홍보", "광고", "브랜드"],
        }

        for skill in skills:
            keywords = skill_keywords.get(skill, [skill])
            found = False
            for kw in keywords:
                if kw.lower() in answer_lower or kw in answer:
                    matched_skills.append(skill)
                    found = True
                    break
            if not found:
                missing_skills.append(skill)

        # 전체 매칭률 계산
        total_items = len(majors) + len(certifications) + len(skills)
        matched_items = len(matched_majors) + len(matched_certs) + len(matched_skills)

        match_rate = (matched_items / total_items * 100) if total_items > 0 else 0

        # 추천 메시지 생성
        recommendation = ""
        if match_rate >= 70:
            recommendation = "직무 요구사항을 잘 반영하고 있습니다."
        elif match_rate >= 40:
            missing_items = []
            if missing_certs:
                missing_items.append(f"자격증({', '.join(missing_certs[:2])})")
            if missing_skills:
                missing_items.append(f"스킬({', '.join(missing_skills[:2])})")
            if missing_items:
                recommendation = f"다음 항목을 추가로 언급하면 좋습니다: {', '.join(missing_items)}"
        else:
            recommendation = "직무 관련 경험, 자격증, 스킬을 더 구체적으로 언급해 보세요."

        return PositionSkillMatch(
            matched_majors=matched_majors,
            missing_majors=missing_majors,
            matched_certifications=matched_certs,
            missing_certifications=missing_certs,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            overall_match_rate=round(match_rate, 1),
            recommendation=recommendation,
        )

    def generate_sample_answers(
        self,
        interview_questions: list[InterviewQuestion],
        answer: str,
        org_data: dict[str, Any] | None,
    ) -> list[InterviewQuestion]:
        """면접 질문에 대한 예시 답변 생성 (자소서 기반).

        Args:
            interview_questions: 면접 질문 목록
            answer: 자소서 답변 텍스트
            org_data: 기관 데이터

        Returns:
            예시 답변이 추가된 면접 질문 목록
        """
        if not interview_questions or not answer:
            return interview_questions

        # 자소서에서 구체적인 경험/키워드 추출 - 캐시된 패턴 사용
        sentences = _SENTENCE_SPLIT_PATTERN.split(answer)

        # 수치가 포함된 문장 추출 - 캐시된 패턴 사용
        quantified_experiences: list[str] = []
        for sentence in sentences:
            if len(sentence) > 20 and _NUMBER_PATTERN.search(sentence):
                quantified_experiences.append(sentence.strip())

        # 활동/경험 관련 문장 추출 - 캐시된 패턴 사용
        activity_experiences: list[str] = []
        for sentence in sentences:
            if len(sentence) > 30 and _EXPERIENCE_PATTERN.search(sentence):
                activity_experiences.append(sentence.strip())

        # 기관 정보
        core_values = org_data.get("core_values", []) if org_data else []
        org_name = org_data.get("name", "") if org_data else ""
        mission = org_data.get("mission", "") if org_data else ""

        # 질문별 예시 답변 생성
        updated_questions: list[InterviewQuestion] = []

        for q in interview_questions:
            sample = ""
            q_text = q.question

            # 지원동기 질문
            if "지원" in q_text and ("동기" in q_text or "이유" in q_text or "왜" in q_text):
                sample = self._generate_motivation_sample(org_name, core_values, mission, activity_experiences)

            # 장단점 질문
            elif "장단점" in q_text or ("장점" in q_text and "단점" in q_text):
                sample = self._generate_strength_weakness_sample(quantified_experiences, activity_experiences)

            # 경험/사례 질문 (STAR 기법)
            elif any(kw in q_text for kw in ["경험", "사례", "해결", "극복", "어려움", "문제"]):
                sample = self._generate_star_sample(q_text, quantified_experiences, activity_experiences)

            # 입사 후 포부
            elif "입사" in q_text and ("포부" in q_text or "계획" in q_text or "목표" in q_text):
                sample = self._generate_aspiration_sample(org_name, mission, activity_experiences)

            # 갈등/협력 질문
            elif any(kw in q_text for kw in ["갈등", "의견", "충돌", "협력", "팀워크"]):
                sample = self._generate_conflict_sample(activity_experiences)

            # 리더십 질문
            elif any(kw in q_text for kw in ["리더", "이끌", "주도"]):
                sample = self._generate_leadership_sample(quantified_experiences, activity_experiences)

            # 기타 - 구체적 답변 제시
            else:
                sample = self._generate_general_sample(q_text, quantified_experiences, activity_experiences, org_name)

            # 새 객체 생성
            updated_questions.append(InterviewQuestion(
                question=q.question,
                is_frequent=q.is_frequent,
                years=q.years,
                answer_tips=q.answer_tips,
                sample_answer=sample,
            ))

        return updated_questions

    def _generate_motivation_sample(
        self, org_name: str, core_values: list[str], mission: str, experiences: list[str]
    ) -> str:
        """지원동기 예시 답변 생성."""
        sample = ""
        if org_name:
            sample = f'"{org_name}이(가) 추구하는 '
            if core_values:
                sample += f"'{core_values[0]}' 가치는 "
            elif mission:
                sample += f"'{mission[:30]}...' 미션은 "
            else:
                sample += "비전은 "

        if experiences:
            exp = experiences[0][:80] + ("..." if len(experiences[0]) > 80 else "")
            sample += f'제가 {exp} 과정에서 느꼈던 가치관과 일치합니다. '
        else:
            sample += "제가 추구하는 방향과 일치합니다. "

        sample += '이러한 이유로 이 조직에서 전문성을 쌓고 기여하고 싶습니다."'
        return sample

    def _generate_strength_weakness_sample(
        self, quantified: list[str], activities: list[str]
    ) -> str:
        """장단점 예시 답변 생성."""
        sample = '"저의 강점은 끈기 있게 목표를 달성하는 것입니다. '
        if quantified:
            exp = quantified[0][:70] + ("..." if len(quantified[0]) > 70 else "")
            sample += f"실제로 {exp} 결과를 이끌어냈습니다. "
        elif activities:
            exp = activities[0][:70] + ("..." if len(activities[0]) > 70 else "")
            sample += f"예를 들어 {exp} 과정에서 이를 증명했습니다. "

        sample += '단점은 때로 세부사항에 집착하는 경향이 있으나, 최근에는 우선순위를 먼저 정하는 습관으로 개선하고 있습니다."'
        return sample

    def _generate_star_sample(
        self, question: str, quantified: list[str], activities: list[str]
    ) -> str:
        """STAR 기법 기반 예시 답변 생성."""
        # 질문에 따라 적절한 경험 선택
        relevant_exp = ""
        if quantified:
            relevant_exp = quantified[0]
        elif activities:
            relevant_exp = activities[0]

        if relevant_exp:
            exp_short = relevant_exp[:60] + ("..." if len(relevant_exp) > 60 else "")
            sample = f'"[상황] {exp_short}을(를) 수행할 때, '
            sample += '[과제] 기한 내 목표 달성이 필요했습니다. '
            sample += '[행동] 저는 우선순위를 정하고 단계별로 접근했으며, '
            sample += '[결과] 성공적으로 완수하여 팀에 기여할 수 있었습니다."'
        else:
            sample = '"[상황] 구체적인 배경 설명 → [과제] 해결해야 할 문제 → [행동] 본인이 취한 구체적 행동 → [결과] 정량적 성과나 배운 점으로 구성하세요."'

        return sample

    def _generate_aspiration_sample(
        self, org_name: str, mission: str, experiences: list[str]
    ) -> str:
        """입사 후 포부 예시 답변 생성."""
        sample = '"입사 후 1-2년간은 '
        if org_name:
            sample += f'{org_name}의 핵심 업무 프로세스를 익히며 실무 역량을 쌓겠습니다. '
        else:
            sample += "실무 역량을 쌓고 업무 프로세스를 익히겠습니다. "

        if experiences:
            exp = experiences[0][:50] + ("..." if len(experiences[0]) > 50 else "")
            sample += f"이전 {exp} 경험을 바탕으로 "

        sample += '3-5년 차에는 담당 분야의 전문가로 성장하여 후배 양성에도 기여하고, '
        sample += '장기적으로는 조직의 핵심 인재로서 발전에 이바지하겠습니다."'
        return sample

    def _generate_conflict_sample(self, activities: list[str]) -> str:
        """갈등 해결 예시 답변 생성."""
        sample = '"팀 프로젝트에서 방향성에 대한 의견 차이가 있었습니다. '
        if activities:
            exp = activities[0][:50] + ("..." if len(activities[0]) > 50 else "")
            sample += f'{exp} 진행 중, '

        sample += '저는 먼저 각자의 의견을 충분히 경청한 후, '
        sample += '공통 목표를 재확인하는 시간을 가졌습니다. '
        sample += '이후 장단점을 객관적으로 비교하여 합의점을 도출했고, '
        sample += '결과적으로 모두가 만족하는 방향으로 프로젝트를 완수했습니다."'
        return sample

    def _generate_leadership_sample(
        self, quantified: list[str], activities: list[str]
    ) -> str:
        """리더십 예시 답변 생성."""
        sample = '"'
        if activities:
            exp = activities[0][:60] + ("..." if len(activities[0]) > 60 else "")
            sample += f'{exp}에서 팀을 이끈 경험이 있습니다. '
        else:
            sample += '팀 프로젝트에서 리더를 맡은 경험이 있습니다. '

        sample += '저는 먼저 팀원들의 강점을 파악하여 적재적소에 역할을 배분했고, '
        sample += '정기적인 진행 상황 공유를 통해 일정을 관리했습니다. '

        if quantified:
            exp = quantified[0][:40] + ("..." if len(quantified[0]) > 40 else "")
            sample += f'그 결과 {exp} 성과를 달성했습니다."'
        else:
            sample += '그 결과 목표를 성공적으로 달성했습니다."'

        return sample

    def _generate_general_sample(
        self, question: str, quantified: list[str], activities: list[str], org_name: str
    ) -> str:
        """일반 질문 예시 답변 생성."""
        sample = '"'

        # 질문에서 키워드 추출하여 관련 경험 연결
        if quantified:
            exp = quantified[0][:70] + ("..." if len(quantified[0]) > 70 else "")
            sample += f'{exp}의 경험을 통해 '
        elif activities:
            exp = activities[0][:70] + ("..." if len(activities[0]) > 70 else "")
            sample += f'{exp} 과정에서 '
        else:
            sample += '관련 경험을 통해 '

        sample += '이 역량을 키워왔습니다. '
        if org_name:
            sample += f'{org_name}에서 이러한 역량을 발휘하여 '
        sample += '조직에 기여하고 싶습니다."'

        return sample

    def _format_model_answer_paragraphs(self, model_answer: str) -> str:
        """모범 답안에 문단 구분(줄바꿈)을 추가.

        LLM이 줄바꿈 없이 연속된 텍스트를 생성한 경우,
        적절한 위치에 문단 구분을 추가합니다.

        Args:
            model_answer: 원본 모범 답안

        Returns:
            문단이 구분된 모범 답안
        """
        if not model_answer:
            return model_answer

        # 이미 줄바꿈이 있으면 그대로 반환
        if "\n" in model_answer:
            return model_answer

        # 문단 구분 기준 패턴 (새로운 문단 시작을 나타내는 표현들)
        paragraph_starters = [
            "이러한 경험",
            "이를 계기로",
            "이후",
            "또한",
            "한편",
            "나아가",
            "앞으로",
            "입사 후",
            "특히",
            "결과적으로",
            "이를 통해",
            "이처럼",
        ]

        result = model_answer
        for starter in paragraph_starters:
            # 문장 중간이 아닌 새로운 문장 시작에서만 구분
            # ". 이러한" 또는 "다. 이러한" 패턴을 찾아서 줄바꿈 추가
            import re
            pattern = rf'([.!?])\s+({starter})'
            result = re.sub(pattern, r'\1\n\n\2', result)

        return result

    def _get_default_interview_tips(self, category: str, question: str = "") -> str:
        """카테고리별 기본 면접 조언 생성.

        Args:
            category: 질문 카테고리 (자기소개, 지원동기 등)
            question: 원본 질문 (상세 팁 생성용)

        Returns:
            해당 카테고리에 맞는 면접 조언
        """
        # 카테고리별 상세 조언 매핑
        tips_map = {
            "자기소개": (
                "1분 이내로 간결하게 준비하세요. "
                "핵심 경험 1-2개와 지원 직무와의 연결점을 강조하고, "
                "마지막에 입사 후 포부를 짧게 덧붙이세요."
            ),
            "지원동기": (
                "기관의 미션/비전과 본인의 가치관 연결이 핵심입니다. "
                "해당 기관만의 차별점(사업, 정책)을 언급하고, "
                "구체적 기여 방안을 제시하세요."
            ),
            "기관이해": (
                "주요 사업 3가지 이상 숙지하세요. "
                "최근 뉴스, 정책 방향, 신사업을 파악하고, "
                "지원 직무와 연계하여 설명하세요."
            ),
            "직무역량": (
                "STAR 기법(상황-과제-행동-결과)으로 답변하세요. "
                "정량적 성과(숫자, 비율)를 포함하고, "
                "해당 경험이 직무에 어떻게 활용될지 연결하세요."
            ),
            "경험/역량": (
                "STAR 기법으로 구체적 사례를 준비하세요. "
                "팀 프로젝트에서의 역할과 기여를 명확히 하고, "
                "배운 점과 성장 포인트를 강조하세요."
            ),
            "인성/가치관": (
                "솔직하되, 직무 연관성을 고려하세요. "
                "단점 질문시 극복 노력과 개선 결과를 함께 언급하고, "
                "구체적 에피소드로 진정성을 보여주세요."
            ),
            "문제해결": (
                "문제 상황을 객관적으로 설명하고, "
                "본인의 분석 과정과 해결 방안을 단계별로 제시하세요. "
                "결과와 함께 배운 교훈을 덧붙이세요."
            ),
            "조직적합성": (
                "기관의 핵심가치와 인재상을 숙지하세요. "
                "본인의 경험 중 해당 가치를 실천한 사례를 준비하고, "
                "조직 문화에 적응할 수 있음을 보여주세요."
            ),
            "발표": (
                "서론-본론-결론 구조로 논리적으로 구성하세요. "
                "핵심 메시지 1-2개에 집중하고, "
                "시간 배분(준비 15분, 발표 5분 등)을 철저히 지키세요."
            ),
            "토론": (
                "찬반 양쪽 논거를 미리 준비하세요. "
                "상대 의견을 경청하고 존중하는 태도를 보이며, "
                "논리적 근거와 데이터로 주장을 뒷받침하세요."
            ),
            "상황대처": (
                "침착하게 상황을 파악하는 모습을 보여주세요. "
                "우선순위를 정하고 단계적 해결 방안을 제시하며, "
                "유사 경험이 있다면 함께 언급하세요."
            ),
            "비전": (
                "단기(1-2년)와 장기(5-10년) 목표를 구분하여 제시하세요. "
                "기관의 사업 방향과 연계된 구체적 성장 계획을 말하고, "
                "해당 기관에서 이루고 싶은 전문성을 명확히 하세요."
            ),
            "포부": (
                "입사 후 1-2년 내 달성할 구체적 목표를 제시하세요. "
                "기관의 미션과 연계된 기여 방안을 설명하고, "
                "해당 직무에서 발휘할 역량을 강조하세요."
            ),
            "인성": (
                "솔직하되, 직무 연관성을 고려하세요. "
                "단점 질문시 극복 노력과 개선 결과를 함께 언급하고, "
                "구체적 에피소드로 진정성을 보여주세요."
            ),
            "자기분석": (
                "객관적인 자기 분석 능력을 보여주세요. "
                "강점은 구체적 사례로, 약점은 개선 노력과 함께 언급하고, "
                "지원 직무와의 연관성을 항상 고려하세요."
            ),
            "경험": (
                "STAR 기법으로 구체적 사례를 준비하세요. "
                "팀 프로젝트에서의 역할과 기여를 명확히 하고, "
                "배운 점과 성장 포인트를 강조하세요."
            ),
        }

        # 카테고리 매칭 (부분 일치 허용)
        for key, tip in tips_map.items():
            if key in category or category in key:
                return tip

        # 질문 내용 기반 추가 매칭
        if "장단점" in question or "단점" in question or "장점" in question:
            return tips_map.get("인성/가치관", "")
        if "갈등" in question or "협업" in question or "팀" in question:
            return (
                "갈등 상황을 객관적으로 설명하고, "
                "본인의 중재/해결 노력을 구체적으로 제시하세요. "
                "결과적으로 팀에 미친 긍정적 영향을 강조하세요."
            )
        if "포부" in question or "입사 후" in question or "목표" in question:
            return (
                "단기(1-2년)와 장기(5년) 목표를 구분하여 제시하세요. "
                "기관의 사업 방향과 연계된 구체적 계획을 말하고, "
                "실현 가능한 현실적인 목표를 설정하세요."
            )

        # 기본 조언
        return (
            "질문의 핵심을 파악하고 간결하게 답변하세요. "
            "구체적 경험과 사례로 답변에 신뢰성을 더하고, "
            "지원 기관/직무와의 연관성을 항상 고려하세요."
        )

    def _get_interview_detail(self, interview_data: dict[str, Any] | None) -> InterviewDetailInfo:
        """면접 상세 정보 추출.

        Args:
            interview_data: 면접 데이터

        Returns:
            면접 상세 정보
        """
        if not interview_data:
            return InterviewDetailInfo()

        interview_format = interview_data.get("interview_format", {})

        # 고빈도 질문 추출 (상위 5개)
        questions = interview_data.get("questions", [])
        frequent_questions: list[FrequentInterviewQuestion] = []

        # frequency가 high인 것 우선, 그 다음 medium
        high_freq = [q for q in questions if q.get("frequency") == "high"]
        medium_freq = [q for q in questions if q.get("frequency") == "medium"]

        for q in (high_freq + medium_freq)[:5]:
            question_text = q.get("question", "")
            category = q.get("category", "")
            existing_tips = q.get("tips", "")

            # 기존 팁이 없거나 너무 짧으면 (30자 미만) 카테고리 기반 기본 팁 생성
            if not existing_tips or len(existing_tips) < 30:
                existing_tips = self._get_default_interview_tips(category, question_text)

            frequent_questions.append(FrequentInterviewQuestion(
                question=question_text,
                category=category,
                frequency=q.get("frequency", "medium"),
                tips=existing_tips,
            ))

        return InterviewDetailInfo(
            format_type=interview_format.get("type", ""),
            stages=interview_format.get("stages", []),
            duration=interview_format.get("duration", ""),
            difficulty=interview_format.get("difficulty", ""),
            pass_rate=interview_format.get("positive_rate", ""),
            frequent_questions=frequent_questions,
        )

    def _parse_response_v2(
        self,
        llm_response: str,
        request: ResumeAnalysisRequest,
        org_data: dict[str, Any] | None = None,
        interview_data: dict[str, Any] | None = None,
        past_questions_data: list[dict[str, Any]] | None = None,
        core_value_scores: list[CoreValueScore] | None = None,
        ncs_competency_scores: list[NCSCompetencyScore] | None = None,
        position_skill_match: PositionSkillMatch | None = None,
    ) -> NewResumeAnalysisResponse:
        """Parse LLM response into new structured response format.

        Args:
            llm_response: Raw LLM JSON response
            request: Original request for length calculation
            org_data: Organization data from knowledge DB
            interview_data: Interview data from knowledge DB
            past_questions_data: Past essay questions from knowledge DB

        Returns:
            Validated new response object
        """
        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON (v2): {e}")
            logger.debug(f"Raw response: {llm_response[:500]}...")
            # Return default response structure on parse error
            data = {
                "overall_score": 50,
                "overall_grade": "보통",
                "overall_summary": "분석 중 오류가 발생했습니다.",
                "strengths": [],
                "improvements": [],
                "keyword_analysis": {"found_keywords": [], "missing_keywords": [], "match_rate": 0},
                "interview_questions": [],
                "model_answer_checklist": {},
                "model_answer": "",
                "model_answer_length": 0,
            }

        # Calculate actual length check
        length_check = self.calculate_length_check(request.answer, request.maxLength)

        # Build organization info directly from knowledge DB (NOT from LLM)
        recent_news_raw: list[dict[str, Any]] = []
        if org_data:
            # 채용 뉴스
            for news in org_data.get("recruitment_news", []):
                recent_news_raw.append({
                    "title": news.get("title", ""),
                    "date": news.get("date", ""),
                    "category": "채용",
                    "url": news.get("url", ""),
                })
            # 사업 뉴스
            for news in org_data.get("business_news", []):
                recent_news_raw.append({
                    "title": news.get("title", ""),
                    "date": news.get("date", ""),
                    "category": "사업",
                    "url": news.get("url", ""),
                })

        # Sort by date descending (most recent first)
        def parse_date_key(item: dict[str, Any]) -> str:
            date_str = item.get("date", "")
            # Handle various date formats: "2025-09", "2025", "2025-04"
            if not date_str:
                return "0000-00"
            # Normalize to "YYYY-MM" format for sorting
            if len(date_str) == 4:  # "2025" -> "2025-12" (assume end of year)
                return f"{date_str}-12"
            elif len(date_str) == 7:  # "2025-09" already correct
                return date_str
            return date_str[:7] if len(date_str) >= 7 else f"{date_str}-00"

        recent_news_raw.sort(key=parse_date_key, reverse=True)

        # Convert to RecentNewsItem (max 5)
        recent_news = [
            RecentNewsItem(
                title=item["title"],
                date=item["date"],
                category=item["category"],
                url=item.get("url", ""),
            )
            for item in recent_news_raw[:5]
        ]

        # Get info from org_data (knowledge DB)
        website = ""
        recruitment_process = []
        data_updated_at = ""
        core_values = []
        talent_image = ""
        org_name = ""
        if org_data:
            org_name = org_data.get("name", "")
            website = org_data.get("website", "")
            core_values = org_data.get("core_values", [])
            talent_image = org_data.get("talent_image", "")
            recruitment_process = org_data.get("recruitment", {}).get("process", [])
            metadata = org_data.get("metadata", {})
            data_updated_at = metadata.get("last_updated", "")

        # Get interview keywords and statistics from interview_data
        interview_keywords = []
        interview_difficulty = ""
        interview_pass_rate = ""
        if interview_data:
            interview_format = interview_data.get("interview_format", {})
            interview_difficulty = interview_format.get("difficulty", "")
            interview_pass_rate = interview_format.get("positive_rate", "")

            # Extract keywords from high-frequency questions
            questions = interview_data.get("questions", [])
            keyword_set: set[str] = set()
            for q in questions:
                if q.get("frequency") in ("high", "medium"):
                    cat = q.get("category", "")
                    if cat:
                        keyword_set.add(cat)
                for ncs in q.get("ncs_competencies", [])[:2]:
                    keyword_set.add(ncs)
            interview_keywords = list(keyword_set)[:8]

        organization_info = OrganizationInfo(
            name=org_name,
            website=website,
            core_values=core_values,
            talent_image=talent_image,
            recent_news=recent_news,
            interview_keywords=interview_keywords,
            recruitment_process=recruitment_process,
            interview_difficulty=interview_difficulty,
            interview_pass_rate=interview_pass_rate,
            data_updated_at=data_updated_at,
        )

        # Parse strengths
        strengths = [
            StrengthItem(
                title=s.get("title", ""),
                score=s.get("score", 5),
                quote=s.get("quote", ""),
                evaluation=s.get("evaluation", ""),
            )
            for s in data.get("strengths", [])
        ]

        # Parse improvements
        improvements = [
            ImprovementItem(
                title=i.get("title", ""),
                score=i.get("score", 5),
                problem=i.get("problem", ""),
                current_text=i.get("current_text", ""),
                improved_text=i.get("improved_text", ""),
            )
            for i in data.get("improvements", [])
        ]

        # Parse keyword analysis
        keyword_data = data.get("keyword_analysis", {})
        keyword_analysis = KeywordAnalysis(
            found_keywords=keyword_data.get("found_keywords", []),
            missing_keywords=keyword_data.get("missing_keywords", []),
            match_rate=keyword_data.get("match_rate", 0),
        )

        # Parse interview questions with multiple years support
        interview_questions = [
            InterviewQuestion(
                question=q.get("question", ""),
                is_frequent=q.get("is_frequent", False),
                years=q.get("years", []) if isinstance(q.get("years"), list) else ([q.get("year")] if q.get("year") else []),
                answer_tips=q.get("answer_tips", ""),
            )
            for q in data.get("interview_questions", [])
        ]

        # Parse past questions from knowledge DB
        past_questions = []
        if past_questions_data:
            past_questions = [
                PastQuestion(
                    year=pq.get("year", 0),
                    half=pq.get("half", ""),
                    question=pq.get("question", ""),
                    char_limit=pq.get("char_limit", 0),
                    is_prediction=pq.get("is_prediction", False),
                )
                for pq in past_questions_data
            ]

        # Get model answer checklist (internal use for quality assurance)
        model_answer_checklist = data.get("model_answer_checklist", {})

        # Get model answer - always calculate actual length (don't trust LLM's count)
        model_answer = data.get("model_answer", "")
        # 문단 구분 후처리: LLM이 줄바꿈을 넣지 않은 경우 자동으로 문단 구분
        model_answer = self._format_model_answer_paragraphs(model_answer)
        # Calculate actual length (excluding whitespace at start/end but keeping internal)
        model_answer_length = len(model_answer.strip())

        # Check for common mistakes/warnings
        warnings = self.check_warnings(request.answer, request.organization)

        # Get interview detail info
        interview_detail = self._get_interview_detail(interview_data)

        # Use pre-computed core value scores or compute if not provided
        if core_value_scores is None:
            core_value_scores = self.analyze_core_values(request.answer, core_values)

        # Use pre-computed NCS competency scores or compute if not provided
        if ncs_competency_scores is None:
            ncs_competency_scores = self.analyze_ncs_competencies(request.answer, request.position)

        # Find similar past questions
        similar_questions = self.find_similar_questions(request.question, request.organization)

        # Use pre-computed position skill match or compute if not provided
        if position_skill_match is None:
            position_skill_match = self.analyze_position_skills(request.answer, request.position)

        # Generate sample answers for interview questions
        interview_questions = self.generate_sample_answers(
            interview_questions, request.answer, org_data
        )

        return NewResumeAnalysisResponse(
            overall_score=data.get("overall_score", 50),
            overall_grade=data.get("overall_grade", "보통"),
            overall_summary=data.get("overall_summary", ""),
            length_check=length_check,
            warnings=warnings,
            organization_info=organization_info,
            interview_detail=interview_detail,
            strengths=strengths,
            improvements=improvements,
            keyword_analysis=keyword_analysis,
            core_value_scores=core_value_scores,
            ncs_competency_scores=ncs_competency_scores,
            similar_questions=similar_questions,
            position_skill_match=position_skill_match,
            interview_questions=interview_questions,
            past_questions=past_questions,
            model_answer_checklist=model_answer_checklist,
            model_answer=model_answer,
            model_answer_length=model_answer_length,
        )
