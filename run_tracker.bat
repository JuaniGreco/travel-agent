@echo off
REM Ejecutado por Windows Task Scheduler (ver install_task.ps1)
cd /d "%~dp0"
if not exist logs mkdir logs
call .venv\Scripts\activate.bat
echo ===== %date% %time% ===== >> logs\tracker.log
python main.py run >> logs\tracker.log 2>&1

