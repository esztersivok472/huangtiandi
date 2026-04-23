$ErrorActionPreference = 'Stop'

if (-not (Test-Path .venv)) {
  py -3 -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
if (Test-Path installer\output) { Remove-Item installer\output -Recurse -Force }

pyinstaller --noconfirm --windowed --name openclaw_demo main.py

New-Item -ItemType Directory -Path installer\payload -Force | Out-Null
Copy-Item dist\openclaw_demo.exe installer\payload\openclaw_demo.exe -Force
Copy-Item README.md installer\payload\README.txt -Force

Write-Host "Build finished."
Write-Host "Executable: dist\openclaw_demo.exe"

$iscc = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
if (Test-Path $iscc) {
  Write-Host "Found Inno Setup, creating installer..."
  Push-Location installer
  & $iscc openclaw_installer.iss
  Pop-Location
  Write-Host "Installer: installer\output\openclaw_demo_setup.exe"
} else {
  Write-Host "Inno Setup not found. Install and run:"
  Write-Host '"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\openclaw_installer.iss'
}
