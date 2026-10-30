@echo off
setlocal
cd /d "%~dp0"

if not exist "_sauvegardes" (
    echo Aucune sauvegarde disponible.
    pause
    exit /b 1
)

echo Sauvegardes disponibles :
dir /b /ad "_sauvegardes"
echo.
set /p "CHOIX=Nom exact de la sauvegarde a restaurer : "

if not exist "_sauvegardes\%CHOIX%" (
    echo Sauvegarde introuvable.
    pause
    exit /b 1
)

robocopy "_sauvegardes\%CHOIX%" "%CD%" /E /R:1 /W:1 >nul
echo Sauvegarde restauree.
pause
