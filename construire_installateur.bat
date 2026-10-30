@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\PlugPilot\PlugPilot.exe" (
    echo PlugPilot n'existe pas encore.
    echo Construction de l'application...
    call construire_exe.bat
    if errorlevel 1 exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not exist "%ISCC%" (
    echo.
    echo Inno Setup 6 n'est pas installe.
    echo Installe-le depuis https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

if exist "installer" rmdir /s /q "installer"

"%ISCC%" PlugPilot.iss

if errorlevel 1 (
    echo ECHEC DE LA CONSTRUCTION DE L'INSTALLATEUR.
    pause
    exit /b 1
)

echo.
echo Installateur cree :
echo %CD%\installer\PlugPilot-Setup.exe
explorer "%CD%\installer"
pause
