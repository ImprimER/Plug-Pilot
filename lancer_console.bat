@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv-dev\Scripts\python.exe" (
    call lancer_dev.bat
    exit /b
)

call ".venv-dev\Scripts\activate.bat"
python "%CD%\main.py"

echo.
pause
