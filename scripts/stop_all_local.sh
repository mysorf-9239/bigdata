#!/bin/bash
set -e
echo "=== Stopping Local BigData Pipeline ==="

stop_process() {
  local name="$1"
  echo "[INFO] Stopping $name..."
  pkill -f "$name" && echo "[OK] $name stopped." || echo "[WARN] $name not running."
}

stop_process "stream_processor.py"
stop_process "ohlcv_1m_producer"

echo "=== All processes stopped cleanly ==="