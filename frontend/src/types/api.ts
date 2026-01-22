/** API Types for Resume Analysis */

export interface ResumeAnalysisRequest {
  organization: string;
  position: string;
  question?: string;
  answer: string;
  maxLength: number;
}

export interface LengthCheck {
  current: number;
  max: number;
  percentage: number;
  status: 'short' | 'optimal' | 'over';
}

export interface FeedbackItem {
  category: string;
  score: number;
  comment: string;
  suggestion?: string;
}

export interface KeywordAnalysis {
  found_keywords: string[];
  missing_keywords: string[];
  match_rate: number;
}

export interface NCSItem {
  competency: string;
  score: number;
  evidence: string;
  suggestion?: string;
}

export interface NCSAnalysis {
  evaluated_competencies: NCSItem[];
  strongest: string;
  weakest: string;
  overall_comment: string;
}

export interface TalentAnalysis {
  match_score: number;
  matched_traits: string[];
  missing_traits: string[];
  overall_comment: string;
  improvement_tips: string[];
}

export interface ResumeAnalysisResponse {
  overall_score: number;
  length_check: LengthCheck;
  feedbacks: FeedbackItem[];
  keyword_analysis: KeywordAnalysis;
  ncs_analysis?: NCSAnalysis;
  talent_analysis?: TalentAnalysis;
  expected_questions: string[];
}

// === 새로운 응답 타입 (리디자인 버전) ===

export interface RecentNewsItem {
  title: string;
  date?: string;
  category?: string;
  url?: string;
}

export interface PastQuestion {
  year: number;
  half?: string;
  question: string;
  char_limit?: number;
  is_prediction?: boolean;
}

export interface WarningItem {
  type: string;
  severity: string;
  message: string;
  detected_text?: string;
  suggestion?: string;
}

export interface FrequentInterviewQuestion {
  question: string;
  category: string;
  frequency: string;
  tips?: string;
}

export interface InterviewDetailInfo {
  format_type?: string;
  stages?: string[];
  duration?: string;
  difficulty?: string;
  pass_rate?: string;
  frequent_questions?: FrequentInterviewQuestion[];
}

export interface OrganizationInfo {
  name: string;
  website?: string;
  core_values: string[];
  talent_image: string;
  recent_news: RecentNewsItem[];
  interview_keywords: string[];
  recruitment_process?: string[];
  interview_difficulty?: string;
  interview_pass_rate?: string;
  data_updated_at?: string;
}

export interface StrengthItem {
  title: string;
  score: number;
  quote: string;
  evaluation: string;
}

export interface ImprovementItem {
  title: string;
  score: number;
  problem: string;
  current_text: string;
  improved_text: string;
}

export interface InterviewQuestion {
  question: string;
  is_frequent: boolean;
  years?: number[];
  answer_tips: string;
  sample_answer?: string;
}

export interface CoreValueScore {
  value: string;
  score: number;
  found: boolean;
  evidence?: string;
  suggestion?: string;
}

export interface NCSCompetencyScore {
  code: string;
  name: string;
  importance: string;
  score: number;
  found: boolean;
  evidence?: string;
  suggestion?: string;
}

export interface SimilarQuestion {
  year: number;
  half?: string;
  question: string;
  similarity: number;
  char_limit?: number;
  matched_keywords: string[];
}

export interface PositionSkillMatch {
  matched_majors: string[];
  missing_majors: string[];
  matched_certifications: string[];
  missing_certifications: string[];
  matched_skills: string[];
  missing_skills: string[];
  overall_match_rate: number;
  recommendation: string;
}

export interface NewResumeAnalysisResponse {
  // 종합 평가
  overall_score: number;
  overall_grade: string;
  overall_summary: string;

  // 글자 수 체크
  length_check: LengthCheck;

  // 경고 사항 (공통 실수 체크)
  warnings?: WarningItem[];

  // 기관 정보
  organization_info: OrganizationInfo;

  // 면접 상세 정보
  interview_detail?: InterviewDetailInfo;

  // 분석 결과
  strengths: StrengthItem[];
  improvements: ImprovementItem[];

  // 키워드 분석
  keyword_analysis: KeywordAnalysis;

  // 핵심가치별 점수
  core_value_scores?: CoreValueScore[];

  // NCS 역량별 점수
  ncs_competency_scores?: NCSCompetencyScore[];

  // 유사 기출문항
  similar_questions?: SimilarQuestion[];

  // 직무별 스킬 매칭
  position_skill_match?: PositionSkillMatch;

  // 면접 준비
  interview_questions: InterviewQuestion[];

  // 자소서 기출문항
  past_questions?: PastQuestion[];

  // 모범 답안
  model_answer: string;
  model_answer_length: number;
}

export interface SkillItem {
  name: string;
  category: string;
}

export interface SkillMatchResult {
  matched: string[];
  missing: string[];
  score: number;
}

export interface SkillAnalysisResponse {
  skills: SkillItem[];
  summary: Record<string, string[]>;
  match_result?: SkillMatchResult;
}

export interface SectionItem {
  type: string;
  content: string;
}

export interface ResumeParseResponse {
  sections: SectionItem[];
  skills: SkillItem[];
  skill_summary: Record<string, string[]>;
  match_result?: SkillMatchResult;
}

export interface Organization {
  code: string;
  name: string;
  keywords: string[];
  core_values: string[];
  positions: string[];
}
