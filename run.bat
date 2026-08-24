@echo off
setlocal DisableDelayedExpansion
title NEUROLEARN launcher
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] backend\.venv not found. Create it and install backend\requirements.txt first.
    pause
    exit /b 1
)

set "GEMINI_API_KEY="

rem ---- create .env from template on first run ----
if not exist ".env" (
    copy /y ".env.example" ".env" >nul
    echo [OK] no .env found - created one from .env.example
)

rem ---- load .env (skips # comments) ----
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"

rem ---- Gemini API key setup ----
if defined GEMINI_API_KEY if not "%GEMINI_API_KEY%"=="" (
    echo.
    echo Found an existing Gemini API key: %GEMINI_API_KEY:~0,6%...
    choice /c YN /n /m "Keep using it? [Y/N] "
    if errorlevel 2 goto ASKKEY
    goto KEYDONE
)

:ASKKEY
echo.
echo ============================================================
echo  Optional AI upgrade: a FREE Gemini API key unlocks
echo  LLM-powered simplification, tutoring and viva grading.
echo  Everything also works WITHOUT a key ^(heuristic mode^).
echo.
echo  How to get your free key:
echo    1. Open  https://aistudio.google.com/app/api-keys
echo    2. Sign in with your Google account
echo    3. Click "Create API key" and copy it
echo ============================================================
choice /c YN /n /m "Open that page in your browser now? [Y/N] "
if not errorlevel 2 start "" "https://aistudio.google.com/app/api-keys"

set "GEMINI_API_KEY="
set /p "GEMINI_API_KEY=Paste your Gemini API key (press Enter to skip): "
if defined GEMINI_API_KEY set "GEMINI_API_KEY=%GEMINI_API_KEY:"=%"

rem ---- persist: keep every line except GEMINI_API_KEY, append current value ----
if exist ".env" (
    (for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        if /i not "%%A"=="GEMINI_API_KEY" echo %%A=%%B
    )) > ".env.tmp"
) else (
    type nul > ".env.tmp"
)
if defined GEMINI_API_KEY >> ".env.tmp" echo GEMINI_API_KEY=%GEMINI_API_KEY%
move /y ".env.tmp" ".env" >nul
echo [OK] .env saved.

:KEYDONE
echo.
echo [1/3] seeding demo data (idempotent)...
backend\.venv\Scripts\python.exe backend\scripts\seed_demo.py

echo [2/3] starting API on http://127.0.0.1:8000 ...
start "NEUROLEARN API" cmd /k backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend

timeout /t 4 /nobreak >nul

echo [3/3] starting UI on http://localhost:5173 ...
start "NEUROLEARN UI" cmd /k npm run dev --prefix frontend

timeout /t 6 /nobreak >nul
start "" http://localhost:5173

echo.
echo Both servers run in their own windows - close them to stop.
echo Demo login: demo@neurolearn.app / demo12345
timeout /t 10 >nul
