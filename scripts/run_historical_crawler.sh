#!/bin/bash
set -e

echo "[INFO] Starting Historical Crawler..."

export PYTHONPATH=$(dirname "$0")/..
export DATA_DIR="../data/historical"
export CRYPTO_SYMBOLS="BTC/USDT,ETH/USDT"
export CRAWL_INTERVAL="1m"
export CRAWL_LIMIT=1000

mkdir -p "$DATA_DIR"

python3 ../services/crawler/historical_crawler.py

echo "Historical Crawler finished successfully."