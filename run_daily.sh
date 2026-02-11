#!/bin/bash
# SignalSDR daily scan - runs the full pipeline
# Scheduled via crontab: 0 6 * * * /path/to/run_daily.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure PATH includes common locations (cron has minimal PATH)
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Brief pause to let OneDrive finish any filesystem sync
sleep 5

# Activate venv from local disk (not OneDrive) to avoid filesystem lock hangs
source "$HOME/.signalsdr-venv/bin/activate"

echo "=== SignalSDR run: $(date) ===" >> data/signalsdr.log
python main.py >> data/signalsdr.log 2>&1
