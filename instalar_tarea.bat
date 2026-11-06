@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================================================
echo   ⏰ Instalando Tarea Automática en Windows Task Scheduler
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_task.ps1" %*

echo.
pause

