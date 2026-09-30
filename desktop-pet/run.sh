#!/usr/bin/env bash

# 스크립트 위치로 이동
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "===================================================="
echo "       🐾 Desktop Pet (Shimeji) 시작 중...        "
echo "===================================================="

# 실행 가능한 정상 Python 3 바이너리 탐색 (권한 오류가 있는 Anaconda 등 자동 회피)
find_working_python() {
    for py in \
        "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3" \
        "/usr/local/bin/python3" \
        "/usr/bin/python3" \
        "$(which python3 2>/dev/null)" \
        "$(which python 2>/dev/null)"; do
        if [ -n "$py" ] && [ -x "$py" ]; then
            if "$py" -c "exit(0)" 2>/dev/null; then
                echo "$py"
                return 0
            fi
        fi
    done
    return 1
}

PY=$(find_working_python)
if [ -z "$PY" ]; then
    echo "[ERROR] 정상 작동하는 Python 3 실행 파일을 찾을 수 없습니다."
    exit 1
fi

echo "[INFO] 선택된 Python: $PY"

# 가상환경 확인 및 생성 시도 (실패해도 중단 없이 계속 진행)
if [ ! -d ".venv" ]; then
    echo "[INFO] 가상환경(.venv) 생성을 시도합니다..."
    "$PY" -m venv --system-site-packages .venv 2>/dev/null || true
fi

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate 2>/dev/null || true
    echo "[INFO] 가상환경 활성화 완료. 패키지 설치 확인 중..."
    pip install --timeout 3 --retries 0 -r requirements.txt 2>/dev/null || echo "[INFO] pip 네트워크 설치를 건너뛰고 내장 엔진으로 즉시 실행합니다."
    if command -v python &>/dev/null; then
        python pet.py
    else
        "$PY" pet.py
    fi
else
    echo "[INFO] 내장 Python 엔진으로 데스크톱 펫을 즉시 실행합니다..."
    "$PY" pet.py
fi
