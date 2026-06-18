@echo off
title OptiGene Launcher
echo =========================================
echo       Starting OptiGene Web Servers      
echo =========================================

echo Starting OptiGene Backend Server (FastAPI on port 5000)...
start cmd /k "title OptiGene Backend (FastAPI) && conda run -n spark312 uvicorn backend.app:app --host 127.0.0.1 --port 5000 --reload"

echo Starting OptiGene Frontend Server (Next.js on port 3000)...
start cmd /k "title OptiGene Frontend (Next.js) && cd frontend && npm run dev"

echo.
echo Both servers are starting up in separate command prompt windows!
echo Access the Web Frontend at: http://localhost:3000
echo Access the Backend API at:  http://127.0.0.1:5000
echo =========================================
pause
