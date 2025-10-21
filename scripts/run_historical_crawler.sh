#!/bin/bash
set -e

echo "[INFO] Starting Historical Crawler..."

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONPATH=$BASE_DIR
export DATA_DIR="$BASE_DIR/data/historical"
export CRYPTO_SYMBOLS="BTC/USDT,ETH/USDT"
export CRAWL_INTERVAL="1m"
export CRAWL_LIMIT=1000

mkdir -p "$DATA_DIR"

python3 "$BASE_DIR/services/crawler/historical_crawler.py"

echo "Historical Crawler finished successfully."