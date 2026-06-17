@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found. Run setup_windows.bat first.
    pause
    exit /b 1
)
if not exist ".env" copy ".env.example" ".env" >nul
echo Starting backend at http://localhost:8000
echo API docs: http://localhost:8000/docs
echo Keep this window open.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload
pause
