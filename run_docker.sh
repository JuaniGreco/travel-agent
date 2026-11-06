#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

mkdir -p logs data capturas .browser_profile
echo "===== Docker Run $(date) =====" >> logs/tracker_docker.log
docker compose run --rm travel-agent run >> logs/tracker_docker.log 2>&1

