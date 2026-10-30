@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PATCH=%CD%\mise_a_jour.zip"
set "TEMP=%CD%\_mise_a_jour_temporaire"
set "BACKUPS=%CD%\_sauvegardes"

if not exist "%PATCH%" (
    echo.
    echo Aucun fichier "mise_a_jour.zip" trouve.
    echo Place le patch a cote de ce fichier puis relance.
    echo.
    pause
    exit /b 1
)

if exist "%TEMP%" rmdir /s /q "%TEMP%"
mkdir "%TEMP%"
if not exist "%BACKUPS%" mkdir "%BACKUPS%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -LiteralPath '%PATCH%' -DestinationPath '%TEMP%' -Force"

if errorlevel 1 (
    echo Impossible de decompresser la mise a jour.
    pause
    exit /b 1
)

if not exist "%TEMP%\patch_manifest.txt" (
    echo.
    echo Patch invalide : patch_manifest.txt est absent.
    rmdir /s /q "%TEMP%"
    pause
    exit /b 1
)

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%I"
set "BACKUP=%BACKUPS%\%STAMP%"
mkdir "%BACKUP%"

echo Sauvegarde des fichiers actuels...
for /f "usebackq delims=" %%F in ("%TEMP%\patch_manifest.txt") do (
    if exist "%CD%\%%F" (
        for %%D in ("%BACKUP%\%%F") do if not exist "%%~dpD" mkdir "%%~dpD"
        copy /y "%CD%\%%F" "%BACKUP%\%%F" >nul
    )
)

echo Installation de la mise a jour...
for /f "usebackq delims=" %%F in ("%TEMP%\patch_manifest.txt") do (
    if not exist "%TEMP%\%%F" (
        echo Fichier absent du patch : %%F
        echo Mise a jour annulee.
        rmdir /s /q "%TEMP%"
        pause
        exit /b 1
    )
    for %%D in ("%CD%\%%F") do if not exist "%%~dpD" mkdir "%%~dpD"
    copy /y "%TEMP%\%%F" "%CD%\%%F" >nul
)

rmdir /s /q "%TEMP%"
del /q "%PATCH%"

echo.
echo Mise a jour terminee.
echo Sauvegarde : %BACKUP%
echo.
pause
