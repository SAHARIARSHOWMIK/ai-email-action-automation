@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found. Run setup_windows.bat first.
    pause
    exit /b 1
)
set API_BASE_URL=http://localhost:8000
echo Starting dashboard at http://localhost:8501
echo Keep this window open.
".venv\Scripts\python.exe" -m streamlit run dashboard/app.py
pause
