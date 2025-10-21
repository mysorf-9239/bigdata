"""
Service: historical_crawler.py
-------------------------------
Crawl historical OHLCV data from Binance REST API and save to local CSV.

- Supports multiple symbols (e.g., BTC/USDT, ETH/USDT)
- Interval: 1m, 5m, 1h, 1d
- Limit: configurable (default 1000)
- Auto-paginates to get full history (using startTime)

Author: Mysorf
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "../data/historical")
os.makedirs(DATA_DIR, exist_ok=True)

SYMBOLS = [s.strip().upper() for s in os.getenv("CRYPTO_SYMBOLS", "BTC/USDT,ETH/USDT").split(",")]
INTERVAL = os.getenv("CRAWL_INTERVAL", "1m")
LIMIT = int(os.getenv("CRAWL_LIMIT", "1000"))
API_BASE = "https://api.binance.com/api/v3/klines"


def fetch_binance_ohlcv(symbol: str, interval: str = "1m", limit: int = 1000, start_time: int = None):
  pair = symbol.replace("/", "")
  params = {"symbol": pair, "interval": interval, "limit": limit}
  if start_time:
    params["startTime"] = start_time

  r = requests.get(API_BASE, params=params, timeout=10)
  r.raise_for_status()
  return r.json()


def crawl_symbol(symbol: str):
  print(f"[INFO] Crawling {symbol}...")
  all_rows = []
  start_time = None
  while True:
    data = fetch_binance_ohlcv(symbol, INTERVAL, LIMIT, start_time)
    if not data:
      break
    all_rows.extend(data)
    start_time = data[-1][0] + 1
    print(f"  → fetched {len(data)} rows, total: {len(all_rows)}")
    time.sleep(0.5)
    if len(data) < LIMIT:
      break

  df = pd.DataFrame(all_rows, columns=[
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "num_trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
  ])
  df["symbol"] = symbol
  df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
  df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

  file_path = os.path.join(DATA_DIR, f"{symbol.replace('/', '_')}_{INTERVAL}.csv")
  df.to_csv(file_path, index=False)
  print(f"Saved {len(df)} rows to {file_path}")
  return file_path


def main():
  print(f"=== Starting Historical Crawler for {SYMBOLS} ===")
  for s in SYMBOLS:
    try:
      crawl_symbol(s)
    except Exception as e:
      print(f"[ERROR] Failed to crawl {s}: {e}")


if __name__ == "__main__":
  main()
