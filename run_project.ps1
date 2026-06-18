# OptiGene Web App Startup Script
# This script launches the FastAPI backend and Next.js frontend in separate terminal windows.

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      Starting OptiGene Web Servers      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Start backend FastAPI server
Write-Host "Starting OptiGene Backend Server (FastAPI on port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'OptiGene FastAPI Server' -ForegroundColor Cyan; conda run -n spark312 uvicorn backend.app:app --host 127.0.0.1 --port 5000 --reload"

# 2. Start frontend Next.js server
Write-Host "Starting OptiGene Frontend Server (Next.js on port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'OptiGene Next.js Frontend' -ForegroundColor Cyan; Set-Location frontend; npm run dev"

Write-Host ""
Write-Host "Both servers are starting up in separate terminal windows!" -ForegroundColor Green
Write-Host "Access the Web Frontend at: http://localhost:3000" -ForegroundColor Green
Write-Host "Access the Backend API at:  http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
