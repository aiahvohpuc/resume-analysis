import html2pdf from 'html2pdf.js';
import type { NewResumeAnalysisResponse } from '../types/api';

export interface PdfExportOptions {
  filename?: string;
  title?: string;
}

/**
 * PDF 전용 HTML을 생성하여 내보내기
 * 브라우저 렌더링과 별개로 PDF에 최적화된 레이아웃 사용
 */
export async function exportToPdf(
  _element: HTMLElement,
  options: PdfExportOptions = {},
  analysisResult?: NewResumeAnalysisResponse
): Promise<void> {
  const { filename = '자기소개서_분석결과', title = '자기소개서 AI 분석 결과' } = options;

  // analysisResult가 없으면 element에서 데이터 추출 시도
  if (!analysisResult) {
    console.warn('analysisResult not provided, PDF may not render correctly');
    // 기존 방식 fallback
    return exportToPdfLegacy(_element, options);
  }

  const pdfHtml = generatePdfHtml(analysisResult, title);

  const container = document.createElement('div');
  container.innerHTML = pdfHtml;
  document.body.appendChild(container);

  const opt = {
    margin: [10, 10, 10, 10] as [number, number, number, number],
    filename: `${filename}.pdf`,
    image: { type: 'jpeg' as const, quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      logging: false,
    },
    jsPDF: {
      unit: 'mm' as const,
      format: 'a4' as const,
      orientation: 'portrait' as const,
    },
    pagebreak: {
      mode: ['avoid-all', 'css'] as ('avoid-all' | 'css' | 'legacy')[],
      before: '.pdf-page-break-before',
      avoid: '.pdf-no-break',
    },
  };

  try {
    const pdfElement = container.firstElementChild as HTMLElement;
    if (!pdfElement) {
      throw new Error('PDF element not found');
    }
    await html2pdf().set(opt).from(pdfElement).save();
  } finally {
    document.body.removeChild(container);
  }
}

function generatePdfHtml(result: NewResumeAnalysisResponse, title: string): string {
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

  const today = new Date().toLocaleDateString('ko-KR');

  return `
    <div style="font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; width: 190mm; padding: 0; color: #333; font-size: 11pt; line-height: 1.5;">

      <!-- 헤더 -->
      <div style="text-align: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #3b82f6;">
        <h1 style="font-size: 18pt; color: #1e293b; margin: 0 0 5px 0;">${title}</h1>
        <p style="font-size: 9pt; color: #64748b; margin: 0;">생성일: ${today}</p>
      </div>

      <!-- 종합 평가 -->
      <div class="pdf-no-break" style="background: #6366f1; color: white; padding: 15px; border-radius: 8px; margin-bottom: 12px;">
        <div style="margin-bottom: 10px;">
          <span style="font-size: 28pt; font-weight: bold;">${overall_score}</span>
          <span style="font-size: 14pt;">점</span>
          <span style="margin-left: 15px; font-size: 14pt;">${getGradeEmoji(overall_grade)} ${overall_grade}</span>
        </div>
        <div style="background: rgba(255,255,255,0.3); height: 8px; border-radius: 4px; margin-bottom: 10px;">
          <div style="background: white; height: 8px; border-radius: 4px; width: ${overall_score}%;"></div>
        </div>
        <p style="margin: 0; font-size: 10pt;">${overall_summary}</p>
        <p style="margin: 8px 0 0 0; font-size: 9pt; text-align: right;">
          글자 수: ${length_check.current}/${length_check.max}자 (${length_check.percentage.toFixed(1)}%)
        </p>
      </div>

      <!-- 기관 정보 -->
      ${organization_info ? `
      <div class="pdf-no-break" style="background: #f0fdf4; border: 1px solid #86efac; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #166534; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #86efac;">
          🏢 ${organization_info.name} 알아두면 좋은 정보
          ${organization_info.data_updated_at ? `<span style="font-size: 8pt; color: #64748b; font-weight: normal; margin-left: 10px;">데이터 기준: ${organization_info.data_updated_at}</span>` : ''}
        </h2>

        ${organization_info.website ? `
        <p style="margin: 0 0 8px 0; font-size: 9pt; color: #059669;">🔗 ${organization_info.website}</p>
        ` : ''}

        ${organization_info.core_values.length > 0 ? `
        <div style="margin-bottom: 8px;">
          <span style="font-size: 9pt; font-weight: bold; color: #166534;">💡 핵심가치: </span>
          <span style="font-size: 9pt;">${organization_info.core_values.join(', ')}</span>
        </div>
        ` : ''}

        ${organization_info.talent_image ? `
        <div style="margin-bottom: 8px;">
          <span style="font-size: 9pt; font-weight: bold; color: #166534;">👤 인재상: </span>
          <span style="font-size: 9pt;">${organization_info.talent_image}</span>
        </div>
        ` : ''}

        ${organization_info.recent_news && organization_info.recent_news.length > 0 ? `
        <div style="margin-bottom: 8px;">
          <span style="font-size: 9pt; font-weight: bold; color: #166534;">📰 최근 동향:</span>
          <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 9pt;">
            ${organization_info.recent_news.map(news =>
              `<li>${typeof news === 'string' ? news : `${news.category ? `[${news.category}] ` : ''}${news.url ? `<a href="${news.url}" style="color: #0ea5e9;">${news.title}</a>` : news.title}${news.date ? ` (${news.date})` : ''}`}</li>`
            ).join('')}
          </ul>
        </div>
        ` : ''}

        ${organization_info.interview_keywords.length > 0 ? `
        <div>
          <span style="font-size: 9pt; font-weight: bold; color: #166534;">🎯 면접 키워드: </span>
          <span style="font-size: 9pt;">${organization_info.interview_keywords.join(', ')}</span>
        </div>
        ` : ''}

        ${organization_info.recruitment_process && organization_info.recruitment_process.length > 0 ? `
        <div style="margin-top: 8px;">
          <span style="font-size: 9pt; font-weight: bold; color: #166534;">📋 채용 프로세스: </span>
          <span style="font-size: 9pt;">
            ${organization_info.recruitment_process.map((step, i) => `<span style="display: inline-block; background: #dbeafe; padding: 2px 6px; border-radius: 10px; margin: 2px; font-size: 8pt;">${i + 1}. ${step}</span>`).join(' → ')}
          </span>
        </div>
        ` : ''}
      </div>
      ` : ''}

      <!-- 블라인드 규칙 위반 검토 -->
      <div class="pdf-no-break" style="background: ${warnings && warnings.length > 0 ? '#fffbeb' : '#ecfdf5'}; border: 1px solid ${warnings && warnings.length > 0 ? '#fde68a' : '#a7f3d0'}; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: ${warnings && warnings.length > 0 ? '#92400e' : '#047857'}; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid ${warnings && warnings.length > 0 ? '#fde68a' : '#a7f3d0'};">
          ${warnings && warnings.length > 0 ? '🚨' : '✅'} 블라인드 규칙 위반 검토 ${warnings && warnings.length > 0 ? `(${warnings.length}개)` : ''}
        </h2>
        ${warnings && warnings.length > 0 ? `
        ${warnings.map((warning, idx) => `
        <div style="background: white; border-left: 3px solid ${warning.severity === 'high' ? '#dc2626' : warning.severity === 'medium' ? '#f59e0b' : '#3b82f6'}; padding: 8px 10px; margin-bottom: ${idx < warnings.length - 1 ? '8px' : '0'}; border-radius: 0 6px 6px 0;">
          <p style="margin: 0 0 4px 0; font-size: 9pt;">
            <span style="margin-right: 6px;">${getWarningIcon(warning.type)}</span>
            <span style="background: ${warning.severity === 'high' ? '#fee2e2' : warning.severity === 'medium' ? '#fef3c7' : '#dbeafe'}; color: ${warning.severity === 'high' ? '#991b1b' : warning.severity === 'medium' ? '#92400e' : '#1e40af'}; font-size: 8pt; padding: 2px 6px; border-radius: 4px; font-weight: bold;">${warning.severity === 'high' ? '심각' : warning.severity === 'medium' ? '주의' : '참고'}</span>
          </p>
          <p style="margin: 4px 0; font-size: 9pt; color: #374151;">${warning.message}</p>
          ${warning.detected_text ? `
          <p style="margin: 4px 0; font-size: 8pt; background: #fef2f2; padding: 4px 6px; border-radius: 4px; color: #7f1d1d;">
            <span style="font-weight: bold; color: #991b1b;">발견:</span> "${warning.detected_text}"
          </p>
          ` : ''}
          ${warning.suggestion ? `
          <p style="margin: 4px 0 0 0; font-size: 8pt; background: #f0fdf4; padding: 4px 6px; border-radius: 4px; color: #166534;">
            💡 ${warning.suggestion}
          </p>
          ` : ''}
        </div>
        `).join('')}
        ` : `
        <p style="margin: 0; font-size: 10pt; color: #047857; text-align: center; font-weight: 500;">주의사항이 없습니다. 잘 작성하셨습니다!</p>
        `}
      </div>

      <!-- 잘한 점 -->
      ${strengths.length > 0 ? `
      <div style="background: white; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #16a34a; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
          ✅ 잘한 점 (${strengths.length}개)
        </h2>
        ${strengths.map((item, idx) => `
        <div class="pdf-no-break" style="background: #f8fafc; border-left: 3px solid #22c55e; padding: 10px; margin-bottom: ${idx < strengths.length - 1 ? '10px' : '0'}; border-radius: 0 6px 6px 0;">
          <div style="margin-bottom: 6px;">
            <span style="font-weight: bold; font-size: 10pt;">${item.title}</span>
            <span style="float: right; font-size: 9pt; color: #16a34a;">${item.score}/10</span>
          </div>
          <div style="background: #f0fdf4; padding: 8px; border-radius: 4px; margin-bottom: 6px; font-size: 9pt; font-style: italic; color: #166534;">
            "${item.quote}"
          </div>
          <p style="margin: 0; font-size: 9pt; color: #475569;">${item.evaluation}</p>
        </div>
        `).join('')}
      </div>
      ` : ''}

      <!-- 개선이 필요한 점 -->
      ${improvements.length > 0 ? `
      <div style="background: white; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #d97706; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
          ⚠️ 개선이 필요한 점 (${improvements.length}개)
        </h2>
        ${improvements.map((item, idx) => `
        <div class="pdf-no-break" style="background: #f8fafc; border-left: 3px solid #f59e0b; padding: 10px; margin-bottom: ${idx < improvements.length - 1 ? '10px' : '0'}; border-radius: 0 6px 6px 0;">
          <div style="margin-bottom: 6px;">
            <span style="font-weight: bold; font-size: 10pt;">${item.title}</span>
            <span style="float: right; font-size: 9pt; color: #d97706;">${item.score}/10</span>
          </div>
          <div style="background: #fef3c7; padding: 8px; border-radius: 4px; margin-bottom: 8px;">
            <span style="font-size: 8pt; font-weight: bold; color: #92400e;">문제점</span>
            <p style="margin: 4px 0 0 0; font-size: 9pt; color: #78350f;">${item.problem}</p>
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: 9pt;">
            <tr>
              <td style="width: 48%; vertical-align: top; padding: 8px; background: #fee2e2; border-radius: 4px;">
                <span style="font-size: 8pt; font-weight: bold; color: #dc2626;">현재</span>
                <p style="margin: 4px 0 0 0; color: #374151;">${item.current_text || '해당 내용 없음'}</p>
              </td>
              <td style="width: 4%; text-align: center; vertical-align: middle; color: #9ca3af;">→</td>
              <td style="width: 48%; vertical-align: top; padding: 8px; background: #d1fae5; border-radius: 4px;">
                <span style="font-size: 8pt; font-weight: bold; color: #16a34a;">수정 예시</span>
                <p style="margin: 4px 0 0 0; color: #374151;">${item.improved_text}</p>
              </td>
            </tr>
          </table>
        </div>
        `).join('')}
      </div>
      ` : ''}

      <!-- 키워드 분석 -->
      <div class="pdf-no-break" style="background: white; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #1e293b; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
          🔑 키워드 분석 <span style="font-size: 10pt; color: #64748b; font-weight: normal;">(${keyword_analysis.match_rate.toFixed(0)}% 매칭)</span>
        </h2>
        <table style="width: 100%; border-collapse: collapse; font-size: 9pt;">
          <tr>
            <td style="width: 50%; vertical-align: top; padding-right: 10px;">
              <p style="margin: 0 0 6px 0; font-weight: bold; color: #16a34a;">✓ 포함됨</p>
              <p style="margin: 0; color: #166534;">
                ${keyword_analysis.found_keywords.length > 0
                  ? keyword_analysis.found_keywords.map(kw => `<span style="display: inline-block; background: #dcfce7; padding: 2px 8px; border-radius: 10px; margin: 2px;">${kw}</span>`).join(' ')
                  : '<span style="color: #9ca3af; font-style: italic;">없음</span>'}
              </p>
            </td>
            <td style="width: 50%; vertical-align: top; padding-left: 10px; border-left: 1px solid #e2e8f0;">
              <p style="margin: 0 0 6px 0; font-weight: bold; color: #dc2626;">✗ 누락됨</p>
              <p style="margin: 0; color: #991b1b;">
                ${keyword_analysis.missing_keywords.length > 0
                  ? keyword_analysis.missing_keywords.map(kw => `<span style="display: inline-block; background: #fee2e2; padding: 2px 8px; border-radius: 10px; margin: 2px;">${kw}</span>`).join(' ')
                  : '<span style="color: #9ca3af; font-style: italic;">없음</span>'}
              </p>
            </td>
          </tr>
        </table>
      </div>

      <!-- 핵심가치별 점수 -->
      ${core_value_scores && core_value_scores.length > 0 ? `
      <div class="pdf-no-break" style="background: #fffbeb; border: 1px solid #fbbf24; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #92400e; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #fbbf24;">
          💎 핵심가치 반영도 <span style="font-size: 10pt; color: #64748b; font-weight: normal;">(${core_value_scores.filter(v => v.found).length}/${core_value_scores.length} 반영)</span>
        </h2>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
          ${core_value_scores.map(cv => `
          <div style="flex: 1 1 45%; min-width: 150px; background: white; padding: 8px; border-radius: 6px; border-left: 3px solid ${cv.found ? '#22c55e' : '#f59e0b'};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-weight: 600; font-size: 9pt; color: #1f2937;">${cv.value}</span>
              <span style="font-size: 8pt; font-weight: 600; padding: 2px 6px; border-radius: 4px; background: ${cv.score >= 7 ? '#dcfce7' : cv.score >= 5 ? '#fef3c7' : '#fee2e2'}; color: ${cv.score >= 7 ? '#166534' : cv.score >= 5 ? '#92400e' : '#991b1b'};">${cv.score}/10</span>
            </div>
            <div style="height: 4px; background: #e5e7eb; border-radius: 2px; overflow: hidden; margin-bottom: 4px;">
              <div style="height: 100%; width: ${cv.score * 10}%; background: ${cv.score >= 7 ? '#22c55e' : cv.score >= 5 ? '#fbbf24' : '#f87171'};"></div>
            </div>
            ${cv.found && cv.evidence ? `<p style="margin: 0; font-size: 7pt; color: #166534; background: #f0fdf4; padding: 3px 5px; border-radius: 3px;">✓ ${cv.evidence}</p>` : ''}
            ${!cv.found && cv.suggestion ? `<p style="margin: 0; font-size: 7pt; color: #92400e; background: #fffbeb; padding: 3px 5px; border-radius: 3px;">💡 ${cv.suggestion}</p>` : ''}
          </div>
          `).join('')}
        </div>
      </div>
      ` : ''}

      <!-- NCS 역량별 점수 -->
      ${ncs_competency_scores && ncs_competency_scores.length > 0 ? `
      <div class="pdf-no-break" style="background: #f5f3ff; border: 1px solid #c4b5fd; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #6d28d9; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #c4b5fd;">
          📊 NCS 역량별 반영도 <span style="font-size: 10pt; color: #64748b; font-weight: normal;">(${ncs_competency_scores.filter(n => n.found).length}/${ncs_competency_scores.length} 반영)</span>
        </h2>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
          ${ncs_competency_scores.map(ncs => `
          <div style="flex: 1 1 45%; min-width: 150px; background: white; padding: 8px; border-radius: 6px; border-left: 3px solid ${ncs.found ? '#22c55e' : (ncs.importance === '필수' ? '#dc2626' : '#f59e0b')};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-weight: 600; font-size: 9pt; color: #1f2937;">${ncs.name}</span>
              <span style="font-size: 8pt;">
                ${ncs.importance === '필수' ? '<span style="background: #fee2e2; color: #991b1b; padding: 1px 4px; border-radius: 3px; font-size: 7pt; margin-right: 4px;">필수</span>' : ''}
                <span style="font-weight: 600; padding: 2px 6px; border-radius: 4px; background: ${ncs.score >= 7 ? '#dcfce7' : ncs.score >= 5 ? '#fef3c7' : '#fee2e2'}; color: ${ncs.score >= 7 ? '#166534' : ncs.score >= 5 ? '#92400e' : '#991b1b'};">${ncs.score}/10</span>
              </span>
            </div>
            <div style="height: 4px; background: #e5e7eb; border-radius: 2px; overflow: hidden; margin-bottom: 4px;">
              <div style="height: 100%; width: ${ncs.score * 10}%; background: ${ncs.score >= 7 ? '#8b5cf6' : ncs.score >= 5 ? '#fbbf24' : '#f87171'};"></div>
            </div>
            ${ncs.found && ncs.evidence ? `<p style="margin: 0; font-size: 7pt; color: #166534; background: #f0fdf4; padding: 3px 5px; border-radius: 3px;">✓ ${ncs.evidence}</p>` : ''}
            ${!ncs.found && ncs.suggestion ? `<p style="margin: 0; font-size: 7pt; color: #92400e; background: #fffbeb; padding: 3px 5px; border-radius: 3px;">💡 ${ncs.suggestion}</p>` : ''}
          </div>
          `).join('')}
        </div>
      </div>
      ` : ''}

      <!-- 직무별 스킬 매칭 -->
      ${position_skill_match && (
        position_skill_match.matched_majors.length > 0 ||
        position_skill_match.missing_majors.length > 0 ||
        position_skill_match.matched_certifications.length > 0 ||
        position_skill_match.missing_certifications.length > 0 ||
        position_skill_match.matched_skills.length > 0 ||
        position_skill_match.missing_skills.length > 0
      ) ? `
      <div class="pdf-no-break" style="background: #f0fdf4; border: 1px solid #86efac; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #166534; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #86efac;">
          🎯 직무별 우대사항 매칭 <span style="font-size: 10pt; color: #64748b; font-weight: normal;">(${position_skill_match.overall_match_rate.toFixed(0)}% 매칭)</span>
        </h2>

        ${(position_skill_match.matched_majors.length > 0 || position_skill_match.missing_majors.length > 0) ? `
        <div style="background: white; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;">
          <p style="margin: 0 0 6px 0; font-size: 9pt; font-weight: bold; color: #166534;">🎓 관련 전공</p>
          <p style="margin: 0; font-size: 9pt;">
            ${position_skill_match.matched_majors.map(m => `<span style="display: inline-block; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px; margin: 2px; border: 1px solid #86efac;">✓ ${m}</span>`).join('')}
            ${position_skill_match.missing_majors.map(m => `<span style="display: inline-block; background: #fef2f2; color: #991b1b; padding: 2px 8px; border-radius: 10px; margin: 2px; border: 1px solid #fecaca;">○ ${m}</span>`).join('')}
          </p>
        </div>
        ` : ''}

        ${(position_skill_match.matched_certifications.length > 0 || position_skill_match.missing_certifications.length > 0) ? `
        <div style="background: white; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;">
          <p style="margin: 0 0 6px 0; font-size: 9pt; font-weight: bold; color: #166534;">📜 관련 자격증</p>
          <p style="margin: 0; font-size: 9pt;">
            ${position_skill_match.matched_certifications.map(c => `<span style="display: inline-block; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px; margin: 2px; border: 1px solid #86efac;">✓ ${c}</span>`).join('')}
            ${position_skill_match.missing_certifications.map(c => `<span style="display: inline-block; background: #fef2f2; color: #991b1b; padding: 2px 8px; border-radius: 10px; margin: 2px; border: 1px solid #fecaca;">○ ${c}</span>`).join('')}
          </p>
        </div>
        ` : ''}

        ${(position_skill_match.matched_skills.length > 0 || position_skill_match.missing_skills.length > 0) ? `
        <div style="background: white; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;">
          <p style="margin: 0 0 6px 0; font-size: 9pt; font-weight: bold; color: #166534;">💼 관련 스킬</p>
          <p style="margin: 0; font-size: 9pt;">
            ${position_skill_match.matched_skills.map(s => `<span style="display: inline-block; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px; margin: 2px; border: 1px solid #86efac;">✓ ${s}</span>`).join('')}
            ${position_skill_match.missing_skills.map(s => `<span style="display: inline-block; background: #fef2f2; color: #991b1b; padding: 2px 8px; border-radius: 10px; margin: 2px; border: 1px solid #fecaca;">○ ${s}</span>`).join('')}
          </p>
        </div>
        ` : ''}

        ${position_skill_match.recommendation ? `
        <div style="background: #fffbeb; padding: 8px 10px; border-radius: 6px; border: 1px solid #fde68a;">
          <p style="margin: 0; font-size: 9pt; color: #92400e;">💡 ${position_skill_match.recommendation}</p>
        </div>
        ` : ''}
      </div>
      ` : ''}

      <!-- 자소서 기출/예상 문항 -->
      ${past_questions && past_questions.length > 0 ? `
      <div class="pdf-no-break" style="background: #faf5ff; border: 1px solid #e9d5ff; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #7c3aed; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #e9d5ff;">
          📚 자소서 기출/예상 문항
        </h2>
        ${past_questions.map((q, idx) => `
        <div style="background: white; padding: 10px; margin-bottom: ${idx < past_questions.length - 1 ? '8px' : '0'}; border-radius: 6px; border: 1px solid #e9d5ff;">
          <p style="margin: 0 0 4px 0; font-size: 9pt;">
            <span style="background: #ede9fe; color: #7c3aed; padding: 2px 6px; border-radius: 4px; font-weight: bold;">${q.year}년 ${q.half || ''}</span>
            <span style="background: ${q.is_prediction ? '#fef3c7' : '#dcfce7'}; color: ${q.is_prediction ? '#92400e' : '#166534'}; padding: 2px 6px; border-radius: 4px; font-size: 8pt; margin-left: 4px;">${q.is_prediction ? '출제 예상' : '기출'}</span>
            ${q.char_limit ? `<span style="color: #8b5cf6; font-size: 8pt; margin-left: 4px;">${q.char_limit}자</span>` : ''}
          </p>
          <p style="margin: 6px 0 0 0; font-size: 9pt; color: #374151;">${q.question}</p>
        </div>
        `).join('')}
      </div>
      ` : ''}

      <!-- 유사 기출문항 -->
      ${similar_questions && similar_questions.length > 0 ? `
      <div class="pdf-no-break" style="background: #ecfdf5; border: 1px solid #6ee7b7; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #047857; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #6ee7b7;">
          🔍 유사 기출문항 분석
        </h2>
        ${similar_questions.map((sq, idx) => `
        <div style="background: white; padding: 8px 10px; margin-bottom: ${idx < similar_questions.length - 1 ? '8px' : '0'}; border-radius: 6px; border-left: 3px solid #10b981;">
          <p style="margin: 0 0 4px 0; font-size: 9pt;">
            <span style="background: #d1fae5; color: #047857; padding: 2px 6px; border-radius: 4px; font-weight: bold;">${sq.year}년 ${sq.half || ''}</span>
            <span style="background: ${sq.similarity >= 70 ? '#dcfce7' : sq.similarity >= 50 ? '#fef3c7' : '#e0f2fe'}; color: ${sq.similarity >= 70 ? '#166534' : sq.similarity >= 50 ? '#92400e' : '#0369a1'}; padding: 2px 6px; border-radius: 4px; font-size: 8pt; margin-left: 4px;">${sq.similarity.toFixed(0)}% 유사</span>
            ${sq.char_limit ? `<span style="color: #6b7280; font-size: 8pt; margin-left: 4px;">${sq.char_limit}자</span>` : ''}
          </p>
          <p style="margin: 4px 0; font-size: 9pt; color: #374151;">${sq.question}</p>
          ${sq.matched_keywords.length > 0 ? `<p style="margin: 0; font-size: 7pt; color: #6b7280;">일치 키워드: ${sq.matched_keywords.map(kw => `<span style="background: #ecfdf5; color: #047857; padding: 1px 4px; border-radius: 8px; margin-right: 4px;">${kw}</span>`).join('')}</p>` : ''}
        </div>
        `).join('')}
      </div>
      ` : ''}

      <!-- 면접 상세 정보 -->
      ${interview_detail && (interview_detail.format_type || (interview_detail.stages && interview_detail.stages.length > 0) || (interview_detail.frequent_questions && interview_detail.frequent_questions.length > 0)) ? `
      <div class="pdf-no-break" style="background: #f0fdfa; border: 1px solid #99f6e4; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #0f766e; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #99f6e4;">
          🎯 면접 상세 정보
        </h2>

        <table style="width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 10px;">
          <tr>
            ${interview_detail.format_type ? `
            <td style="padding: 6px 10px; background: white; border-radius: 4px; margin: 2px;">
              <span style="font-size: 8pt; color: #0f766e; font-weight: bold; display: block;">면접 형식</span>
              <span style="color: #134e4a;">${interview_detail.format_type}</span>
            </td>
            ` : ''}
            ${interview_detail.duration ? `
            <td style="padding: 6px 10px; background: white; border-radius: 4px; margin: 2px;">
              <span style="font-size: 8pt; color: #0f766e; font-weight: bold; display: block;">면접 시간</span>
              <span style="color: #134e4a;">${interview_detail.duration}</span>
            </td>
            ` : ''}
            ${interview_detail.difficulty ? `
            <td style="padding: 6px 10px; background: white; border-radius: 4px; margin: 2px;">
              <span style="font-size: 8pt; color: #0f766e; font-weight: bold; display: block;">난이도</span>
              <span style="color: ${interview_detail.difficulty.includes('상') || interview_detail.difficulty.includes('높') ? '#dc2626' : '#134e4a'};">${interview_detail.difficulty}</span>
            </td>
            ` : ''}
            ${interview_detail.pass_rate ? `
            <td style="padding: 6px 10px; background: white; border-radius: 4px; margin: 2px;">
              <span style="font-size: 8pt; color: #0f766e; font-weight: bold; display: block;">합격률</span>
              <span style="color: #134e4a;">${interview_detail.pass_rate}</span>
            </td>
            ` : ''}
          </tr>
        </table>

        ${interview_detail.stages && interview_detail.stages.length > 0 ? `
        <div style="background: white; padding: 8px 10px; border-radius: 6px; margin-bottom: 10px;">
          <span style="font-size: 8pt; color: #0f766e; font-weight: bold; display: block; margin-bottom: 4px;">전형 단계</span>
          <p style="margin: 0; font-size: 9pt;">
            ${interview_detail.stages.map((stage, i) => `<span style="display: inline-block; background: #ccfbf1; color: #0f766e; padding: 2px 8px; border-radius: 12px; margin: 2px;">${i + 1}. ${stage}</span>`).join(' ')}
          </p>
        </div>
        ` : ''}

        ${interview_detail.frequent_questions && interview_detail.frequent_questions.length > 0 ? `
        <div style="background: white; padding: 10px; border-radius: 6px;">
          <p style="margin: 0 0 8px 0; font-size: 9pt; font-weight: bold; color: #0f766e;">⭐ 고빈도 면접 질문 TOP ${interview_detail.frequent_questions.length}</p>
          ${interview_detail.frequent_questions.map((q, idx) => `
          <div style="background: #f0fdfa; padding: 8px; margin-bottom: ${idx < interview_detail.frequent_questions!.length - 1 ? '6px' : '0'}; border-radius: 4px; border-left: 2px solid #14b8a6;">
            <p style="margin: 0 0 4px 0; font-size: 9pt;">
              <span style="display: inline-block; width: 18px; height: 18px; background: #14b8a6; color: white; text-align: center; line-height: 18px; border-radius: 50%; font-size: 8pt; margin-right: 6px;">${idx + 1}</span>
              <span style="font-weight: 500; color: #134e4a;">${q.question}</span>
              <span style="background: ${q.frequency === 'high' ? '#fef3c7' : '#e0f2fe'}; color: ${q.frequency === 'high' ? '#92400e' : '#0369a1'}; font-size: 7pt; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">${q.frequency === 'high' ? '매우 빈출' : '빈출'}</span>
            </p>
            <p style="margin: 0; font-size: 8pt; padding-left: 24px;">
              <span style="color: #0f766e; font-weight: 500;">[${q.category}]</span>
              ${q.tips ? `<span style="color: #475569; margin-left: 6px;">💡 ${q.tips}</span>` : ''}
            </p>
          </div>
          `).join('')}
        </div>
        ` : ''}
      </div>
      ` : ''}

      <!-- 예상 면접 질문 -->
      ${interview_questions.length > 0 ? `
      <div style="background: white; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
        <h2 style="font-size: 12pt; color: #1e293b; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
          🎤 예상 면접 질문 & 답변 예시
        </h2>
        ${interview_questions.map((item, idx) => `
        <div class="pdf-no-break" style="background: #f8fafc; padding: 10px; margin-bottom: ${idx < interview_questions.length - 1 ? '8px' : '0'}; border-radius: 6px; border: 1px solid #e2e8f0;">
          <p style="margin: 0 0 6px 0; font-size: 10pt;">
            <span style="font-weight: bold; color: #3b82f6;">Q${idx + 1}.</span>
            <span style="color: #1e293b;">${item.question}</span>
            ${item.is_frequent ? `<span style="background: #fef3c7; color: #92400e; font-size: 8pt; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">${item.years && item.years.length > 0 ? `${item.years.join(', ')}년 기출` : '기출'} ⭐</span>` : `<span style="background: #dbeafe; color: #1e40af; font-size: 8pt; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">출제 예상 🎯</span>`}
          </p>
          <div style="background: #eff6ff; padding: 6px 8px; border-radius: 4px; font-size: 9pt; color: #1e40af; margin-bottom: 6px;">
            💡 <strong>답변 포인트:</strong> ${item.answer_tips}
          </div>
          ${item.sample_answer ? `
          <div style="background: #f0f9ff; padding: 8px; border-radius: 4px; border-left: 3px solid #0ea5e9;">
            <p style="margin: 0 0 4px 0; font-size: 8pt; font-weight: 600; color: #0369a1;">📝 예시 답변 (자소서 기반):</p>
            <p style="margin: 0; font-size: 9pt; color: #1e3a5f; line-height: 1.5;">${item.sample_answer}</p>
          </div>
          ` : ''}
        </div>
        `).join('')}
      </div>
      ` : ''}

      <!-- 모범 답안 -->
      ${model_answer ? `
      <div class="pdf-page-break-before" style="background: #f0f9ff; border: 1px solid #bae6fd; padding: 12px; border-radius: 8px;">
        <h2 style="font-size: 12pt; color: #0369a1; margin: 0 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #bae6fd;">
          📝 모범 답안 (AI 추천)
          <span style="font-size: 8pt; font-weight: normal; color: #94a3b8; margin-left: 8px;">지원자가 제출한 자기소개서를 토대로 작성되었습니다</span>
        </h2>
        <div style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #bae6fd;">
          <p style="margin: 0; font-size: 10pt; color: #1e293b; line-height: 1.8; white-space: pre-wrap;">${model_answer}</p>
        </div>
        <p style="margin: 10px 0 0 0; font-size: 9pt; color: #64748b; text-align: right;">
          📊 글자 수: ${model_answer_length}자 / ${length_check.max}자 (${((model_answer_length / length_check.max) * 100).toFixed(1)}%)
        </p>
      </div>
      ` : ''}

    </div>
  `;
}

function getGradeEmoji(grade: string): string {
  switch (grade) {
    case '우수': return '🌟';
    case '양호': return '👍';
    case '보통': return '📝';
    case '미흡': return '⚠️';
    default: return '📊';
  }
}

function getWarningIcon(type: string): string {
  switch (type) {
    case 'blind_violation': return '🚫';
    case 'abstract_expression': return '💭';
    case 'no_result': return '📊';
    case 'wrong_organization': return '🏢';
    default: return '⚠️';
  }
}

/**
 * 기존 방식 (fallback) - analysisResult가 없을 때 사용
 */
async function exportToPdfLegacy(
  element: HTMLElement,
  options: PdfExportOptions
): Promise<void> {
  const { filename = '자기소개서_분석결과', title = '자기소개서 AI 분석 결과' } = options;

  const pdfContent = document.createElement('div');
  pdfContent.innerHTML = `
    <div style="font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; padding: 15px; color: #333;">
      <div style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #3b82f6;">
        <h1 style="font-size: 20px; color: #1e293b; margin: 0 0 6px 0;">${title}</h1>
        <p style="font-size: 11px; color: #64748b; margin: 0;">생성일: ${new Date().toLocaleDateString('ko-KR')}</p>
      </div>
      ${element.innerHTML}
    </div>
  `;

  // Remove buttons
  const buttonsToRemove = pdfContent.querySelectorAll('button, .pdf-save-container, .scroll-top-btn');
  buttonsToRemove.forEach((btn) => btn.remove());

  const opt = {
    margin: [10, 10, 10, 10] as [number, number, number, number],
    filename: `${filename}.pdf`,
    image: { type: 'jpeg' as const, quality: 0.95 },
    html2canvas: {
      scale: 2,
      useCORS: true,
    },
    jsPDF: {
      unit: 'mm' as const,
      format: 'a4' as const,
      orientation: 'portrait' as const,
    },
  };

  await html2pdf().set(opt).from(pdfContent).save();
}
