@echo off
setlocal
chcp 65001 >nul
title Mistybot - Transfert de memoire Railway
cd /d "%~dp0"

if not exist "%~dp0transfer-railway-memory.ps1" (
    echo Le fichier transfer-railway-memory.ps1 doit rester a cote de ce .bat.
    pause
    exit /b 1
)

if not exist "%~dp0railway-memory-transfer.py" (
    echo Le fichier railway-memory-transfer.py doit rester a cote de ce .bat.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0transfer-railway-memory.ps1"
set "TRANSFER_EXIT=%ERRORLEVEL%"

echo.
if not "%TRANSFER_EXIT%"=="0" (
    echo Le transfert n'a pas ete valide. Lis le message affiche au-dessus.
) else (
    echo Termine. La fenetre peut maintenant etre fermee.
)
echo.
pause
exit /b %TRANSFER_EXIT%
