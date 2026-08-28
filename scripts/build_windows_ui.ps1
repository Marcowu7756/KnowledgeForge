# Build optional/legacy portable Web UI shell (PyInstaller).
# Preferred launch: .\.venv\Scripts\python.exe main.py ui  (browser-first)
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_ui.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
  Write-Error "Missing venv python: $Py"
}

Write-Host "[build] ensure pyinstaller"
& $Py -m pip install "pyinstaller>=6.3"
if ($LASTEXITCODE -ne 0) {
  Write-Error "pip install pyinstaller failed"
}

$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
New-Item -ItemType Directory -Force -Path $Build | Out-Null

$Spec = Join-Path $Root "packaging\knowledgeforge_ui.spec"
Write-Host "[build] pyinstaller onedir"
& $Py -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Build $Spec
if ($LASTEXITCODE -ne 0) {
  Write-Error "PyInstaller failed"
}

$Out = Join-Path $Dist "KnowledgeForgeUI"
$Readme = Join-Path $Out "README_UI.txt"
@(
  "KnowledgeForge Web UI (portable shell · legacy)",
  "",
  "Prefer: .\.venv\Scripts\python.exe main.py ui  (browser-first)",
  "",
  "1. Set KF_ROOT to your full KnowledgeForge repo so models/data resolve:",
  "   setx KF_ROOT `"D:\KnowledgeForge`"",
  "",
  "2. Or place models\ and data\ next to KnowledgeForgeUI.exe",
  "",
  "3. Run: KnowledgeForgeUI.exe",
  "   Browser opens http://127.0.0.1:8765",
  "",
  "Note: This build excludes heavy ML runtimes (torch/paddle/whisper).",
  "For full Capture/Compile/Retrieve/Compose, run from the repo:",
  "   .\.venv\Scripts\python.exe main.py ui"
) | Set-Content -Encoding UTF8 $Readme

Write-Host "[ok] output: $Out"
Write-Host "[ok] run:    $(Join-Path $Out 'KnowledgeForgeUI.exe')"
