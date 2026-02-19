# Startup script for CamExtractor Web UI (Local Mode)

Write-Host "Starting CamExtractor Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command .\venv\Scripts\python.exe app.py"

Write-Host "Starting CamExtractor Frontend..." -ForegroundColor Cyan
Set-Location frontend
npm run dev
