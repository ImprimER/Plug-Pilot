@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-build\Scripts\python.exe" (
    py -3.11 -m venv .venv-build
    if errorlevel 1 py -3 -m venv .venv-build
    if errorlevel 1 exit /b 1
)
".venv-build\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6.11,<7" pywin32-ctypes
if errorlevel 1 (
    echo Installation des dependances impossible.
    pause
    exit /b 1
)
".venv-build\Scripts\python.exe" construire_version_stable.py
if errorlevel 1 (
    echo La construction n'a pas abouti. Consulte le message ci-dessus.
    pause
    exit /b 1
)
explorer "%CD%\installer"
pause
