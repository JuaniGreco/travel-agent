@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo ===== %date% %time% ===== >> logs\tracker.log
"%PYTHON_EXE%" main.py run %* >> logs\tracker.log 2>&1
endlocal
