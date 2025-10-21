#!/bin/bash
set -e

echo "=== Starting Batch Processor (Model Training) ==="

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
DATA_DIR="$BASE_DIR/data/historical"
CRAWLER_SCRIPT="$BASE_DIR/scripts/run_historical_crawler.sh"
BATCH_SCRIPT="$BASE_DIR/services/batch/batch_processor.py"

# Activate virtual env
if [ -d "$BASE_DIR/.venv" ]; then
  source "$BASE_DIR/.venv/bin/activate"
fi

# === Step 1: Check data availability ===
if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
  echo "[WARN] No historical data found in $DATA_DIR"
  echo "[INFO] Running crawler..."
  bash "$CRAWLER_SCRIPT"
else
  echo "[INFO] Found existing historical data in $DATA_DIR"
fi

# === Step 2: Run Batch Processor ===
export PYTHONPATH=$BASE_DIR
python3 "$BATCH_SCRIPT"

echo "=== Batch Processor finished successfully ==="