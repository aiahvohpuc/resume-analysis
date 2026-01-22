# CLAUDE.md (Project: Resume Analysis)

이 파일은 `resume-analysis` 프로젝트에 특화된 Claude Code 지침입니다.
전역 인프라 규칙은 `~/ai_project/CLAUDE.md`를 상속합니다.

## 📋 Project Overview

- **목적**: 공기업 자기소개서 AI 분석 서비스
- **기술 스택**:
  - Backend: Python 3.12+ (FastAPI)
  - Frontend: React + Vite + TypeScript
  - LLM: OpenAI GPT-4o-mini
- **주요 기능**:
  - PDF 문서 파싱 및 텍스트 추출
  - 이력서 섹션 자동 분류 (경력, 학력, 기술 등)
  - 키워드 추출 및 스킬 매칭 분석
  - AI 기반 자기소개서 피드백 생성

## 🚀 Quick Start (Development)

### 통합 개발 서버 실행
```bash
# 백엔드 + 프론트엔드 동시 실행
./scripts/dev.sh

# 또는 개별 실행:
# Terminal 1 - Backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 서버 접속 URL
| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://192.168.0.8:3003 | React 개발 서버 |
| Backend API | http://192.168.0.8:8001 | FastAPI 서버 |
| API Docs | http://192.168.0.8:8001/docs | Swagger UI |

## 🔧 Development Environment

### Backend (Python)
```bash
# 가상환경 생성 (최초 1회)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### Frontend (Node.js)
```bash
# nvm 로드 (최초 세션)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 의존성 설치
cd frontend
npm install
```

### 환경 변수 설정
```bash
# .env 파일 생성 (루트 디렉토리)
cp .env.example .env

# OpenAI API 키 설정 필수!
# OPENAI_API_KEY=your-actual-api-key
```

## 📦 Core Dependencies

### Backend
| Package | Purpose |
|---------|---------|
| `fastapi` | 웹 API 프레임워크 |
| `openai` | GPT API 클라이언트 |
| `pdfplumber` | PDF 텍스트 추출 |
| `pydantic` | 데이터 검증 |
| `pytest` | 테스트 프레임워크 |
| `ruff` | 린팅 및 포맷팅 |
| `bandit` | SAST 보안 스캔 |

### Frontend
| Package | Purpose |
|---------|---------|
| `react` | UI 라이브러리 |
| `vite` | 빌드 도구 |
| `typescript` | 타입 시스템 |

## ⌨️ Commands

### Development
```bash
# 통합 개발 서버
./scripts/dev.sh

# Backend만 실행
source venv/bin/activate && uvicorn src.main:app --reload

# Frontend만 실행
cd frontend && npm run dev
```

### Testing (TDD)
```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src --cov-report=term-missing

# 특정 테스트 파일 실행
pytest test/test_parser.py -v
```

### Code Quality
```bash
# 린팅
ruff check src/ test/

# 자동 수정
ruff check --fix src/ test/

# SAST 보안 스캔
bandit -r src/
```

### Build & Deploy
```bash
# Frontend 빌드
cd frontend && npm run build

# Docker 이미지 빌드
docker build -t resume-analysis:latest .
```

## 📁 Project Structure

```
resume-analysis/
├── src/                        # Backend (Python)
│   ├── api/                    # API 라우트
│   │   ├── routes.py           # 메인 API 엔드포인트
│   │   └── analyzer_routes.py  # 분석기 API 엔드포인트
│   ├── analyzer/               # 분석 로직
│   │   ├── section_classifier.py
│   │   └── skill_extractor.py
│   ├── parser/                 # PDF/텍스트 파싱
│   │   ├── pdf_parser.py
│   │   └── text_parser.py
│   ├── models/                 # 데이터 모델
│   │   └── resume.py
│   ├── schemas/                # Pydantic 스키마
│   │   ├── request.py
│   │   ├── response.py
│   │   └── analyzer.py
│   ├── services/               # 비즈니스 로직
│   │   ├── openai_client.py
│   │   ├── llm_service.py
│   │   └── feedback_analyzer.py
│   ├── core/                   # 설정 및 프롬프트
│   │   ├── config.py
│   │   └── prompts.py
│   └── main.py                 # FastAPI 앱
├── frontend/                   # Frontend (React)
│   ├── src/
│   │   ├── components/         # UI 컴포넌트
│   │   │   ├── ResumeForm.tsx
│   │   │   └── AnalysisDashboard.tsx
│   │   ├── services/           # API 클라이언트
│   │   │   └── api.ts
│   │   ├── types/              # TypeScript 타입
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── vite.config.ts
│   └── package.json
├── test/                       # 테스트 코드
├── scripts/
│   ├── dev.sh                  # 개발 서버 실행
│   └── tdd-watch.sh
├── .env                        # 환경 변수 (gitignore)
├── .env.example                # 환경 변수 템플릿
├── requirements.txt
└── CLAUDE.md
```

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/feedback/resume` | AI 기반 자소서 분석 |
| POST | `/api/analyze/skills` | 스킬 추출 및 매칭 |
| POST | `/api/analyze/sections` | 섹션 자동 분류 |
| POST | `/api/analyze/resume` | 통합 이력서 파싱 |
| GET | `/api/organizations` | 기관 목록 |
| GET | `/api/organizations/{code}` | 기관 상세 |
| GET | `/health` | 헬스체크 |

## 🧪 TDD Protocol

이 프로젝트는 **Red-Green-Refactor** 사이클을 엄격히 준수합니다.

### TDD 사이클
```
🔴 RED    → pytest test/test_*.py (FAIL 확인)
🟢 GREEN  → src/ 에 최소 구현
🔵 REFACTOR → ruff + bandit 실행 후 코드 개선
```

### Quality Gates (현재 상태 ✅)
- [x] `pytest --cov=src` → 커버리지 97% (목표 80%)
- [x] `ruff check src/` → 린트 오류 0개
- [x] `bandit -r src/` → High severity 0개
- [x] 총 115개 테스트 통과

## 🎯 Implementation Status

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| Phase 1 | Foundation (Models, Parsers) | ✅ Complete | 74 |
| Phase 2 | Analyzer (Section, Skill) | ✅ Complete | 101 |
| Phase 3 | API Integration | ✅ Complete | 115 |
| Phase 4 | UI & LLM Integration | ✅ Complete | - |

## 🔒 Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...        # OpenAI API 키

# Optional (defaults provided)
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
APP_ENV=development
DEBUG=true
CORS_ORIGINS=http://localhost:3003
```

## 🚢 Production Deployment

### NPM (Nginx Proxy Manager) 설정
- Domain: `resume.vibelogic.net`
- Backend: `http://192.168.0.8:8001`
- Frontend: `http://192.168.0.8:3003` (또는 static build)

### Docker Compose
```yaml
services:
  backend:
    build: .
    ports:
      - "8001:8001"
    env_file: .env

  frontend:
    build: ./frontend
    ports:
      - "3003:80"
```

## 📜 Inherited Global Rules

다음 규칙은 `~/ai_project/CLAUDE.md`에서 상속됩니다:
- **Storage Policy**: 소스코드 `/mnt/fast`, 로그 `/data/logs/`
- **Docker Data Root**: `/mnt/fast/docker-data`
- **Session Management**: `tmux` 세션 내 작업 권장
- **TDD Knowledge Base**: `TDD/docs/SKILL.md` 참조

## 🔗 Related Resources

- **Implementation Plan**: `~/ai_project/TDD/docs/plans/resume-analysis/implementation-plan.md`
- **Global CLAUDE.md**: `~/ai_project/CLAUDE.md`
- **TDD Skill Guide**: `~/ai_project/TDD/docs/SKILL.md`
- **기획안**: 이 프로젝트의 전체 기획은 대화 히스토리 참조

---
*Created: 2026-01-20*
*Phase 4 Updated: 2026-01-20*
