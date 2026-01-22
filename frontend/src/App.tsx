import { useState, useRef } from 'react';
import { ResumeForm } from './components/ResumeForm';
import { AnalysisDashboard, type AnalysisDashboardHandle } from './components/AnalysisDashboard';
import { api, ApiError } from './services/api';
import type { ResumeAnalysisRequest, NewResumeAnalysisResponse } from './types/api';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<NewResumeAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const dashboardRef = useRef<AnalysisDashboardHandle>(null);

  const handleSubmit = async (request: ResumeAnalysisRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.analyzeResumeV2(request);
      setResult(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`분석 실패 (${err.status}): ${err.message}`);
      } else {
        setError('서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.');
      }
      console.error('Analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📝 자기소개서 AI 분석</h1>
        <p>공기업 자기소개서를 AI가 분석하여 맞춤형 피드백을 제공합니다</p>
      </header>

      <main className="app-main">
        {!result ? (
          <section className="input-section">
            <ResumeForm onSubmit={handleSubmit} isLoading={isLoading} />
            {error && (
              <div className="error-message">
                <span>⚠️</span> {error}
              </div>
            )}
          </section>
        ) : (
          <section className="result-section">
            <div className="result-header">
              <h2>분석 결과</h2>
              <div className="header-buttons">
                <button className="header-btn" onClick={handleReset}>
                  새로운 분석하기
                </button>
                <button
                  className="header-btn pdf-btn"
                  onClick={() => dashboardRef.current?.savePdf()}
                >
                  PDF로 저장
                </button>
              </div>
            </div>
            <AnalysisDashboard ref={dashboardRef} result={result} />
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>© 2026 Resume Analysis - Powered by AI</p>
      </footer>
    </div>
  );
}

export default App;
