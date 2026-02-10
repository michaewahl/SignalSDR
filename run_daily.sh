#!/bin/bash
# SignalSDR daily scan - runs the full pipeline
# Scheduled via crontab: 0 12 * * * /path/to/run_daily.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use the project venv
echo "=== SignalSDR run: $(date) ===" >> data/signalsdr.log
.venv/bin/python main.py >> data/signalsdr.log 2>&1
