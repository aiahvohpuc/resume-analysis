import { useState, useEffect, useRef } from 'react';
import type { ResumeAnalysisRequest } from '../types/api';
import { api } from '../services/api';
import './ResumeForm.css';

interface ResumeFormProps {
  onSubmit: (request: ResumeAnalysisRequest) => void;
  isLoading: boolean;
}

interface OrganizationData {
  code: string;
  name: string;
  positions: string[];
}

// 기관 카테고리 정의
const ORGANIZATION_CATEGORIES: Record<string, string[]> = {
  '복지/의료': ['NHIS', 'NPS', 'HIRA'],
  '금융': ['IBK', 'KDB', 'KEXIM', 'HF', 'KIBO', 'KODIT', 'KDIC', 'KAMCO', 'KIC', 'KSURE', 'KINFA'],
  '에너지/발전': ['KEPCO', 'KHNP', 'KOGAS', 'KNOC', 'KEA', 'KDHC', 'KDN', 'KGS', 'KPS', 'KNF', 'KOGAS_TECH', 'GENCO'],
  'SOC/교통/환경': ['EX', 'KORAIL', 'KWATER', 'LH', 'IIAC', 'KECO', 'HUG', 'SMRT', 'KOROAD', 'LX', 'SR', 'HUMETRO', 'KRNA', 'ICTR', 'SISUL'],
  '산업진흥/기타': ['HRDK', 'KEIS', 'KOSAF', 'SEMAS', 'KOSMES', 'KISED', 'KTO', 'KOSHA', 'KSPO', 'KRC', 'AT', 'KOMSCO'],
};

// 기관 코드로 카테고리 찾기
function getCategoryByCode(code: string): string {
  for (const [category, codes] of Object.entries(ORGANIZATION_CATEGORIES)) {
    if (codes.includes(code)) return category;
  }
  return '기타';
}

export function ResumeForm({ onSubmit, isLoading }: ResumeFormProps) {
  const [organizations, setOrganizations] = useState<OrganizationData[]>([]);
  const [orgLoading, setOrgLoading] = useState<boolean>(true);
  const [orgError, setOrgError] = useState<string>('');
  const [selectedOrg, setSelectedOrg] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('전체');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [position, setPosition] = useState<string>('');
  const [answer, setAnswer] = useState<string>('');
  const [maxLength] = useState<number>(2500);
  const [pdfUploading, setPdfUploading] = useState<boolean>(false);
  const [pdfError, setPdfError] = useState<string>('');
  const [truncatedWarning, setTruncatedWarning] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentOrg = organizations.find(org => org.code === selectedOrg);
  const currentLength = answer.length;
  const lengthPercentage = maxLength > 0 ? (currentLength / maxLength) * 100 : 0;

  // 텍스트가 있으면 PDF 업로드 비활성화
  const hasText = answer.trim().length > 0;

  // 카테고리 목록
  const categories = ['전체', ...Object.keys(ORGANIZATION_CATEGORIES)];

  // 카테고리 및 검색어로 필터링된 기관 목록
  const filteredOrganizations = organizations.filter(org => {
    const matchesCategory = selectedCategory === '전체' || getCategoryByCode(org.code) === selectedCategory;
    const matchesSearch = searchQuery === '' || org.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // 기관 목록 로드
  useEffect(() => {
    const loadOrganizations = async () => {
      setOrgLoading(true);
      setOrgError('');

      try {
        const orgCodes = await api.getOrganizations();
        const orgDataPromises = orgCodes.map(async (code) => {
          try {
            const details = await api.getOrganization(code);
            return {
              code,
              name: (details.name as string) || code,
              positions: (details.positions as string[]) || ['행정직'],
            };
          } catch {
            return { code, name: code, positions: ['행정직'] };
          }
        });

        const orgData = await Promise.all(orgDataPromises);
        setOrganizations(orgData);
        // 기관 자동 선택 제거 - 사용자가 직접 선택하도록 함
      } catch (err) {
        console.error('Failed to load organizations:', err);
        setOrgError('기관 목록을 불러오는데 실패했습니다.');
      } finally {
        setOrgLoading(false);
      }
    };

    loadOrganizations();
  }, []);

  // 기관 변경 시 직렬 초기화
  useEffect(() => {
    // 기관이 변경되면 직렬 선택 초기화 (사용자가 직접 선택하도록)
    setPosition('');
  }, [selectedOrg]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;

    onSubmit({
      organization: selectedOrg,
      position,
      answer,
      maxLength,
    });
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length > maxLength) {
      setAnswer(value.slice(0, maxLength));
      setTruncatedWarning(true);
    } else {
      setAnswer(value);
      setTruncatedWarning(false);
    }
  };

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setPdfError('PDF 파일만 업로드 가능합니다.');
      return;
    }

    setPdfUploading(true);
    setPdfError('');

    try {
      const result = await api.uploadPdf(file);
      if (result.text.length > maxLength) {
        setAnswer(result.text.slice(0, maxLength));
        setTruncatedWarning(true);
      } else {
        setAnswer(result.text);
        setTruncatedWarning(false);
      }
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : 'PDF 업로드에 실패했습니다.');
    } finally {
      setPdfUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleClear = () => {
    setAnswer('');
    setPdfError('');
    setTruncatedWarning(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getLengthStatus = () => {
    if (lengthPercentage > 100) return 'over';
    if (lengthPercentage >= 70) return 'optimal';
    return 'short';
  };

  const lengthStatus = getLengthStatus();

  return (
    <form className="resume-form" onSubmit={handleSubmit}>
      {/* 기관, 직렬 선택 영역 */}
      <div className="form-section">
        <h3 className="section-title">
          지원 정보
          {!orgLoading && organizations.length > 0 && (
            <span className="org-count">{organizations.length}개 기관</span>
          )}
        </h3>

        {orgError && <div className="org-error">{orgError}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="category">분야</label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                // 카테고리 변경 시 검색어/기관/직렬 선택 초기화
                setSearchQuery('');
                setSelectedOrg('');
                setPosition('');
              }}
              disabled={isLoading || pdfUploading || orgLoading}
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="organization">기관</label>
            <div className="org-search-wrapper">
              <input
                type="text"
                className="org-search-input"
                placeholder="🔍 기관명 검색..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  // 검색 시 기관 선택 초기화
                  if (selectedOrg) {
                    setSelectedOrg('');
                    setPosition('');
                  }
                }}
                disabled={isLoading || pdfUploading || orgLoading}
              />
              <select
                id="organization"
                value={selectedOrg}
                onChange={(e) => setSelectedOrg(e.target.value)}
                disabled={isLoading || pdfUploading || orgLoading}
              >
                {orgLoading ? (
                  <option>로딩 중...</option>
                ) : (
                  <>
                    <option value="">
                      {filteredOrganizations.length === 0
                        ? '검색 결과 없음'
                        : `기관 선택 (${filteredOrganizations.length}개)`}
                    </option>
                    {filteredOrganizations.map((org) => (
                      <option key={org.code} value={org.code}>
                        {org.name}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="position">직렬</label>
            <select
              id="position"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              disabled={isLoading || pdfUploading || orgLoading || !selectedOrg}
            >
              {!selectedOrg ? (
                <option value="">기관을 먼저 선택하세요</option>
              ) : (
                <>
                  <option value="">직렬을 선택하세요</option>
                  {currentOrg?.positions.map((pos) => (
                    <option key={pos} value={pos}>
                      {pos}
                    </option>
                  ))}
                </>
              )}
            </select>
          </div>
        </div>
      </div>

      {/* 자기소개서 입력 영역 */}
      <div className="form-section">
        <h3 className="section-title">
          자기소개서
          <div className="input-controls">
            {hasText && (
              <button
                type="button"
                className="clear-btn"
                onClick={handleClear}
                disabled={isLoading || pdfUploading}
              >
                초기화
              </button>
            )}
            <span className="pdf-upload-wrapper">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handlePdfUpload}
                disabled={isLoading || pdfUploading || hasText}
                className="pdf-input"
                id="pdf-upload"
              />
              <label
                htmlFor="pdf-upload"
                className={`pdf-upload-btn ${hasText ? 'disabled' : ''}`}
              >
                {pdfUploading ? 'PDF 처리중...' : 'PDF 업로드'}
              </label>
            </span>
          </div>
        </h3>

        {pdfError && <div className="pdf-error">{pdfError}</div>}
        {truncatedWarning && (
          <div className="truncated-warning">
            글자수가 {maxLength}자를 초과하였습니다.
          </div>
        )}

        <div className="form-group">
          <textarea
            id="answer"
            value={answer}
            onChange={handleTextChange}
            placeholder="자기소개서 내용을 직접 입력하거나 PDF 파일을 업로드하세요..."
            rows={10}
            disabled={isLoading || pdfUploading}
          />
          <div className={`length-counter ${lengthStatus}`}>
            현재 글자수: {currentLength}/{maxLength}
            <span className="length-bar">
              <span
                className="length-fill"
                style={{ width: `${Math.min(lengthPercentage, 100)}%` }}
              />
            </span>
          </div>
        </div>
      </div>

      {/* 분석하기 버튼 */}
      <button
        type="submit"
        className="submit-button"
        disabled={isLoading || pdfUploading || !answer.trim() || !selectedOrg || !position}
      >
        {isLoading ? '분석 중...' : '분석하기'}
      </button>
    </form>
  );
}
