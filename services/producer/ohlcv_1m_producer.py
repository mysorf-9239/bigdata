"""
Service: ohlcv_1m_producer
--------------------------
Target: Collect OHLCV data every minute from Binance (or other exchange)
and send to Kafka topic crypto_ohlcv_1m.

Author: Mysorf
"""

import os
import time
import json
import logging
from datetime import datetime
from kafka import KafkaProducer
import requests
from dotenv import load_dotenv

# === Load env ===
load_dotenv()

# === Config ===
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_OHLCV_1M_TOPIC", "crypto_ohlcv_1m")
SYMBOLS = [s.strip() for s in os.getenv("CRYPTO_SYMBOLS", "BTC/USDT").split(",")]
EXCHANGE = os.getenv("CRYPTO_EXCHANGE", "binance")
FETCH_INTERVAL = int(os.getenv("MINUTE_CHART_FETCH_INTERVAL", "60"))

# === Logging ===
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("producer")

# === Kafka ===
producer = KafkaProducer(
  bootstrap_servers=KAFKA_BROKER,
  value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


# === API Helper ===
def fetch_binance_ohlcv(symbol: str):
  """
  Call Binance API to get the latest 1m OHLCV price.
  """
  pair = symbol.replace("/", "")
  url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1m&limit=1"
  resp = requests.get(url, timeout=10)
  resp.raise_for_status()
  data = resp.json()[0]
  return {
    "symbol": symbol,
    "exchange": EXCHANGE,
    "@timestamp": datetime.utcnow().isoformat() + "Z",
    "timestamp_ms": int(data[0]),
    "open": float(data[1]),
    "high": float(data[2]),
    "low": float(data[3]),
    "close": float(data[4]),
    "volume": float(data[5]),
  }


# === Main Loop ===
def main():
  logger.info(f"Starting producer for {SYMBOLS} → {KAFKA_BROKER}/{KAFKA_TOPIC}")
  while True:
    for symbol in SYMBOLS:
      try:
        msg = fetch_binance_ohlcv(symbol)
        producer.send(KAFKA_TOPIC, msg)
        logger.info(f"Produced {symbol} {msg['close']}")
      except Exception as e:
        logger.exception(f"Error producing {symbol}: {e}")
    producer.flush()
    time.sleep(FETCH_INTERVAL)


if __name__ == "__main__":
  main()
