"""Response schemas for resume analysis API."""

from pydantic import BaseModel, Field


class LengthCheck(BaseModel):
    """Length check result schema."""

    current: int = Field(..., description="현재 글자 수")
    max: int = Field(..., description="최대 글자 수")
    percentage: float = Field(..., description="사용률 (%)")
    status: str = Field(..., description="상태 (short, optimal, over)")


class FeedbackItem(BaseModel):
    """Individual feedback item schema."""

    category: str = Field(..., description="피드백 카테고리")
    score: int = Field(..., description="점수 (1-10)", ge=1, le=10)
    comment: str = Field(..., description="피드백 코멘트")
    suggestion: str | None = Field(default=None, description="개선 제안")


class KeywordAnalysis(BaseModel):
    """Keyword analysis result schema."""

    found_keywords: list[str] = Field(..., description="발견된 키워드 목록")
    missing_keywords: list[str] = Field(..., description="누락된 키워드 목록")
    match_rate: float = Field(..., description="키워드 매칭률 (%)")


class NCSItem(BaseModel):
    """Individual NCS competency evaluation item."""

    competency: str = Field(..., description="NCS 역량명")
    score: int = Field(..., description="역량 점수 (1-10)", ge=1, le=10)
    evidence: str = Field(..., description="자소서에서 발견된 근거")
    suggestion: str | None = Field(default=None, description="개선 제안")


class NCSAnalysis(BaseModel):
    """NCS competency analysis result schema."""

    evaluated_competencies: list[NCSItem] = Field(..., description="평가된 NCS 역량 목록")
    strongest: str = Field(..., description="가장 강점인 역량")
    weakest: str = Field(..., description="보완이 필요한 역량")
    overall_comment: str = Field(..., description="NCS 역량 종합 평가")


class TalentAnalysis(BaseModel):
    """Talent image comparison analysis schema."""

    match_score: int = Field(..., description="인재상 부합도 점수 (1-10)", ge=1, le=10)
    matched_traits: list[str] = Field(..., description="인재상에서 잘 드러난 특성 목록")
    missing_traits: list[str] = Field(..., description="인재상에서 부족한 특성 목록")
    overall_comment: str = Field(..., description="인재상 부합도 종합 평가")
    improvement_tips: list[str] = Field(..., description="인재상에 맞추기 위한 개선 팁")


# === 새로운 스키마 (리디자인) ===


class RecentNewsItem(BaseModel):
    """최근 뉴스 항목."""

    title: str = Field(..., description="뉴스 제목")
    date: str = Field(default="", description="날짜 (YYYY-MM 형식)")
    category: str = Field(default="", description="카테고리 (채용/사업)")
    url: str = Field(default="", description="뉴스 링크 URL")


class PastQuestion(BaseModel):
    """자소서 기출/예상 문항."""

    year: int = Field(..., description="출제 연도")
    half: str = Field(default="", description="상/하반기")
    question: str = Field(..., description="문항 내용")
    char_limit: int = Field(default=0, description="글자 수 제한")
    is_prediction: bool = Field(default=False, description="출제 예상 여부 (True면 예상, False면 기출)")


class WarningItem(BaseModel):
    """자소서 작성 경고/주의사항 항목."""

    type: str = Field(..., description="경고 유형 (blind_violation, abstract_expression, no_result, etc)")
    severity: str = Field(..., description="심각도 (high, medium, low)")
    message: str = Field(..., description="경고 메시지")
    detected_text: str = Field(default="", description="발견된 텍스트")
    suggestion: str = Field(default="", description="개선 제안")


class FrequentInterviewQuestion(BaseModel):
    """고빈도 면접 질문 항목."""

    question: str = Field(..., description="면접 질문")
    category: str = Field(..., description="질문 카테고리")
    frequency: str = Field(..., description="출제 빈도 (high, medium)")
    tips: str = Field(default="", description="답변 팁")


class InterviewDetailInfo(BaseModel):
    """면접 상세 정보."""

    format_type: str = Field(default="", description="면접 형식 (PT면접, 토론면접, 인성면접 등)")
    stages: list[str] = Field(default_factory=list, description="전형 단계")
    duration: str = Field(default="", description="면접 시간")
    difficulty: str = Field(default="", description="면접 난이도")
    pass_rate: str = Field(default="", description="면접 합격률")
    frequent_questions: list[FrequentInterviewQuestion] = Field(
        default_factory=list, description="고빈도 면접 질문 (상위 5개)"
    )


class OrganizationInfo(BaseModel):
    """기관 정보 요약 (분석 결과 표시용)."""

    name: str = Field(..., description="기관명")
    website: str = Field(default="", description="공식 홈페이지 URL")
    core_values: list[str] = Field(..., description="핵심가치 목록")
    talent_image: str = Field(..., description="인재상")
    recent_news: list[RecentNewsItem] = Field(
        default_factory=list, description="최근 동향 (채용 + 사업)"
    )
    interview_keywords: list[str] = Field(..., description="면접 준비 키워드")
    recruitment_process: list[str] = Field(
        default_factory=list, description="채용 프로세스"
    )
    interview_difficulty: str = Field(default="", description="면접 난이도")
    interview_pass_rate: str = Field(default="", description="면접 합격률")
    data_updated_at: str = Field(default="", description="데이터 기준일")


class StrengthItem(BaseModel):
    """잘한 점 항목."""

    title: str = Field(..., description="평가 항목명")
    score: int = Field(..., description="점수 (1-10)", ge=1, le=10)
    quote: str = Field(..., description="자소서에서 해당 부분 인용")
    evaluation: str = Field(..., description="왜 잘했는지 평가")


class ImprovementItem(BaseModel):
    """개선점 항목 (구체적 수정 예시 포함)."""

    title: str = Field(..., description="평가 항목명")
    score: int = Field(..., description="점수 (1-10)", ge=1, le=10)
    problem: str = Field(..., description="문제점 설명")
    current_text: str = Field(..., description="현재 작성 내용")
    improved_text: str = Field(..., description="수정 예시")


class InterviewQuestion(BaseModel):
    """예상 면접 질문."""

    question: str = Field(..., description="면접 질문")
    is_frequent: bool = Field(..., description="기출/빈출 여부")
    years: list[int] = Field(default_factory=list, description="기출 연도 목록 (최근 5년)")
    answer_tips: str = Field(..., description="답변 포인트")
    sample_answer: str = Field(default="", description="자소서 기반 예시 답변")


class CoreValueScore(BaseModel):
    """핵심가치별 점수 항목."""

    value: str = Field(..., description="핵심가치 이름")
    score: int = Field(..., description="점수 (1-10)", ge=1, le=10)
    found: bool = Field(..., description="자소서에서 해당 가치가 드러났는지 여부")
    evidence: str = Field(default="", description="자소서에서 발견된 근거 (있는 경우)")
    suggestion: str = Field(default="", description="개선 제안 (부족한 경우)")


class NCSCompetencyScore(BaseModel):
    """NCS 역량별 점수 항목."""

    code: str = Field(..., description="NCS 역량 코드")
    name: str = Field(..., description="NCS 역량명")
    importance: str = Field(..., description="중요도 (필수/중요/권장)")
    score: int = Field(..., description="점수 (1-10)", ge=1, le=10)
    found: bool = Field(..., description="자소서에서 해당 역량이 드러났는지 여부")
    evidence: str = Field(default="", description="자소서에서 발견된 근거")
    suggestion: str = Field(default="", description="개선 제안")


class SimilarQuestion(BaseModel):
    """유사 기출문항 항목."""

    year: int = Field(..., description="출제 연도")
    half: str = Field(default="", description="상/하반기")
    question: str = Field(..., description="기출 문항")
    similarity: float = Field(..., description="유사도 (0-100%)")
    char_limit: int = Field(default=0, description="글자 수 제한")
    matched_keywords: list[str] = Field(default_factory=list, description="일치하는 키워드")


class PositionSkillMatch(BaseModel):
    """직무별 우대사항 매칭 결과."""

    # 전공 매칭
    matched_majors: list[str] = Field(default_factory=list, description="자소서에서 언급된 관련 전공")
    missing_majors: list[str] = Field(default_factory=list, description="직무 권장 전공 중 미언급")

    # 자격증 매칭
    matched_certifications: list[str] = Field(default_factory=list, description="자소서에서 언급된 관련 자격증")
    missing_certifications: list[str] = Field(default_factory=list, description="직무 권장 자격증 중 미언급")

    # 스킬 매칭
    matched_skills: list[str] = Field(default_factory=list, description="자소서에서 언급된 관련 스킬")
    missing_skills: list[str] = Field(default_factory=list, description="직무 권장 스킬 중 미언급")

    # 종합
    overall_match_rate: float = Field(default=0, description="전체 매칭률 (%)")
    recommendation: str = Field(default="", description="개선 제안")


class NewResumeAnalysisResponse(BaseModel):
    """새로운 분석 결과 구조 (리디자인 버전)."""

    # 종합 평가
    overall_score: int = Field(..., description="종합 점수 (0-100)", ge=0, le=100)
    overall_grade: str = Field(..., description="등급 (우수/양호/보통/미흡)")
    overall_summary: str = Field(..., description="1-2문장 종합 평가")

    # 글자 수 체크
    length_check: LengthCheck = Field(..., description="글자 수 체크 결과")

    # 경고 사항 (공통 실수 체크)
    warnings: list[WarningItem] = Field(
        default_factory=list, description="자소서 작성 경고/주의사항"
    )

    # 기관 정보
    organization_info: OrganizationInfo = Field(..., description="기관 정보 요약")

    # 면접 상세 정보
    interview_detail: InterviewDetailInfo = Field(
        default_factory=InterviewDetailInfo, description="면접 상세 정보"
    )

    # 분석 결과
    strengths: list[StrengthItem] = Field(..., description="잘한 점 (상위 3개)")
    improvements: list[ImprovementItem] = Field(..., description="개선점 (상위 3개)")

    # 키워드 분석 (기존 유지)
    keyword_analysis: KeywordAnalysis = Field(..., description="키워드 분석 결과")

    # 핵심가치별 점수
    core_value_scores: list[CoreValueScore] = Field(
        default_factory=list, description="핵심가치별 반영 점수"
    )

    # NCS 역량별 점수
    ncs_competency_scores: list[NCSCompetencyScore] = Field(
        default_factory=list, description="NCS 역량별 반영 점수"
    )

    # 유사 기출문항
    similar_questions: list[SimilarQuestion] = Field(
        default_factory=list, description="현재 질문과 유사한 기출문항"
    )

    # 직무별 스킬 매칭
    position_skill_match: PositionSkillMatch = Field(
        default_factory=PositionSkillMatch, description="직무별 우대사항 매칭 결과"
    )

    # 면접 준비
    interview_questions: list[InterviewQuestion] = Field(..., description="예상 면접 질문")

    # 자소서 기출문항
    past_questions: list[PastQuestion] = Field(
        default_factory=list, description="이 기관의 자소서 기출문항"
    )

    # 모범 답안 생성 체크리스트 (내부용 - 프론트엔드에 전달하지 않음)
    model_answer_checklist: dict[str, list[str]] = Field(
        default_factory=dict, description="모범 답안 작성 시 반영할 요소 체크리스트"
    )

    # 모범 답안
    model_answer: str = Field(..., description="전체 재작성 모범 답안")
    model_answer_length: int = Field(..., description="모범 답안 글자 수")


# === 기존 스키마 (호환성 유지) ===


class ResumeAnalysisResponse(BaseModel):
    """Complete response schema for resume analysis."""

    overall_score: int = Field(..., description="종합 점수 (0-100)", ge=0, le=100)
    length_check: LengthCheck = Field(..., description="글자 수 체크 결과")
    feedbacks: list[FeedbackItem] = Field(..., description="상세 피드백 목록")
    keyword_analysis: KeywordAnalysis = Field(..., description="키워드 분석 결과")
    ncs_analysis: NCSAnalysis | None = Field(default=None, description="NCS 역량 분석 결과")
    talent_analysis: TalentAnalysis | None = Field(default=None, description="인재상 부합도 분석 결과")
    expected_questions: list[str] = Field(..., description="예상 면접 질문")
