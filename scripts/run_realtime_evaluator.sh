#!/bin/bash
set -e

export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export ES_PRED_INDEX=crypto_ohlcv_1m_pred
export ES_STATS_INDEX=crypto_prediction_stats
export EVAL_POLL_INTERVAL=10

echo "[INFO] Starting Realtime Evaluator..."
python3 ../services/evaluator/realtime_evaluator.py