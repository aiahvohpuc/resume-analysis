import { useState, useEffect, useRef, forwardRef, useImperativeHandle, useCallback } from 'react';
import type { NewResumeAnalysisResponse } from '../types/api';
import { exportToPdf } from '../services/pdfExport';
import './AnalysisDashboard.css';

// 헬퍼 함수들을 컴포넌트 외부로 이동 (매 렌더링마다 재생성 방지)
const getScoreColor = (score: number): string => {
  if (score >= 80) return 'excellent';
  if (score >= 60) return 'good';
  if (score >= 40) return 'average';
  return 'poor';
};

const getGradeEmoji = (grade: string): string => {
  switch (grade) {
    case '우수': return '🌟';
    case '양호': return '👍';
    case '보통': return '📝';
    case '미흡': return '⚠️';
    default: return '📊';
  }
};

const getWarningSeverityClass = (severity: string): string => {
  switch (severity) {
    case 'high': return 'severity-high';
    case 'medium': return 'severity-medium';
    case 'low': return 'severity-low';
    default: return 'severity-medium';
  }
};

const getWarningIcon = (type: string): string => {
  switch (type) {
    case 'blind_violation': return '🚫';
    case 'abstract_expression': return '💭';
    case 'no_result':
    case 'missing_result': return '📊';
    case 'wrong_organization': return '🏢';
    default: return '⚠️';
  }
};

interface AnalysisDashboardProps {
  result: NewResumeAnalysisResponse;
}

export interface AnalysisDashboardHandle {
  savePdf: () => Promise<void>;
}

export const AnalysisDashboard = forwardRef<AnalysisDashboardHandle, AnalysisDashboardProps>(
  function AnalysisDashboard({ result }, ref) {
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [copiedModelAnswer, setCopiedModelAnswer] = useState(false);
  const dashboardRef = useRef<HTMLDivElement>(null);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const {
    overall_score,
    overall_grade,
    overall_summary,
    length_check,
    warnings,
    organization_info,
    interview_detail,
    strengths,
    improvements,
    keyword_analysis,
    core_value_scores,
    ncs_competency_scores,
    similar_questions,
    position_skill_match,
    interview_questions,
    past_questions,
    model_answer,
    model_answer_length,
  } = result;

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 200);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
      }
    };
  }, []);

  const scrollToTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleSavePdf = useCallback(async () => {
    if (!dashboardRef.current || isExporting) return;

    setIsExporting(true);
    try {
      const timestamp = new Date().toISOString().slice(0, 10);
      await exportToPdf(
        dashboardRef.current,
        {
          filename: `자기소개서_분석결과_${timestamp}`,
          title: '자기소개서 AI 분석 결과',
        },
        result  // 분석 결과 데이터 전달
      );
    } catch (error) {
      console.error('PDF 생성 실패:', error);
      alert('PDF 생성에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsExporting(false);
    }
  }, [isExporting, result]);

  useImperativeHandle(ref, () => ({
    savePdf: handleSavePdf,
  }));

  const handleCopyModelAnswer = useCallback(async () => {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(model_answer);
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement('textarea');
        textArea.value = model_answer;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopiedModelAnswer(true);
      // 이전 타이머 정리
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
      }
      copyTimeoutRef.current = setTimeout(() => setCopiedModelAnswer(false), 2000);
    } catch (error) {
      console.error('복사 실패:', error);
      alert('복사에 실패했습니다. 텍스트를 직접 선택하여 복사해 주세요.');
    }
  }, [model_answer]);

  return (
    <div className="analysis-dashboard" ref={dashboardRef}>
      {/* 1. 종합 평가 */}
      <section className="dashboard-section score-section">
        <div className="score-header">
          <div className={`overall-score ${getScoreColor(overall_score)}`}>
            <span className="score-value">{overall_score}</span>
            <span className="score-label">점</span>
          </div>
          <div className="score-gauge">
            <div
              className={`gauge-fill ${getScoreColor(overall_score)}`}
              style={{ width: `${overall_score}%` }}
            />
          </div>
          <div className="score-grade">
            <span className="grade-emoji">{getGradeEmoji(overall_grade)}</span>
            <span className="grade-text">{overall_grade}</span>
          </div>
        </div>
        <p className="score-summary">{overall_summary}</p>
        <div className="length-info">
          <span className={`length-status ${length_check.status}`}>
            {length_check.current}/{length_check.max}자
            ({length_check.percentage.toFixed(1)}%)
          </span>
        </div>
      </section>

      {/* 2. 기관 정보 (알아두면 좋은 정보) */}
      {organization_info && (
        <section className="dashboard-section org-info-section">
          <div className="section-title-row">
            <h3 className="section-title">
              <span className="section-icon">🏢</span>
              {organization_info.name} 알아두면 좋은 정보
            </h3>
            {organization_info.data_updated_at && (
              <span className="data-updated">데이터 기준: {organization_info.data_updated_at}</span>
            )}
          </div>
          {organization_info.website && (
            <div className="org-website">
              <span className="website-icon">🔗</span>
              <a href={organization_info.website} target="_blank" rel="noopener noreferrer">
                {organization_info.website}
              </a>
            </div>
          )}
          <div className="org-info-grid">
            {organization_info.core_values.length > 0 && (
              <div className="org-info-item">
                <span className="info-icon">💡</span>
                <div className="info-content">
                  <span className="info-label">핵심가치</span>
                  <div className="info-tags">
                    {organization_info.core_values.map((value, index) => (
                      <span key={index} className="info-tag core-value">{value}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {organization_info.talent_image && (
              <div className="org-info-item">
                <span className="info-icon">👤</span>
                <div className="info-content">
                  <span className="info-label">인재상</span>
                  <p className="info-text">{organization_info.talent_image}</p>
                </div>
              </div>
            )}

            {organization_info.recent_news && organization_info.recent_news.length > 0 && (
              <div className="org-info-item">
                <span className="info-icon">📰</span>
                <div className="info-content">
                  <span className="info-label">최근 동향</span>
                  <ul className="info-list">
                    {organization_info.recent_news.map((news, index) => (
                      <li key={index}>
                        {typeof news === 'string' ? news : (
                          <>
                            {news.category && <span className="news-category">[{news.category}]</span>}
                            {news.url ? (
                              <a
                                href={news.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="news-link"
                              >
                                {news.title}
                              </a>
                            ) : (
                              <span style={{ color: 'red' }}>[URL 없음] {news.title}</span>
                            )}
                            {news.date && <span className="news-date"> ({news.date})</span>}
                          </>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {organization_info.interview_keywords.length > 0 && (
              <div className="org-info-item">
                <span className="info-icon">🎯</span>
                <div className="info-content">
                  <span className="info-label">면접 키워드</span>
                  <div className="info-tags">
                    {organization_info.interview_keywords.map((keyword, index) => (
                      <span key={index} className="info-tag interview-keyword">{keyword}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {organization_info.recruitment_process && organization_info.recruitment_process.length > 0 && (
              <div className="org-info-item recruitment-process-item">
                <span className="info-icon">📋</span>
                <div className="info-content">
                  <span className="info-label">채용 프로세스</span>
                  <div className="recruitment-process-flow">
                    {organization_info.recruitment_process.map((step, index) => (
                      <span key={index} className="process-step">
                        <span className="step-number">{index + 1}</span>
                        <span className="step-name">{step}</span>
                        {index < organization_info.recruitment_process!.length - 1 && (
                          <span className="step-arrow">→</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 3. 블라인드 규칙 위반 검토 */}
      <section className="dashboard-section warnings-section">
        <h3 className="section-title">
          <span className="section-icon">{warnings && warnings.length > 0 ? '🚨' : '✅'}</span> 블라인드 규칙 위반 검토
          {warnings && warnings.length > 0 && (
            <span className="count-badge warning-count">{warnings.length}개</span>
          )}
        </h3>
        {warnings && warnings.length > 0 ? (
          <ul className="warnings-list">
            {warnings.map((warning, index) => (
              <li key={index} className={`warning-item ${getWarningSeverityClass(warning.severity)}`}>
                <div className="warning-header">
                  <span className="warning-icon">{getWarningIcon(warning.type)}</span>
                  <span className={`warning-severity ${warning.severity}`}>
                    {warning.severity === 'high' ? '심각' : warning.severity === 'medium' ? '주의' : '참고'}
                  </span>
                </div>
                <p className="warning-message">{warning.message}</p>
                {warning.detected_text && (
                  <div className="warning-detected">
                    <span className="detected-label">발견:</span>
                    <span className="detected-text">"{warning.detected_text}"</span>
                  </div>
                )}
                {warning.suggestion && (
                  <div className="warning-suggestion">
                    <span className="suggestion-icon">💡</span>
                    <span>{warning.suggestion}</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="no-warnings-message">
            <p>주의사항이 없습니다. 잘 작성하셨습니다!</p>
          </div>
        )}
      </section>

      {/* 4. 잘한 점 */}
      {strengths.length > 0 && (
        <section className="dashboard-section">
          <h3 className="section-title">
            <span className="section-icon">✅</span> 잘한 점
            <span className="count-badge">{strengths.length}개</span>
          </h3>
          <ul className="analysis-list strengths-list">
            {strengths.map((item, index) => (
              <li key={index} className="analysis-item strength-item">
                <div className="item-header">
                  <span className="item-title">{item.title}</span>
                  <span className={`item-score score-high`}>{item.score}/10</span>
                </div>
                <div className="item-quote">
                  <span className="quote-icon">"</span>
                  <p>{item.quote}</p>
                  <span className="quote-icon">"</span>
                </div>
                <p className="item-evaluation">{item.evaluation}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* 5. 개선이 필요한 점 */}
      {improvements.length > 0 && (
        <section className="dashboard-section">
          <h3 className="section-title">
            <span className="section-icon">⚠️</span> 개선이 필요한 점
            <span className="count-badge">{improvements.length}개</span>
          </h3>
          <ul className="analysis-list improvements-list">
            {improvements.map((item, index) => (
              <li key={index} className="analysis-item improvement-item">
                <div className="item-header">
                  <span className="item-title">{item.title}</span>
                  <span className={`item-score ${item.score >= 7 ? 'score-high' : item.score >= 5 ? 'score-mid' : 'score-low'}`}>
                    {item.score}/10
                  </span>
                </div>
                <div className="problem-box">
                  <span className="problem-label">문제점</span>
                  <p>{item.problem}</p>
                </div>
                <div className="comparison-box">
                  <div className="comparison-before">
                    <span className="comparison-label">현재</span>
                    <p>{item.current_text || '해당 내용 없음'}</p>
                  </div>
                  <div className="comparison-arrow">→</div>
                  <div className="comparison-after">
                    <span className="comparison-label">수정 예시</span>
                    <p>{item.improved_text}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* 6. 키워드 분석 */}
      <section className="dashboard-section">
        <h3 className="section-title">
          <span className="section-icon">🔑</span> 키워드 분석
          <span className="match-rate">({keyword_analysis.match_rate.toFixed(0)}% 매칭)</span>
        </h3>
        <div className="keyword-analysis">
          <div className="keyword-group found">
            <h4>✓ 포함됨</h4>
            <div className="keyword-tags">
              {keyword_analysis.found_keywords.length > 0 ? (
                keyword_analysis.found_keywords.map((kw, index) => (
                  <span key={index} className="keyword-tag found">
                    {kw}
                  </span>
                ))
              ) : (
                <span className="no-keywords">없음</span>
              )}
            </div>
          </div>
          <div className="keyword-group missing">
            <h4>✗ 누락됨</h4>
            <div className="keyword-tags">
              {keyword_analysis.missing_keywords.length > 0 ? (
                keyword_analysis.missing_keywords.map((kw, index) => (
                  <span key={index} className="keyword-tag missing">
                    {kw}
                  </span>
                ))
              ) : (
                <span className="no-keywords">없음</span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 7. 핵심가치별 점수 */}
      {core_value_scores && core_value_scores.length > 0 && (
        <section className="dashboard-section core-values-section">
          <h3 className="section-title">
            <span className="section-icon">💎</span> 핵심가치 반영도
            <span className="match-rate">
              ({core_value_scores.filter(v => v.found).length}/{core_value_scores.length} 반영)
            </span>
          </h3>
          <div className="core-values-grid">
            {core_value_scores.map((cv, index) => (
              <div key={index} className={`core-value-item ${cv.found ? 'found' : 'missing'}`}>
                <div className="cv-header">
                  <span className="cv-name">{cv.value}</span>
                  <span className={`cv-score ${cv.score >= 7 ? 'high' : cv.score >= 5 ? 'mid' : 'low'}`}>
                    {cv.score}/10
                  </span>
                </div>
                <div className="cv-bar">
                  <div
                    className={`cv-bar-fill ${cv.score >= 7 ? 'high' : cv.score >= 5 ? 'mid' : 'low'}`}
                    style={{ width: `${cv.score * 10}%` }}
                  />
                </div>
                {cv.found && cv.evidence && (
                  <p className="cv-evidence">
                    <span className="evidence-icon">✓</span> {cv.evidence}
                  </p>
                )}
                {!cv.found && cv.suggestion && (
                  <p className="cv-suggestion">
                    <span className="suggestion-icon">💡</span> {cv.suggestion}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 8. NCS 역량별 점수 */}
      {ncs_competency_scores && ncs_competency_scores.length > 0 && (
        <section className="dashboard-section ncs-section">
          <h3 className="section-title">
            <span className="section-icon">📊</span> NCS 역량별 반영도
            <span className="match-rate">
              ({ncs_competency_scores.filter(n => n.found).length}/{ncs_competency_scores.length} 반영)
            </span>
          </h3>
          <div className="ncs-grid">
            {ncs_competency_scores.map((ncs, index) => (
              <div key={index} className={`ncs-item ${ncs.found ? 'found' : 'missing'} ${ncs.importance === '필수' ? 'required' : ''}`}>
                <div className="ncs-header">
                  <span className="ncs-name">{ncs.name}</span>
                  <div className="ncs-badges">
                    {ncs.importance === '필수' && (
                      <span className="importance-badge required">필수</span>
                    )}
                    <span className={`ncs-score ${ncs.score >= 7 ? 'high' : ncs.score >= 5 ? 'mid' : 'low'}`}>
                      {ncs.score}/10
                    </span>
                  </div>
                </div>
                <div className="ncs-bar">
                  <div
                    className={`ncs-bar-fill ${ncs.score >= 7 ? 'high' : ncs.score >= 5 ? 'mid' : 'low'}`}
                    style={{ width: `${ncs.score * 10}%` }}
                  />
                </div>
                {ncs.found && ncs.evidence && (
                  <p className="ncs-evidence">
                    <span className="evidence-icon">✓</span> {ncs.evidence}
                  </p>
                )}
                {!ncs.found && ncs.suggestion && (
                  <p className="ncs-suggestion">
                    <span className="suggestion-icon">💡</span> {ncs.suggestion}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 9. 직무별 스킬 매칭 */}
      {position_skill_match && (
        position_skill_match.matched_majors.length > 0 ||
        position_skill_match.missing_majors.length > 0 ||
        position_skill_match.matched_certifications.length > 0 ||
        position_skill_match.missing_certifications.length > 0 ||
        position_skill_match.matched_skills.length > 0 ||
        position_skill_match.missing_skills.length > 0
      ) && (
        <section className="dashboard-section skill-match-section">
          <h3 className="section-title">
            <span className="section-icon">🎯</span> 직무별 우대사항 매칭
            <span className="match-rate">
              ({position_skill_match.overall_match_rate.toFixed(0)}% 매칭)
            </span>
          </h3>
          <div className="skill-match-grid">
            {/* 전공 */}
            {(position_skill_match.matched_majors.length > 0 || position_skill_match.missing_majors.length > 0) && (
              <div className="skill-match-category">
                <h4 className="category-title">
                  <span className="category-icon">🎓</span> 관련 전공
                </h4>
                <div className="skill-match-tags">
                  {position_skill_match.matched_majors.map((major, index) => (
                    <span key={`matched-major-${index}`} className="skill-tag matched">{major}</span>
                  ))}
                  {position_skill_match.missing_majors.map((major, index) => (
                    <span key={`missing-major-${index}`} className="skill-tag missing">{major}</span>
                  ))}
                </div>
              </div>
            )}

            {/* 자격증 */}
            {(position_skill_match.matched_certifications.length > 0 || position_skill_match.missing_certifications.length > 0) && (
              <div className="skill-match-category">
                <h4 className="category-title">
                  <span className="category-icon">📜</span> 관련 자격증
                </h4>
                <div className="skill-match-tags">
                  {position_skill_match.matched_certifications.map((cert, index) => (
                    <span key={`matched-cert-${index}`} className="skill-tag matched">{cert}</span>
                  ))}
                  {position_skill_match.missing_certifications.map((cert, index) => (
                    <span key={`missing-cert-${index}`} className="skill-tag missing">{cert}</span>
                  ))}
                </div>
              </div>
            )}

            {/* 스킬 */}
            {(position_skill_match.matched_skills.length > 0 || position_skill_match.missing_skills.length > 0) && (
              <div className="skill-match-category">
                <h4 className="category-title">
                  <span className="category-icon">💼</span> 관련 스킬
                </h4>
                <div className="skill-match-tags">
                  {position_skill_match.matched_skills.map((skill, index) => (
                    <span key={`matched-skill-${index}`} className="skill-tag matched">{skill}</span>
                  ))}
                  {position_skill_match.missing_skills.map((skill, index) => (
                    <span key={`missing-skill-${index}`} className="skill-tag missing">{skill}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
          {position_skill_match.recommendation && (
            <div className="skill-match-recommendation">
              <span className="recommendation-icon">💡</span>
              <span>{position_skill_match.recommendation}</span>
            </div>
          )}
        </section>
      )}

      {/* 10. 자소서 기출/예상 문항 */}
      {past_questions && past_questions.length > 0 && (
        <section className="dashboard-section past-questions-section">
          <h3 className="section-title">
            <span className="section-icon">📚</span> 자소서 기출/예상 문항
          </h3>
          <ul className="past-questions-list">
            {past_questions.map((q, index) => (
              <li key={index} className="past-question-item">
                <div className="pq-header">
                  <span className="pq-year">{q.year}년 {q.half}</span>
                  <span className={`pq-type-badge ${q.is_prediction ? 'prediction' : 'past'}`}>
                    {q.is_prediction ? '출제 예상' : '기출'}
                  </span>
                  {q.char_limit && q.char_limit > 0 && (
                    <span className="pq-limit">{q.char_limit}자</span>
                  )}
                </div>
                <p className="pq-text">{q.question}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* 11. 유사 기출문항 */}
      {similar_questions && similar_questions.length > 0 && (
        <section className="dashboard-section similar-questions-section">
          <h3 className="section-title">
            <span className="section-icon">🔍</span> 유사 기출문항 분석
          </h3>
          <p className="section-desc">현재 질문과 유사한 과거 기출문항입니다.</p>
          <ul className="similar-questions-list">
            {similar_questions.map((sq, index) => (
              <li key={index} className="similar-question-item">
                <div className="sq-header">
                  <span className="sq-year">{sq.year}년 {sq.half}</span>
                  <span className={`sq-similarity ${sq.similarity >= 70 ? 'high' : sq.similarity >= 50 ? 'mid' : 'low'}`}>
                    {sq.similarity.toFixed(0)}% 유사
                  </span>
                  {sq.char_limit && sq.char_limit > 0 && (
                    <span className="sq-limit">{sq.char_limit}자</span>
                  )}
                </div>
                <p className="sq-text">{sq.question}</p>
                {sq.matched_keywords.length > 0 && (
                  <div className="sq-keywords">
                    <span className="keywords-label">일치 키워드:</span>
                    {sq.matched_keywords.map((kw, kwIndex) => (
                      <span key={kwIndex} className="sq-keyword">{kw}</span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* 12. 면접 상세 정보 */}
      {interview_detail && (interview_detail.format_type || (interview_detail.stages && interview_detail.stages.length > 0) || (interview_detail.frequent_questions && interview_detail.frequent_questions.length > 0)) && (
        <section className="dashboard-section interview-detail-section">
          <h3 className="section-title">
            <span className="section-icon">🎯</span> 면접 상세 정보
          </h3>
          <div className="interview-detail-grid">
            {interview_detail.format_type && (
              <div className="interview-detail-item">
                <span className="detail-label">면접 형식</span>
                <span className="detail-value">{interview_detail.format_type}</span>
              </div>
            )}
            {interview_detail.stages && interview_detail.stages.length > 0 && (
              <div className="interview-detail-item stages">
                <span className="detail-label">전형 단계</span>
                <div className="stages-list">
                  {interview_detail.stages.map((stage, index) => (
                    <span key={index} className="stage-badge">
                      {index + 1}. {stage}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {interview_detail.duration && (
              <div className="interview-detail-item">
                <span className="detail-label">면접 시간</span>
                <span className="detail-value">{interview_detail.duration}</span>
              </div>
            )}
            {interview_detail.difficulty && (
              <div className="interview-detail-item">
                <span className="detail-label">난이도</span>
                <span className={`detail-value difficulty ${interview_detail.difficulty.includes('상') || interview_detail.difficulty.includes('높') ? 'high' : interview_detail.difficulty.includes('하') || interview_detail.difficulty.includes('낮') ? 'low' : 'medium'}`}>
                  {interview_detail.difficulty}
                </span>
              </div>
            )}
            {interview_detail.pass_rate && (
              <div className="interview-detail-item">
                <span className="detail-label">합격률</span>
                <span className="detail-value">{interview_detail.pass_rate}</span>
              </div>
            )}
          </div>

          {/* 고빈도 면접 질문 */}
          {interview_detail.frequent_questions && interview_detail.frequent_questions.length > 0 && (
            <div className="frequent-questions-box">
              <h4 className="frequent-questions-title">
                <span>⭐</span> 고빈도 면접 질문 TOP {interview_detail.frequent_questions.length}
              </h4>
              <ul className="frequent-questions-list">
                {interview_detail.frequent_questions.map((q, index) => (
                  <li key={index} className="frequent-question-item">
                    <div className="fq-header">
                      <span className="fq-number">{index + 1}</span>
                      <span className="fq-question">{q.question}</span>
                      <span className={`fq-frequency ${q.frequency}`}>
                        {q.frequency === 'high' ? '매우 빈출' : '빈출'}
                      </span>
                    </div>
                    <div className="fq-meta">
                      <span className="fq-category">[{q.category}]</span>
                      {q.tips && (
                        <span className="fq-tips">
                          <span className="tips-icon">💡</span> {q.tips}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* 13. 예상 면접 질문 */}
      {interview_questions.length > 0 && (
        <section className="dashboard-section interview-questions-section">
          <h3 className="section-title">
            <span className="section-icon">🎤</span> 예상 면접 질문 & 답변 예시
          </h3>
          <ul className="interview-list">
            {interview_questions.map((item, index) => (
              <li key={index} className="interview-item">
                <div className="question-header">
                  <span className="question-number">Q{index + 1}.</span>
                  <span className="question-text">{item.question}</span>
                  {item.is_frequent && item.years && item.years.length > 0 && (
                    <span className="frequent-badge">
                      {item.years.join(', ')}년 기출 ⭐
                    </span>
                  )}
                  {item.is_frequent && (!item.years || item.years.length === 0) && (
                    <span className="frequent-badge">기출 ⭐</span>
                  )}
                  {!item.is_frequent && (
                    <span className="prediction-badge">출제 예상 🎯</span>
                  )}
                </div>
                <div className="answer-tips">
                  <span className="tips-icon">💡</span>
                  <span className="tips-label">답변 포인트:</span>
                  <span className="tips-text">{item.answer_tips}</span>
                </div>
                {item.sample_answer && (
                  <div className="sample-answer">
                    <span className="sample-label">
                      <span className="sample-icon">📝</span> 예시 답변 (자소서 기반):
                    </span>
                    <p className="sample-text">{item.sample_answer}</p>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* 14. 모범 답안 */}
      {model_answer && (
        <section className="dashboard-section model-answer-section">
          <h3 className="section-title">
            <span className="section-icon">📝</span> 모범 답안 (AI 추천)
            <span className="model-answer-disclaimer">지원자가 제출한 자기소개서를 토대로 작성되었으며, AI는 실수를 할 수 있습니다.</span>
            <button
              className={`copy-btn ${copiedModelAnswer ? 'copied' : ''}`}
              onClick={handleCopyModelAnswer}
            >
              {copiedModelAnswer ? '✓ 복사됨' : '복사'}
            </button>
          </h3>
          <div className="model-answer-content">
            <p className="model-answer-text">{model_answer}</p>
            <div className="model-answer-meta">
              <span className="meta-item">
                📊 글자 수: {model_answer_length}자 / {length_check.max}자
                ({((model_answer_length / length_check.max) * 100).toFixed(1)}%)
              </span>
            </div>
          </div>
        </section>
      )}

      {/* PDF 저장 버튼 (하단) */}
      <div className="pdf-save-container bottom">
        <button
          className="pdf-save-btn"
          onClick={handleSavePdf}
          disabled={isExporting}
        >
          {isExporting ? 'PDF 생성 중...' : 'PDF로 저장'}
        </button>
      </div>

      {/* 맨 위로 버튼 */}
      {showScrollTop && (
        <button className="scroll-top-btn" onClick={scrollToTop} aria-label="맨 위로">
          ↑
        </button>
      )}
    </div>
  );
});
