#!/usr/bin/env bash
# Quick start script for The Daily Broadsheet
cd "$(dirname "$0")"

PORT="${1:-8080}"
echo "Starting The Daily Broadsheet on port $PORT..."
python3 app.py "$PORT"
