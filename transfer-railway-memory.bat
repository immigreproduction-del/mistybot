@echo off
setlocal
cd /d "%~dp0"

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
