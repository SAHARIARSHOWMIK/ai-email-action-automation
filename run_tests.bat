@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Run setup_windows.bat first.
    pause
    exit /b 1
)
set PYTHONPATH=%CD%
".venv\Scripts\python.exe" -m pytest -q
pushd frontend
call npm run build
popd
pause
