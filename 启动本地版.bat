@echo off
setlocal

set "APP=%~dp0runtime\LocalDatabaseQA\LocalDatabaseQA.exe"
if not exist "%APP%" goto app_missing

where ollama.exe >nul 2>&1
if errorlevel 1 goto ollama_missing

ollama list >nul 2>&1
if errorlevel 1 (
    start "Ollama" /min ollama serve
    timeout /t 2 /nobreak >nul
)

start "" "%APP%" %*
exit /b 0

:app_missing
echo LocalDatabaseQA.exe was not found.
echo Run build_windows.ps1 to rebuild the local application.
pause
exit /b 1

:ollama_missing
echo Ollama was not found. Install Ollama and the required models first.
pause
exit /b 1
