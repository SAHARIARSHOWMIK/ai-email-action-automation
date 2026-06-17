@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo AI Email-to-Action System - Windows setup
echo ==========================================
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3.12 --version >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PY=py -3.12"
        goto :found_python
    )
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY=python"
    goto :found_python
)

echo ERROR: Python was not found.
echo Install Python 3.12 from python.org and tick "Add Python to PATH".
pause
exit /b 1

:found_python
echo Using Python command: %PY%
%PY% -c "import sys; print('Python version:', sys.version); raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>nul
if not %ERRORLEVEL%==0 (
    echo.
    echo ERROR: This project is safest with Python 3.12 exactly.
    echo Please install Python 3.12, then run this file again.
    echo Python 3.13 may fail with the pinned PostgreSQL dependency.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    %PY% -m venv .venv
    if not %ERRORLEVEL%==0 goto :error
) else (
    echo Virtual environment already exists.
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if not %ERRORLEVEL%==0 goto :error

echo.
echo Installing project dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if not %ERRORLEVEL%==0 goto :error

if not exist ".env" (
    echo.
    echo Creating .env from .env.example...
    copy ".env.example" ".env" >nul
)

echo.
echo Running tests...
".venv\Scripts\python.exe" -m pytest -q
if not %ERRORLEVEL%==0 (
    echo.
    echo WARNING: Setup installed dependencies, but tests reported a problem.
    echo You can still try running the backend and dashboard, or send me the error.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Setup complete.
echo Next:
echo   1. Double-click start_backend.bat
echo   2. Double-click start_dashboard.bat
echo ==========================================
pause
exit /b 0

:error
echo.
echo ERROR: Setup failed. Copy the error above and send it to ChatGPT.
pause
exit /b 1
