@echo off
REM === FastAPI One-Click Startup ===
REM This is the fastest way to get your FastAPI server running

setlocal enabledelayedexpansion
cd /d "C:\Users\zhangmohan\Desktop\信息系统"

echo.
echo ================================================================
echo FastAPI Server - One-Click Startup
echo ================================================================
echo.
echo Checking Python...
python --version

echo.
echo Installing/Verifying dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -q fastapi uvicorn sqlalchemy python-jose passlib apscheduler networkx chromadb httpx python-multipart

echo Done!
echo.
echo ================================================================
echo Starting FastAPI Server
echo ================================================================
echo.
echo Server Address: http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

endlocal
pause
