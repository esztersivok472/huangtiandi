@echo off
setlocal enabledelayedexpansion

REM Build OpenClaw into a Windows executable and create installer payload.

if not exist .venv (
  py -3 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer\output rmdir /s /q installer\output

pyinstaller --noconfirm --windowed --name openclaw_demo main.py

mkdir installer\payload 2>nul
copy dist\openclaw_demo.exe installer\payload\openclaw_demo.exe >nul
copy README.md installer\payload\README.txt >nul

echo.
echo Build finished.
echo Executable: dist\openclaw_demo.exe

set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
  echo Found Inno Setup, creating installer...
  pushd installer
  "%ISCC%" openclaw_installer.iss
  popd
  echo Installer: installer\output\openclaw_demo_setup.exe
) else (
  echo Inno Setup not found. Install it and run:
  echo "%ISCC%" installer\openclaw_installer.iss
)
