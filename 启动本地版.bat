@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_local_candidate.ps1"
if errorlevel 1 (
    echo Local candidate startup failed. See the error above.
    pause
    exit /b 1
)
exit /b 0
