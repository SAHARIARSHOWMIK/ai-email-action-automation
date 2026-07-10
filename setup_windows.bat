@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo MailPilot AI - Windows development setup
echo ==============================================
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3.12 --version >nul 2>nul
    if %ERRORLEVEL%==0 set "PY=py -3.12"
)
if not defined PY (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 set "PY=python"
)
if not defined PY (
    echo ERROR: Python was not found. Install Python 3.12 or newer.
    pause
    exit /b 1
)

where node >nul 2>nul
if not %ERRORLEVEL%==0 (
    echo ERROR: Node.js was not found. Install Node.js 20 or newer.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    %PY% -m venv .venv || goto :error
)

".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error

pushd frontend
call npm install || goto :error_pop
popd

if not exist ".env" copy ".env.example" ".env" >nul

echo Running backend tests...
set PYTHONPATH=%CD%
".venv\Scripts\python.exe" -m pytest -q || goto :error

echo Running frontend production build...
pushd frontend
call npm run build || goto :error_pop
popd

echo.
echo Setup complete.
echo 1. Double-click start_backend.bat
echo 2. Double-click start_frontend.bat
pause
exit /b 0

:error_pop
popd
:error
echo.
echo Setup failed. Review the error above.
pause
exit /b 1
