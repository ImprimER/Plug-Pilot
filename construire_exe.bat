@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo CONSTRUCTION DE PLUGPILOT
echo ==========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo ERREUR : Python est introuvable.
    echo Installe Python 3.11 ou 3.12 depuis python.org.
    pause
    exit /b 1
)

if not exist ".venv-build\Scripts\python.exe" (
    echo Creation de l'environnement de construction...
    py -3.11 -m venv .venv-build
    if errorlevel 1 py -3 -m venv .venv-build
)

call ".venv-build\Scripts\activate.bat"

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install "pyinstaller>=6.11,<7" pywin32-ctypes

if errorlevel 1 (
    echo ERREUR : installation des dependances impossible.
    pause
    exit /b 1
)

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

pyinstaller --noconfirm --clean PlugPilot.spec

if errorlevel 1 (
    echo.
    echo ECHEC DE LA CONSTRUCTION.
    pause
    exit /b 1
)

if not exist "dist\PlugPilot\PlugPilot.exe" (
    echo ERREUR : PlugPilot.exe n'a pas ete genere.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo CONSTRUCTION TERMINEE
echo ==========================================
echo Application :
echo %CD%\dist\PlugPilot\PlugPilot.exe
echo.
echo Le format dossier demarre plus vite et consomme moins
echo de ressources qu'un EXE monofichier.
echo.
explorer "%CD%\dist\PlugPilot"
pause
