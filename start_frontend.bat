@echo off
cd /d "%~dp0\frontend"
if not exist "node_modules" (
    echo ERROR: Frontend dependencies not found. Run setup_windows.bat first.
    pause
    exit /b 1
)
echo Starting MailPilot AI at http://localhost:5173
call npm run dev
pause
