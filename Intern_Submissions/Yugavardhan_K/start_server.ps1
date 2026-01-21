# Start the Django development server
# This script starts the server from the correct directory

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Audio Pipeline Server Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$pythonExe = Join-Path $projectRoot "venv_wx\Scripts\python.exe"

Write-Host "Starting Django development server..." -ForegroundColor Yellow
Write-Host "Server will be available at: http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

Push-Location $backendDir
& $pythonExe manage.py runserver --noreload

Pop-Location
