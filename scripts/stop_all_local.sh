#!/bin/bash
set -e
echo "=== Stopping Local BigData Pipeline ==="

function stop_process() {
  local name="$1"
  local pattern="$2"

  echo "[INFO] Stopping $name..."
  pids=$(pgrep -f "$pattern" || true)
  if [ -n "$pids" ]; then
    kill -9 $pids || true
    echo "[OK] $name stopped."
  else
    echo "[WARN] $name not running."
  fi
}

stop_process "Spark Stream Processor" "stream_processor.py"
stop_process "Kafka Producer" "ohlcv_1m_producer.py"
stop_process "Elasticsearch" "org.elasticsearch.bootstrap.Elasticsearch"
stop_process "Kibana" "kibana"
stop_process "Realtime Evaluator" "realtime_evaluator.py"

echo "=== All processes stopped cleanly ==="