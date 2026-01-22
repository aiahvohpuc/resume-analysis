# Resume Analysis

이력서 분석 프로젝트

## Project Structure

```
resume-analysis/
├── src/            # 소스 코드
├── scripts/        # TDD watch, 백업, 자동화 스크립트
├── config/         # 환경 및 앱 설정
├── test/           # 테스트 (Unit, Integration, E2E)
├── logs/           # 심볼릭 링크 -> /data/logs/resume-analysis/
└── README.md       # 프로젝트 개요
```

## Development

### TDD Workflow
이 프로젝트는 TDD(Test-Driven Development) 방식을 따릅니다:

1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 테스트 통과를 위한 최소 코드 구현
3. **REFACTOR**: 코드 정리 및 SAST 스캔

### Commands
```bash
npm run dev      # 개발 서버 실행
npm test         # 테스트 실행
npm run lint     # 코드 품질 검사
```

## Storage Policy
- 소스 코드: `~/ai_project/` (NVMeSSD)
- 로그: `/data/logs/resume-analysis/`

---
*초기화: 2026-01-20*
