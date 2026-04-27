@echo off
setlocal enabledelayedexpansion

set "ENV_NAME=shironosuke-pet-hospital"
set "ENV_FILE=%~dp0environment.yml"

where conda >nul 2>nul
if %errorlevel% neq 0 (
  if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
    set "CONDA=%USERPROFILE%\miniconda3\Scripts\conda.exe"
  ) else if exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" (
    set "CONDA=%USERPROFILE%\Miniconda3\Scripts\conda.exe"
  ) else (
    echo 未找到conda，请先安装Miniconda/Anaconda。
    exit /b 1
  )
) else (
  set "CONDA=conda"
)

%CONDA% env list | findstr /B /C:"%ENV_NAME% " >nul
if errorlevel 1 (
  set "HTTP_PROXY="
  set "HTTPS_PROXY="
  set "ALL_PROXY="
  set "http_proxy="
  set "https_proxy="
  set "all_proxy="
  %CONDA% config --remove-key proxy_servers >nul 2>nul
  %CONDA% env create -f "%ENV_FILE%" -n "%ENV_NAME%"
  if errorlevel 1 exit /b 1
)

%CONDA% run -n "%ENV_NAME%" python -m uvicorn backend.main:app --reload --port 8000

endlocal

