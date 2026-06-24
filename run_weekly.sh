#!/bin/bash
# ks-scout weekly runner — triggered by launchd every Tuesday 10:00 AM
set -e

PROJECT_DIR="/Users/simon/Development/ks-scout"
LOG_DIR="$PROJECT_DIR/output"

mkdir -p "$LOG_DIR"

# Source API keys from .env
[ -f "$PROJECT_DIR/.env" ] && source "$PROJECT_DIR/.env"

cd "$PROJECT_DIR"

# Redirect all output to log
exec 1>>"$LOG_DIR/cron.log"
exec 2>&1

echo "=== ks-scout run: $(date '+%Y-%m-%d %H:%M:%S') ==="
/Users/simon/.local/bin/uv run ks-scout \
    --ended-within-days 20 \
    --min-pledged-usd 20000 \
    --verbose \
    --no-cache \
    --output yaml
echo ""
