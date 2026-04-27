@echo off
REM FastAPI Quick Start Batch Script
REM This script will install dependencies and start the server

cd /d "C:\Users\zhangmohan\Desktop\信息系统"

echo.
echo ============================================================
echo FastAPI Server Quick Start
echo ============================================================
echo.

REM Check if python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not in PATH
    echo Please add Python to your PATH and try again
    pause
    exit /b 1
)

echo Step 1: Installing dependencies...
python -m pip install -q fastapi uvicorn sqlalchemy >nul 2>&1
if errorlevel 1 (
    echo WARNING: pip install failed, but continuing anyway
)

echo Step 2: Verifying backend module...
python -c "import backend.main" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot import backend.main
    echo Trying to install requirements.txt...
    python -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo FAILED to install requirements
        pause
        exit /b 1
    )
)

echo Step 3: Starting FastAPI server...
echo.
echo Access the API at: http://127.0.0.1:8000/docs
echo Swagger UI at:     http://127.0.0.1:8000/swagger-ui
echo OpenAPI schema:    http://127.0.0.1:8000/openapi.json
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
