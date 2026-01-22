"""LLM prompt templates."""

from typing import TYPE_CHECKING, Any

from src.schemas.request import ResumeAnalysisRequest

if TYPE_CHECKING:
    from src.schemas.response import CoreValueScore, NCSCompetencyScore, PositionSkillMatch


class PromptBuilder:
    """Builder for LLM prompts."""

    @staticmethod
    def build_system_prompt(
        org_data: dict[str, Any],
        position: str = "",
        interview_data: dict[str, Any] | None = None,
    ) -> str:
        """Build system prompt with organization context.

        Args:
            org_data: Organization data dictionary
            position: Target position for position-specific keywords
            interview_data: Interview questions data (optional)

        Returns:
            System prompt string
        """
        # 기본 키워드
        keywords = ", ".join(org_data.get("keywords", []))
        core_values = ", ".join(org_data.get("core_values", []))

        # 직렬별 키워드 (있으면 추가)
        position_keywords = ""
        keywords_by_position = org_data.get("keywords_by_position", {})
        if position and keywords_by_position:
            # 정확히 일치하는 직렬 찾기
            matched_keywords = keywords_by_position.get(position, [])
            # 부분 일치도 시도 (예: "경영기획" in "경영기획직")
            if not matched_keywords:
                for pos_name, pos_keywords in keywords_by_position.items():
                    if position in pos_name or pos_name in position:
                        matched_keywords = pos_keywords
                        break
            if matched_keywords:
                position_keywords = ", ".join(matched_keywords)

        # 최근 동향
        recent_initiatives = org_data.get("recent_initiatives", [])
        initiatives_text = "\n".join(f"  - {item}" for item in recent_initiatives[:5])

        # 면접 정보 구성
        interview_section = PromptBuilder._build_interview_section(interview_data)

        # NCS 역량 정보 구성
        ncs_section = PromptBuilder._build_ncs_section(interview_data)

        # 채용 트렌드 정보 구성
        recruitment_section = PromptBuilder._build_recruitment_section(org_data)

        return f"""당신은 공기업 자기소개서 분석 전문가입니다.
{org_data.get("name", "기관")}에 지원하는 자기소개서를 분석하여 상세한 피드백을 제공합니다.

## 기관 정보
- 기관명: {org_data.get("name", "")}
- 분야: {org_data.get("category", "")}
- 슬로건: {org_data.get("slogan", "")}

## 기관 정체성
- 미션: {org_data.get("mission", "")}
- 비전: {org_data.get("vision", "")}
- 인재상: {org_data.get("talent_image", "")}
- 핵심 가치: {core_values}

## 핵심 키워드
- 기관 공통: {keywords}
{f"- 직렬별({position}): {position_keywords}" if position_keywords else ""}

## 최근 주요 동향
{initiatives_text if initiatives_text else "- 정보 없음"}
{recruitment_section}{interview_section}{ncs_section}
## 분석 기준
1. 구체성: 추상적 표현 대신 구체적 경험과 사례 포함 여부
2. 직무 연관성: 지원 직무와의 연관성
3. 기관 이해도: 기관의 미션, 비전, 인재상 반영 여부
4. 핵심가치 반영: 기관의 핵심 가치가 자소서에 녹아있는지
5. 논리 구조: 서론-본론-결론의 논리적 구성
6. 차별성: 다른 지원자와 차별화되는 내용
7. 최신 트렌드: 기관의 최근 동향/사업에 대한 이해도
8. 채용 트렌드 부합: 기관의 최근 채용 동향, 신규 사업 분야와의 부합 여부

## 응답 형식
반드시 다음 JSON 형식으로 응답하세요:
{{
  "overall_score": <0-100 정수>,
  "length_check": {{
    "current": <현재 글자 수>,
    "max": <최대 글자 수>,
    "percentage": <사용률 퍼센트>,
    "status": "<short|optimal|over>"
  }},
  "feedbacks": [
    {{
      "category": "<카테고리명>",
      "score": <1-10 정수>,
      "comment": "<피드백 내용>",
      "suggestion": "<개선 제안 또는 null>"
    }}
  ],
  "keyword_analysis": {{
    "found_keywords": ["<발견된 키워드 목록>"],
    "missing_keywords": ["<누락된 키워드 목록>"],
    "match_rate": <매칭률 퍼센트>
  }},
  "ncs_analysis": {{
    "evaluated_competencies": [
      {{
        "competency": "<NCS 역량명>",
        "score": <1-10 정수>,
        "evidence": "<자소서에서 발견된 근거>",
        "suggestion": "<개선 제안 또는 null>"
      }}
    ],
    "strongest": "<가장 강점인 역량>",
    "weakest": "<보완이 필요한 역량>",
    "overall_comment": "<NCS 역량 종합 평가>"
  }},
  "talent_analysis": {{
    "match_score": <1-10 정수>,
    "matched_traits": ["<인재상에서 잘 드러난 특성 목록>"],
    "missing_traits": ["<인재상에서 부족한 특성 목록>"],
    "overall_comment": "<인재상 부합도 종합 평가>",
    "improvement_tips": ["<인재상에 맞추기 위한 구체적 개선 팁>"]
  }},
  "expected_questions": ["<자소서 내용과 연관된 실제 기출 면접 질문 5개>"]
}}

## NCS 역량 평가 지침
- 위 "평가할 NCS 역량" 목록에서 자소서에 드러난 역량을 평가하세요
- 각 역량별로 자소서에서 발견된 구체적 근거(경험, 사례)를 명시하세요
- 근거가 부족한 역량은 낮은 점수와 함께 개선 제안을 제공하세요
- 해당 기관에서 자주 평가하는 역량(빈도 높음)에 주목하세요

## 인재상 분석 지침
- 위 "인재상" 정보를 분석하여 핵심 특성(전문성, 역량, 가치관 등)을 추출하세요
- 자소서에서 해당 특성이 드러나는 부분을 찾아 matched_traits로 기록하세요
- 인재상에서 요구하지만 자소서에 부족한 특성은 missing_traits로 기록하세요
- improvement_tips에는 구체적이고 실행 가능한 개선 방안을 제시하세요
- 인재상과의 부합도를 종합적으로 평가하여 match_score를 산정하세요

## 예상 면접 질문 작성 지침
- 위 "실제 기출 면접 질문" 목록에서 자소서 내용과 연관된 질문을 우선 선택하세요
- 자소서에서 언급된 경험, 역량, 지원동기와 관련된 질문을 선택하세요
- 꼬리질문(follow_up)이 있는 경우 함께 고려하세요
- 기출 질문이 없는 경우에만 새로운 질문을 생성하세요"""

    @staticmethod
    def build_system_prompt_v2(
        org_data: dict[str, Any],
        position: str = "",
        interview_data: dict[str, Any] | None = None,
        core_value_scores: "list[CoreValueScore] | None" = None,
        ncs_competency_scores: "list[NCSCompetencyScore] | None" = None,
        position_skill_match: "PositionSkillMatch | None" = None,
    ) -> str:
        """Build system prompt with organization context (V2 - Redesigned).

        Args:
            org_data: Organization data dictionary
            position: Target position for position-specific keywords
            interview_data: Interview questions data (optional)
            core_value_scores: Pre-computed core value analysis
            ncs_competency_scores: Pre-computed NCS competency analysis
            position_skill_match: Pre-computed position skill match analysis

        Returns:
            System prompt string for new analysis format
        """
        # 기본 정보
        keywords = ", ".join(org_data.get("keywords", []))
        core_values_list = org_data.get("core_values", [])
        core_values = ", ".join(core_values_list)

        # 직렬별 키워드
        position_keywords = ""
        keywords_by_position = org_data.get("keywords_by_position", {})
        if position and keywords_by_position:
            matched_keywords = keywords_by_position.get(position, [])
            if not matched_keywords:
                for pos_name, pos_keywords in keywords_by_position.items():
                    if position in pos_name or pos_name in position:
                        matched_keywords = pos_keywords
                        break
            if matched_keywords:
                position_keywords = ", ".join(matched_keywords)

        # 최근 동향
        recent_news = []
        for news in org_data.get("recruitment_news", [])[:2]:
            recent_news.append(news.get("title", ""))
        for news in org_data.get("business_news", [])[:2]:
            recent_news.append(news.get("title", ""))
        for item in org_data.get("recent_initiatives", [])[:2]:
            recent_news.append(item)
        recent_news_text = "\n".join(f"  - {item}" for item in recent_news[:5] if item)

        # 면접 키워드 추출
        interview_keywords = PromptBuilder._extract_interview_keywords(interview_data)

        # 면접 질문 섹션 (연도 포함)
        interview_section = PromptBuilder._build_interview_section_v2(interview_data)

        # 핵심가치별 활용 예시 생성
        core_value_examples = PromptBuilder._build_core_value_examples(core_values_list)

        # 사전 분석 결과 섹션 (기관별 맞춤형 모범답안 생성용)
        analysis_context = PromptBuilder._build_analysis_context(
            core_value_scores, ncs_competency_scores, position_skill_match
        )

        # 평가 기준 정보
        evaluation_criteria = org_data.get("evaluation_criteria", [])
        eval_text = ""
        if evaluation_criteria:
            eval_text = "\n## 평가 기준 (가중치)\n"
            for crit in evaluation_criteria:
                eval_text += f"- {crit.get('name', '')}: {crit.get('weight', 0)}% - {crit.get('description', '')}\n"

        return f"""당신은 10년 이상 경력의 공기업 자기소개서 컨설턴트입니다.
실제 면접관 경험을 바탕으로 합격하는 자기소개서의 특징을 잘 알고 있습니다.

## 기관 정보
- 기관명: {org_data.get("name", "")}
- 분야: {org_data.get("category", "")}
- 슬로건: {org_data.get("slogan", "")}
- 미션: {org_data.get("mission", "")}
- 비전: {org_data.get("vision", "")}
- 인재상: {org_data.get("talent_image", "")}
- 핵심 가치: {core_values}
{eval_text}
## 핵심 키워드
- 기관 공통: {keywords}
{f"- 직렬별({position}): {position_keywords}" if position_keywords else ""}

## 최근 동향 (2025-2026)
{recent_news_text if recent_news_text else "- 정보 없음"}

## 면접 준비 키워드
{", ".join(interview_keywords) if interview_keywords else "- 정보 없음"}
{interview_section}
{core_value_examples}
{analysis_context}
## 분석 지침

### 1. 종합 평가
- overall_score: 0-100점 (평가 기준 가중치 반영)
- overall_grade: 우수(80+), 양호(60-79), 보통(40-59), 미흡(40 미만)
- overall_summary: 핵심 강점과 개선점을 포함한 1-2문장 요약

### 2. 잘한 점 (strengths) - 상위 3개
- 자소서에서 실제로 잘 작성된 부분을 인용(quote)
- 왜 좋은지 구체적으로 평가(evaluation)

### 3. 개선점 (improvements) - 상위 3개
- 문제점(problem): 무엇이 부족한지 명확히
- 현재 텍스트(current_text): 자소서에서 해당 부분 인용
- 수정 예시(improved_text): 구체적으로 어떻게 바꾸면 좋은지 50자 이상 예시 제공

### 4. 예상 면접 질문 (interview_questions) - 3-5개
🚨 중요: 기출 질문 + 예상 질문을 반드시 섞어서 제공
- 기출 질문(is_frequent: true): 위 "실제 기출 면접 질문" 목록에서 자소서와 관련된 것 2-3개
- 예상 질문(is_frequent: false): 자소서 내용 기반으로 면접관이 물어볼 만한 새로운 질문 1-2개 필수

🚨 answer_tips 작성 지침 (매우 중요):
- 단순한 "~와 연결하여 설명" 같은 추상적 조언 금지
- 자소서에서 언급한 구체적 내용을 인용하여 작성
- 실제 답변 시작 문장을 예시로 제공

❌ 나쁜 예시:
  - "자소서에서 언급한 경험과 연결하여 설명하세요"
  - "구체적인 사례를 들어 답변하세요"
  - "[서두 부분]의 경험을 활용하세요"

✅ 좋은 예시:
  - "'3개월간 Python으로 수급예측 모델을 개발한 경험'을 구체적으로 설명하고, 정확도 15% 향상이라는 수치의 산출 근거를 준비하세요"
  - "답변 예시: '팀원 5명과 함께 진행한 프로젝트에서 저는 데이터 전처리를 담당했으며, 특히 결측치 처리 방식에 대해 팀원들과 의견 조율을 했습니다...'"
  - "'K-FOOD 수출 확대'에 대해 언급했으므로, 구체적인 수출 전략 아이디어(예: 동남아 할랄 인증, 일본 프리미엄 마케팅 등)를 1-2개 준비하세요"

### 5. 모범 답안 (model_answer) ⭐⭐⭐ 최우선 과제 ⭐⭐⭐

🎯🎯🎯 품질 목표 (가장 중요 - 반드시 달성):
이 모범 답안을 다시 분석했을 때 **80점 이상**이 나와야 합니다.
아래 요구사항을 모두 충족해야만 80점 이상 달성 가능합니다.

🚨🚨🚨 분량 요구사항 (절대 준수):
- 최소 1000자 이상, 최대 2500자 이내 작성
- 권장 분량: 1800~2200자
- 각 문단을 350-450자로 충분히 서술
- 글자 수가 부족하면 경험을 더 구체적으로 풀어서 작성

🚨🚨🚨 필수 반영 요소 - 점수 직결 (모두 반영해야 80점 이상):

1️⃣ 키워드 매칭 (keyword_analysis 활용) - 점수에 큰 영향:
- 위 분석의 missing_keywords에 있는 키워드들을 모범 답안에 자연스럽게 포함할 것
- 목표: 키워드 매칭률 60% 이상 달성
- 예: missing_keywords가 ["전력", "탄소중립", "안전"]이면 이 단어들을 답안에 녹여내기

2️⃣ NCS 역량 (ncs_competency_scores 활용):
- 위 "NCS 역량 분석" 중 최소 3가지 이상의 역량을 구체적 경험으로 녹여낼 것
- 특히 "필수" 표시되고 점수가 낮은 역량은 반드시 포함
- ❌로 표시된 역량을 ✅로 바꿀 수 있도록 구체적 근거 제시

3️⃣ 핵심가치 (core_value_scores 활용):
- 위 "핵심가치 반영 분석" 중 최소 2가지 이상을 자연스럽게 언급할 것
- ❌로 표시된 핵심가치를 우선적으로 보완
- 단순 언급이 아닌, 경험/사례와 연결하여 설득력 있게 표현

4️⃣ 개선점 반영 (improvements 활용):
- 위 분석의 improvements에서 제시된 문제점들을 모범 답안에서는 해결할 것
- improved_text의 방향성을 참고하여 더 발전된 내용 작성

⭐⭐⭐ 자연스러운 서술 최우선 원칙 ⭐⭐⭐

🚫 절대 금지 - 나열식 작성:
아래와 같이 평가 기준을 단순 나열하는 방식은 절대 금지:
❌ "저는 의사소통능력이 뛰어납니다. 또한 문제해결능력도 갖추고 있습니다. 그리고 대인관계능력도..."
❌ "첫째, ~입니다. 둘째, ~입니다. 셋째, ~입니다."
❌ "~역량을 갖추었고, ~역량도 보유하고 있으며, ~능력도 있습니다."

✅ 필수 - 스토리텔링 방식:
하나의 경험 안에서 여러 역량이 자연스럽게 드러나도록 서술:
✅ "프로젝트 초반, 팀원들 간 의견 충돌로 진행이 더뎌졌습니다. 저는 각자의 의견을 경청한 뒤,
   공통 목표를 재확인하는 회의를 제안했습니다. 서로의 강점을 살린 역할 분담을 통해
   결국 기한 내 프로젝트를 완수할 수 있었고, 이 과정에서 소통과 협업의 중요성을 깊이
   깨달았습니다."
   → 이 한 문단에서 의사소통, 대인관계, 문제해결 역량이 모두 자연스럽게 드러남

🚨 자연스러운 글쓰기 원칙:
1. 경험을 시간 순서로 서술 (시작 → 과정 → 결과 → 깨달음)
2. 감정과 생각의 변화 포함 ("처음에는 막막했지만", "그때 깨달은 것은")
3. 구체적인 상황 묘사 ("20명 규모의 팀에서", "3개월간의 프로젝트")
4. 하나의 경험을 깊이 있게 풀어쓰기 (여러 경험 간략히 나열 X)
5. 문장과 문장 사이에 논리적 연결 ("이를 통해", "이러한 경험은", "그 결과")

🚨 반영해야 할 요소들 (자연스럽게 녹여내기 - 80점 달성 필수):
- missing_keywords의 키워드들: 답안 전체에 자연스럽게 분산 배치
- NCS 역량 3가지 이상: 경험 서술 속에서 자연스럽게 드러나도록 (점수가 낮은 역량 우선)
- 핵심가치 2가지 이상: 가치관이나 교훈으로 연결 (부족 표시된 것 우선)
- 기관 특성: 지원동기나 포부에서 연결 (미션/비전/최신 사업 언급)
- 구체적 수치/성과: "20% 개선", "3개월간", "10명 규모" 등
→ 이 요소들을 "나열"하지 말고 "이야기 속에 녹여내기"
→ 모든 요소가 포함되어야 80점 이상 달성 가능

🚨 문단 구성 (총 5개 문단, 각 350-450자):
⚠️ 중요: 각 문단 사이에 반드시 빈 줄을 넣어서 문단을 구분하세요!
예시: "첫 번째 문단 내용...[여기서 줄바꿈 2번]두 번째 문단 내용..."

[1문단 - 도입 / 350자 이상]
- 인상적인 경험이나 계기로 시작
- 독자의 관심을 끄는 첫 문장
- 원문의 좋은 표현 유지하면서 확장
- 💡 이 문단에서 핵심가치 1개를 자연스럽게 녹여낼 것

[2문단 - 핵심 경험 상세 서술 / 450자 이상]
- 가장 중요한 경험 하나를 깊이 있게 서술
- 상황(Situation) → 과제(Task) → 행동(Action) → 결과(Result) 구조
- 구체적 수치와 맥락 포함 (3개월, 20명, 15% 개선 등)
- 💡 이 문단에서 NCS 역량 1개 이상을 구체적 경험으로 보여줄 것

[3문단 - 추가 경험 및 역량 / 350자 이상]
- 2문단과 다른 측면의 경험
- 💡 이 문단에서 NCS 역량 1개 이상을 추가로 보여줄 것

[4문단 - 기관 연결 / 350자 이상]
- 왜 이 기관인지 구체적 이유
- 기관의 미션/비전/최신 사업과 본인 경험의 연결점

[5문단 - 입사 후 포부 / 350자 이상]
- 구체적인 기여 계획
- 추상적 다짐이 아닌 실행 가능한 목표

🚨 맞춤법 및 띄어쓰기:
- "~할 수 있다" (O) / "~할수있다" (X)
- "~에 대해" (O) / "~에대해" (X)
- "되" vs "돼" 구분, "~로서" vs "~로써" 구분

🚨 문체 원칙 (인간이 쓴 것처럼):
- 종결어미 다양화: "~습니다", "~였습니다", "~게 되었습니다", "~던 기억이 있습니다"
- 감정/생각 표현: "솔직히 처음에는", "그때 비로소 깨달았습니다", "뿌듯함을 느꼈습니다"
- 시간적 맥락: "당시", "그 무렵", "대학 3학년 때", "인턴 기간 중"
- 자연스러운 연결어: "이를 계기로", "이러한 경험은", "돌이켜보면"

🚨 절대 금지:
- "저는 ~한 인재입니다" (자기 규정)
- "귀사", "귀 기관" (기관명 직접 사용)
- 1000자 미만의 짧은 답변
- 역량/가치를 나열하는 방식
- 가족 관계 언급 금지 (블라인드 채용 위반):
  ❌ "아버지의 영향으로", "어머니의 가르침" 등
- 같은 표현 반복 금지:
  ❌ "~을 통해 ~을 통해" (한 문장에 동일 표현 2번 이상 사용 금지)
  ❌ "~하며 ~하며", "~하고 ~하고" 등 반복 구조
  ✅ 다양한 연결 표현 사용: "~함으로써", "~한 결과", "~덕분에", "이로 인해"

🚨 외국어 사용 원칙:
- 전문용어, 고유명사 등 필요한 경우 영어/외국어 사용 가능
  ✅ "Python을 활용한 데이터 분석", "AI 기반 서비스", "ERP 시스템"
- 단, 문법에 맞고 맥락이 자연스러워야 함
  ❌ "일 ethic" → ✅ "직업윤리" 또는 "work ethic을 갖추어"
  ❌ "강한 responsibility" → ✅ "강한 책임감" 또는 "responsibility를 다하여"
- 한글과 영어를 섞을 때 문장 구조가 어색하지 않도록 주의
  ❌ "저의 main 역할은" → ✅ "저의 주요 역할은" 또는 "저의 main role은"

## ⚠️⚠️⚠️ CRITICAL: model_answer 길이 요구사항 ⚠️⚠️⚠️
model_answer 필드는 반드시 **1200자 이상**이어야 합니다.
- 1000자 미만: ❌ 절대 불가 (실패로 간주)
- 1000-1199자: ⚠️ 부족 (재작성 필요)
- 1200-2500자: ✅ 합격

## 응답 형식 (반드시 JSON)
{{
  "overall_score": <0-100 정수>,
  "overall_grade": "<우수|양호|보통|미흡>",
  "overall_summary": "<1-2문장 종합 평가>",
  "strengths": [
    {{
      "title": "<평가 항목명>",
      "score": <1-10 정수>,
      "quote": "<자소서에서 해당 부분 인용>",
      "evaluation": "<왜 잘했는지 평가>"
    }}
  ],
  "improvements": [
    {{
      "title": "<평가 항목명>",
      "score": <1-10 정수>,
      "problem": "<문제점>",
      "current_text": "<현재 작성 내용 또는 '해당 내용 없음'>",
      "improved_text": "<구체적 수정 예시 50자 이상>"
    }}
  ],
  "keyword_analysis": {{
    "found_keywords": ["<발견된 키워드>"],
    "missing_keywords": ["<누락된 키워드>"],
    "match_rate": <매칭률 퍼센트>
  }},
  "interview_questions": [
    {{
      "question": "<면접 질문>",
      "is_frequent": <true|false>,
      "years": [<출제연도 배열, 예: [2024, 2023, 2021]>],
      "answer_tips": "<답변 포인트>"
    }}
  ],
  "model_answer_checklist": {{
    "missing_keywords_to_include": ["<keyword_analysis.missing_keywords에서 3-5개 선택>"],
    "weak_core_values_to_include": ["<점수가 낮은 핵심가치 2개>"],
    "weak_ncs_to_include": ["<점수가 낮은 NCS 역량 2개>"],
    "improvements_to_apply": ["<improvements에서 지적된 문제점 해결 방향 2-3개>"]
  }},
  "model_answer": "<위 문단 구성 지침 준수하여 1200자 이상 작성. checklist 전부 반영. 반드시 문단 사이에 빈 줄(\\n\\n)로 구분>",
  "model_answer_length": <1200 이상>
}}"""

    @staticmethod
    def _build_analysis_context(
        core_value_scores: "list[CoreValueScore] | None",
        ncs_competency_scores: "list[NCSCompetencyScore] | None",
        position_skill_match: "PositionSkillMatch | None",
    ) -> str:
        """Build pre-computed analysis context for model answer generation.

        Args:
            core_value_scores: Pre-computed core value analysis
            ncs_competency_scores: Pre-computed NCS competency analysis
            position_skill_match: Pre-computed position skill match analysis

        Returns:
            Formatted analysis context for prompt
        """
        sections = []

        # 핵심가치 반영 분석 결과
        if core_value_scores:
            cv_text = "\n## 🎯 핵심가치 반영 분석 (모범답안 작성 시 참고)\n"
            missing_values = []
            found_values = []
            for cv in core_value_scores:
                status = "✅" if cv.found else "❌"
                cv_text += f"- {status} {cv.value}: {cv.score}/10점"
                if cv.evidence:
                    cv_text += f" (근거: \"{cv.evidence[:30]}...\")"
                if cv.suggestion:
                    cv_text += f"\n  └ 💡 {cv.suggestion}"
                    missing_values.append(cv.value)
                else:
                    found_values.append(cv.value)
                cv_text += "\n"

            if missing_values:
                cv_text += f"\n⚠️ 모범답안에서 반드시 보완할 핵심가치: {', '.join(missing_values)}\n"
            sections.append(cv_text)

        # NCS 역량 분석 결과
        if ncs_competency_scores:
            ncs_text = "\n## 📊 NCS 역량 분석 (모범답안 작성 시 참고)\n"
            missing_ncs = []
            for ncs in ncs_competency_scores:
                status = "✅" if ncs.found else "❌"
                importance_mark = "⭐" if ncs.importance == "필수" else ""
                ncs_text += f"- {status} {ncs.name} ({ncs.importance}{importance_mark}): {ncs.score}/10점"
                if ncs.evidence:
                    ncs_text += f"\n  └ 근거: \"{ncs.evidence[:40]}...\""
                if ncs.suggestion:
                    ncs_text += f"\n  └ 💡 {ncs.suggestion}"
                    missing_ncs.append(ncs.name)
                ncs_text += "\n"

            if missing_ncs:
                ncs_text += f"\n⚠️ 모범답안에서 반드시 보완할 NCS 역량: {', '.join(missing_ncs)}\n"
            sections.append(ncs_text)

        # 직무 우대사항 매칭 결과
        if position_skill_match:
            psm = position_skill_match
            psm_text = "\n## 💼 직무 우대사항 매칭 (모범답안 작성 시 참고)\n"
            psm_text += f"전체 매칭률: {psm.overall_match_rate}%\n"

            if psm.matched_majors:
                psm_text += f"- ✅ 관련 전공 언급됨: {', '.join(psm.matched_majors)}\n"
            if psm.missing_majors:
                psm_text += f"- ❌ 언급되지 않은 관련 전공: {', '.join(psm.missing_majors)}\n"

            if psm.matched_certifications:
                psm_text += f"- ✅ 관련 자격증 언급됨: {', '.join(psm.matched_certifications)}\n"
            if psm.missing_certifications:
                psm_text += f"- ❌ 언급되지 않은 우대 자격증: {', '.join(psm.missing_certifications[:5])}\n"

            if psm.matched_skills:
                psm_text += f"- ✅ 관련 스킬 언급됨: {', '.join(psm.matched_skills)}\n"
            if psm.missing_skills:
                psm_text += f"- ❌ 언급되지 않은 우대 스킬: {', '.join(psm.missing_skills[:5])}\n"

            if psm.recommendation:
                psm_text += f"\n💡 추천: {psm.recommendation}\n"

            sections.append(psm_text)

        return "\n".join(sections) if sections else ""

    @staticmethod
    def _build_core_value_examples(core_values: list[str]) -> str:
        """Build core value usage examples for prompt.

        Args:
            core_values: List of core values

        Returns:
            Formatted core value examples
        """
        if not core_values:
            return ""

        value_examples = {
            "고객중심": "고객의 불편함을 먼저 해소하기 위해 ~한 시도를 했습니다",
            "상생": "함께 성장하는 것이 진정한 성공이라는 믿음으로 ~",
            "혁신": "기존 방식에 안주하지 않고 ~라는 새로운 시도를 했습니다",
            "전문성": "해당 분야에서 깊이 있는 지식을 쌓기 위해 ~",
            "청렴": "원칙을 지키는 것이 신뢰의 시작이라 생각하여 ~",
            "도전": "실패를 두려워하지 않고 ~에 도전했습니다",
            "소통": "다양한 의견을 경청하고 ~를 통해 합의점을 찾았습니다",
            "책임": "맡은 바 책임을 다하기 위해 ~까지 완수했습니다",
            "신뢰": "약속을 지키는 것이 관계의 기본이라 생각하여 ~",
            "열정": "밤늦게까지 ~에 매달리며 열정을 쏟았습니다",
        }

        text = "\n## 핵심가치 활용 예시\n"
        text += "모범 답안에서 아래 핵심가치를 자연스럽게 녹여내세요:\n"
        for value in core_values[:5]:
            example = value_examples.get(value, f"'{value}'의 가치를 실천하기 위해 ~")
            text += f"- {value}: \"{example}\"\n"
        return text

    @staticmethod
    def _build_interview_section_v2(interview_data: dict[str, Any] | None) -> str:
        """Build interview section with year information (V2).

        Args:
            interview_data: Interview data dictionary

        Returns:
            Formatted interview section with years
        """
        if not interview_data:
            return ""

        sections = []

        # 면접 형식 정보
        interview_format = interview_data.get("interview_format", {})
        if interview_format:
            format_text = f"""
## 면접 정보
- 면접 유형: {interview_format.get("type", "정보 없음")}
- 면접 단계: {" → ".join(interview_format.get("stages", []))}
- 난이도: {interview_format.get("difficulty", "정보 없음")}
- 합격률: {interview_format.get("positive_rate", "정보 없음")}"""
            sections.append(format_text)

        # 실제 기출 면접 질문 (연도 포함)
        questions = interview_data.get("questions", [])
        if questions:
            high_freq = [q for q in questions if q.get("frequency") == "high"]
            medium_freq = [q for q in questions if q.get("frequency") == "medium"]
            other = [q for q in questions if q.get("frequency") not in ("high", "medium")]

            sorted_questions = high_freq + medium_freq + other
            selected_questions = sorted_questions[:15]

            questions_text = "\n## 실제 기출 면접 질문\n"
            for q in selected_questions:
                year = q.get("year", "")
                freq_mark = f"({year}년 기출 ⭐)" if q.get("frequency") == "high" and year else ""
                if not freq_mark and year:
                    freq_mark = f"({year}년)"
                questions_text += f"- [{q.get('category', '기타')}] {q.get('question', '')} {freq_mark}\n"

            sections.append(questions_text)

        return "\n".join(sections)

    @staticmethod
    def _extract_interview_keywords(interview_data: dict[str, Any] | None) -> list[str]:
        """Extract important interview keywords from interview data.

        Args:
            interview_data: Interview data dictionary

        Returns:
            List of important keywords
        """
        if not interview_data:
            return []

        keywords = set()

        # 질문에서 자주 나오는 키워드 추출
        questions = interview_data.get("questions", [])
        for q in questions:
            # 빈출 질문의 키워드
            if q.get("frequency") in ("high", "medium"):
                category = q.get("category", "")
                if category:
                    keywords.add(category)

        # NCS 역량 키워드
        for q in questions:
            for ncs in q.get("ncs_competencies", [])[:3]:
                keywords.add(ncs)

        return list(keywords)[:8]

    @staticmethod
    def _build_interview_section(interview_data: dict[str, Any] | None) -> str:
        """Build interview information section for prompt.

        Args:
            interview_data: Interview data dictionary

        Returns:
            Formatted interview section string
        """
        if not interview_data:
            return ""

        sections = []

        # 면접 형식 정보
        interview_format = interview_data.get("interview_format", {})
        if interview_format:
            format_text = f"""
## 면접 정보
- 면접 유형: {interview_format.get("type", "정보 없음")}
- 면접 단계: {" → ".join(interview_format.get("stages", []))}
- 난이도: {interview_format.get("difficulty", "정보 없음")}
- 평가 비중: {interview_format.get("scoring", "정보 없음")}"""
            sections.append(format_text)

        # 실제 기출 면접 질문 (빈출 우선)
        questions = interview_data.get("questions", [])
        if questions:
            # 빈출(high frequency) 질문 우선, 그 다음 medium
            high_freq = [q for q in questions if q.get("frequency") == "high"]
            medium_freq = [q for q in questions if q.get("frequency") == "medium"]
            other = [q for q in questions if q.get("frequency") not in ("high", "medium")]

            # 우선순위로 정렬하여 최대 15개 선택
            sorted_questions = high_freq + medium_freq + other
            selected_questions = sorted_questions[:15]

            questions_text = "\n## 실제 기출 면접 질문\n"
            for q in selected_questions:
                freq_mark = "⭐" if q.get("frequency") == "high" else ""
                questions_text += f"- [{q.get('category', '기타')}] {q.get('question', '')} {freq_mark}\n"

                # 꼬리질문이 있으면 추가
                follow_ups = q.get("follow_up", [])
                for fu in follow_ups[:2]:  # 최대 2개
                    questions_text += f"  └ 꼬리질문: {fu}\n"

            sections.append(questions_text)

        return "\n".join(sections)

    @staticmethod
    def _build_ncs_section(interview_data: dict[str, Any] | None) -> str:
        """Build NCS competency section for prompt.

        Args:
            interview_data: Interview data dictionary

        Returns:
            Formatted NCS section string
        """
        if not interview_data:
            return ""

        questions = interview_data.get("questions", [])
        if not questions:
            return ""

        # NCS 역량 빈도 집계
        ncs_counts: dict[str, int] = {}
        for q in questions:
            for ncs in q.get("ncs_competencies", []):
                ncs_counts[ncs] = ncs_counts.get(ncs, 0) + 1

        if not ncs_counts:
            return ""

        # 빈도 순으로 정렬
        sorted_ncs = sorted(ncs_counts.items(), key=lambda x: x[1], reverse=True)

        # NCS 역량 설명 (공통)
        ncs_descriptions = {
            "의사소통능력": "문서 작성, 경청, 의사 표현, 비언어적 소통 능력",
            "대인관계능력": "팀워크, 리더십, 갈등 관리, 협상, 고객 서비스 능력",
            "문제해결능력": "문제 인식, 대안 도출, 의사 결정, 창의적 해결 능력",
            "자기개발능력": "자아 인식, 자기 관리, 경력 개발, 학습 능력",
            "조직이해능력": "조직 체계, 경영 이해, 업무 이해, 국제 감각",
            "자원관리능력": "시간 관리, 예산 관리, 물적/인적 자원 관리 능력",
            "기술능력": "기술 이해, 기술 선택, 기술 적용 능력",
            "정보능력": "정보 수집, 정보 분석, 정보 관리, 컴퓨터 활용 능력",
            "직업윤리": "직업 윤리 의식, 공동체 윤리, 근로 윤리",
        }

        ncs_text = "\n## 평가할 NCS 역량 (빈도순)\n"
        for ncs, count in sorted_ncs[:7]:  # 상위 7개
            desc = ncs_descriptions.get(ncs, "")
            freq_label = "⭐⭐" if count >= 15 else "⭐" if count >= 8 else ""
            ncs_text += f"- {ncs} ({count}회 출제) {freq_label}\n"
            if desc:
                ncs_text += f"  └ 평가 요소: {desc}\n"

        return ncs_text

    @staticmethod
    def _build_recruitment_section(org_data: dict[str, Any]) -> str:
        """Build recruitment trend section for prompt.

        Args:
            org_data: Organization data dictionary

        Returns:
            Formatted recruitment section string
        """
        sections = []

        # 채용 뉴스
        recruitment_news = org_data.get("recruitment_news", [])
        if recruitment_news:
            news_text = "\n## 최근 채용 동향\n"
            for news in recruitment_news[:3]:  # 최대 3개
                title = news.get("title", "")
                date = news.get("date", "")
                summary = news.get("summary", "")
                news_text += f"- [{date}] {title}\n"
                if summary:
                    news_text += f"  └ {summary}\n"
            sections.append(news_text)

        # 사업 뉴스 (채용과 관련된 신규 사업 동향)
        business_news = org_data.get("business_news", [])
        if business_news:
            biz_text = "\n## 신규 사업 동향\n"
            for news in business_news[:3]:  # 최대 3개
                title = news.get("title", "")
                summary = news.get("summary", "")
                biz_text += f"- {title}\n"
                if summary:
                    biz_text += f"  └ {summary}\n"
            sections.append(biz_text)

        if sections:
            return "\n".join(sections) + "\n"
        return ""

    @staticmethod
    def build_user_prompt(request: ResumeAnalysisRequest) -> str:
        """Build user prompt from request.

        Args:
            request: Resume analysis request

        Returns:
            User prompt string
        """
        return f"""## 지원 정보
- 지원 직렬: {request.position}
- 문항: {request.question}
- 최대 글자 수: {request.maxLength}자

## 자기소개서 내용
{request.answer}

위 자기소개서를 분석하여 JSON 형식으로 상세한 피드백을 제공해주세요."""
