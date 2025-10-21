#!/bin/bash
set -e

mkdir -p logs

echo "=== Starting Local BigData Pipeline ==="

echo "[INFO] Starting Elasticsearch..."
bash ./run_elasticsearch.sh > ../logs/elasticsearch.log 2>&1 &
sleep 15

echo "[INFO] Starting Spark Stream Processor..."
bash ./run_stream_processor.sh > ../logs/stream.log 2>&1 &
sleep 5

echo "[INFO] Starting Kafka Producer..."
bash ./run_ohlcv_1m_producer.sh > ../logs/producer.log 2>&1 &
sleep 3

echo "=== All services started successfully ==="
echo "Logs available in ./logs/"