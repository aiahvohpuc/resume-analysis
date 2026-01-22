#!/bin/bash
# TDD Watch Script - 파일 변경 시 자동 테스트 실행

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# 가상환경 활성화
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🧪 TDD Watch Mode Started"
echo "📁 Watching: src/ and test/"
echo "Press Ctrl+C to stop"
echo "---"

# pytest-watch 사용 (설치된 경우)
if command -v ptw &> /dev/null; then
    ptw --runner "pytest --tb=short -q"
# entr 사용 (fallback)
elif command -v entr &> /dev/null; then
    find src test -name "*.py" | entr -c pytest --tb=short -q
else
    echo "❌ pytest-watch 또는 entr가 필요합니다."
    echo "   pip install pytest-watch"
    echo "   또는"
    echo "   sudo apt install entr"
    exit 1
fi
