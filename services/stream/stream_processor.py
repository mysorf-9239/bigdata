"""
Service: stream_processor.py
--------------------------
Spark Structured Streaming: Kafka -> (Console | Elasticsearch)

- Read JSON from Kafka topic (value is JSON from producer).
- Parse schema, select necessary columns.
- Write to Console (default) for quick testing.
- If set ELASTICSEARCH_HOST/PORT -> write to Elasticsearch index rotating hourly.

Env vars (eg set in .env):
KAFKA_BROKER=localhost:9092
KAFKA_OHLCV_1M_TOPIC=crypto_ohlcv_1m
CHECKPOINT_DIR=/tmp/stream-checkpoint

# If you want to record ES (optional):
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ES_STREAM_INDEX=crypto_ohlcv_1m_chartdata-%{+YYYY.MM.dd.HH}

# If you want to force console recording:
WRITE_TO_CONSOLE=true

Author: Mysorf
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
  StructType, StructField, StringType, DoubleType, LongType
)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = os.getenv("KAFKA_OHLCV_1M_TOPIC", "crypto_ohlcv_1m")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/stream-checkpoint")

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "")
ES_PORT = os.getenv("ELASTICSEARCH_PORT", "")
ES_INDEX = os.getenv("ES_STREAM_INDEX", "crypto_ohlcv_1m_chartdata-%{+YYYY.MM.dd.HH}")

# Nếu ES_HOST, ES_PORT rỗng hoặc WRITE_TO_CONSOLE=true -> ghi ra console
WRITE_TO_CONSOLE = (
    os.getenv("WRITE_TO_CONSOLE", "true").lower() == "true"
    or not (ES_HOST and ES_PORT)
)

schema = StructType([
  StructField("symbol", StringType()),
  StructField("exchange", StringType()),
  StructField("@timestamp", StringType()),
  StructField("timestamp_ms", LongType()),
  StructField("open", DoubleType()),
  StructField("high", DoubleType()),
  StructField("low", DoubleType()),
  StructField("close", DoubleType()),
  StructField("volume", DoubleType()),
])


def main():
  spark = (
    SparkSession.builder
    .appName("stream-ohlcv-1m")
    # Fix Hadoop UGI getSubject bug on macOS + Java >=17
    .config("spark.hadoop.fs.file.impl.disable.cache", "true")
    .config("spark.hadoop.fs.AbstractFileSystem.file.impl", "org.apache.hadoop.fs.local.LocalFs")
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR)
    .getOrCreate()
  )
  spark.sparkContext.setLogLevel("WARN")

  # Read from Kafka
  raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BROKER)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
  )

  # Parse JSON
  parsed = (
    raw.selectExpr("CAST(value AS STRING) AS json")
    .select(from_json(col("json"), schema).alias("data"))
    .select("data.*")
    .withColumnRenamed("@timestamp", "ts_iso")
  )

  # Disable checkpoint on macOS (fix getSubject issue)
  checkpoint_arg = {}
  if os.uname().sysname != "Darwin":  # Darwin = macOS
    checkpoint_arg["checkpointLocation"] = CHECKPOINT_DIR

  if WRITE_TO_CONSOLE:
    query = (
      parsed.writeStream
      .outputMode("append")
      .format("console")
      .option("truncate", "false")
      .option("numRows", 20)
      .options(**checkpoint_arg)
      .start()
    )
    print("[INFO] Writing to CONSOLE sink…")
  else:
    query = (
      parsed.writeStream
      .outputMode("append")
      .format("org.elasticsearch.spark.sql")
      .option("es.nodes", ES_HOST)
      .option("es.port", ES_PORT)
      .option("es.nodes.wan.only", "true")
      .option("es.resource", ES_INDEX)
      .options(**checkpoint_arg)
      .start()
    )
    print(f"[INFO] Writing to Elasticsearch http://{ES_HOST}:{ES_PORT} index={ES_INDEX}")

  query.awaitTermination()


if __name__ == "__main__":
  main()
