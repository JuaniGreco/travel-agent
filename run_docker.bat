@echo off
REM Ejecución desatendida del Travel Agent vía Docker
cd /d "%~dp0"
if not exist logs mkdir logs
echo ===== Docker Run %date% %time% ===== >> logs\tracker_docker.log
docker compose run --rm travel-agent run >> logs\tracker_docker.log 2>&1
