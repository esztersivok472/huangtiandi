@echo off
setlocal

REM One-click setup for Windows users: install dependencies and run app.

where py >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] Python launcher 'py' not found.
  echo Please install Python 3.10+ from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating virtual environment...
  py -3 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Starting OpenClaw...
python main.py
