#!/bin/bash
set -e

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$BASE_DIR/logs"

echo "=== Starting Local BigData Pipeline ==="

# Start Elasticsearch & Kibana
echo "[INFO] Starting Elasticsearch + Kibana..."
bash ./run_elasticsearch.sh > "$BASE_DIR/logs/elasticsearch.log" 2>&1 &
sleep 15

# Start Spark Stream Processor
echo "[INFO] Starting Spark Stream Processor..."
bash ./run_stream_processor.sh > "$BASE_DIR/logs/stream.log" 2>&1 &
sleep 5

# Start Kafka Producer
echo "[INFO] Starting Kafka Producer..."
bash ./run_ohlcv_1m_producer.sh > "$BASE_DIR/logs/producer.log" 2>&1 &
sleep 3

echo "=== All services started successfully ==="
echo "Logs available in ./logs/"