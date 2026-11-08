@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dpn0.ps1" %*
if errorlevel 1 (
    echo V4.1 startup failed. See the error above.
    pause
    exit /b 1
)
exit /b 0

