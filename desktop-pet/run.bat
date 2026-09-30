@echo off
chcp 65001 > nul
title Desktop Pet (Shimeji)

echo ====================================================
echo        🐾 Desktop Pet (Shimeji) 시작 중...        
echo ====================================================

:: Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되어 있지 않거나 환경변수 PATH에 등록되지 않았습니다.
    echo https://www.python.org 에서 Python을 설치 후 다시 시도해 주세요.
    pause
    exit /b 1
)

:: 가상환경 확인 및 생성
if not exist ".venv" (
    echo [INFO] 최초 실행을 위한 Python 가상환경(.venv)을 생성합니다...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [INFO] 필수 패키지(PyQt6, Pillow)를 설치합니다...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: 실행
echo [INFO] 데스크톱 펫을 화면에 띄웁니다!
python pet.py

if errorlevel 1 (
    echo [ERROR] 실행 중 오류가 발생했습니다.
    pause
)
