#!/bin/bash
# Prospect Scanner — Daily run script
# Used by launchd to run the scanner every morning

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use the Python3 from PATH
PYTHON=$(which python3)

# Run the full scan with Telegram notifications
$PYTHON main.py --notify >> "$SCRIPT_DIR/output/cron.log" 2>&1

echo "$(date): Scan completed" >> "$SCRIPT_DIR/output/cron.log"
