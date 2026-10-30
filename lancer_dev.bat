@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv-dev\Scripts\pythonw.exe" (
    echo Installation initiale de PlugPilot...
    py -3.11 -m venv .venv-dev
    if errorlevel 1 py -3 -m venv .venv-dev
    if errorlevel 1 (
        echo Python est introuvable.
        pause
        exit /b 1
    )

    call ".venv-dev\Scripts\activate.bat"
    python -m pip install --upgrade pip
    pip install -r requirements.txt

    if errorlevel 1 (
        echo Installation impossible.
        pause
        exit /b 1
    )
)

start "" ".venv-dev\Scripts\pythonw.exe" "%CD%\main.py"
