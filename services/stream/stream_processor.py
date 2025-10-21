"""
Service: stream_processor.py
--------------------------
Kafka → Spark Structured Streaming → Model Predict → Elasticsearch

Reads JSON OHLCV messages from Kafka, applies trained XGBoost model
to predict price direction ("UP"/"DOWN"), then writes to Elasticsearch.

Author: Mysorf
"""

import os
import joblib
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from xgboost import XGBClassifier

# Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_OHLCV_1M_TOPIC", "crypto_ohlcv_1m")

# Elasticsearch
ES_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ES_PORT = os.getenv("ELASTICSEARCH_PORT", "9200")
# Nên tách index dự đoán khỏi index dữ liệu gốc
ES_INDEX = os.getenv("ELASTICSEARCH_INDEX", "crypto_ohlcv_1m_pred")

# Streaming
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/stream-checkpoint-es")

# Nếu ES_HOST/PORT trống hoặc WRITE_TO_CONSOLE=true → ghi ra console
WRITE_TO_CONSOLE = (
    os.getenv("WRITE_TO_CONSOLE", "false").lower() == "true"
    or not (ES_HOST and ES_PORT)
)

# Path
MODEL_PATH = os.getenv("MODEL_PATH", "../models/xgb_model.json")
SCALER_PATH = os.getenv("SCALER_PATH", "../models/scaler.pkl")

# Schema
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


# Load model
def load_model():
  print(f"[INFO] Loading model: {MODEL_PATH} and scaler: {SCALER_PATH} ...")
  model = XGBClassifier()
  model.load_model(MODEL_PATH)
  scaler = joblib.load(SCALER_PATH)
  return model, scaler


MODEL, SCALER = load_model()


# Predict udf
def predict_direction(open_, high_, low_, close_, volume_):
  if None in (open_, high_, low_, close_, volume_):
    return "UNKNOWN"
  try:
    features = pd.DataFrame(
      [[open_, high_, low_, close_, volume_]],
      columns=["open", "high", "low", "close", "volume"]
    )
    scaled = SCALER.transform(features)
    pred = MODEL.predict(scaled)
    return "UP" if int(pred[0]) == 1 else "DOWN"
  except Exception as e:
    print("[WARN] Prediction error:", e)
    return "ERROR"


predict_udf = udf(predict_direction, StringType())


def main():
  spark = (
    SparkSession.builder
    .appName("stream-ohlcv-predict")
    # Fix Hadoop UGI getSubject bug on macOS + Java >= 17
    .config("spark.hadoop.fs.file.impl.disable.cache", "true")
    .config("spark.hadoop.fs.AbstractFileSystem.file.impl", "org.apache.hadoop.fs.local.LocalFs")
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR)
    .getOrCreate()
  )
  spark.sparkContext.setLogLevel("WARN")

  # Read from Kafka stream
  raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BROKER)
    .option("subscribe", KAFKA_TOPIC)
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

  # Apply Prediction
  predicted = parsed.withColumn(
    "prediction",
    predict_udf(col("open"), col("high"), col("low"), col("close"), col("volume"))
  )

  # Checkpoint args
  checkpoint_args = {"checkpointLocation": CHECKPOINT_DIR}

  if WRITE_TO_CONSOLE:
    query = (
      predicted.writeStream
      .outputMode("append")
      .format("console")
      .option("truncate", "false")
      .option("numRows", 20)
      .options(**checkpoint_args)
      .start()
    )
    print("[INFO] Writing PREDICTIONS to CONSOLE sink…")
  else:
    query = (
      predicted.writeStream
      .outputMode("append")
      .format("org.elasticsearch.spark.sql")
      .option("es.nodes", ES_HOST)
      .option("es.port", ES_PORT)
      .option("es.nodes.wan.only", "true")
      .option("es.index.auto.create", "true")
      .option("es.resource", ES_INDEX)
      .options(**checkpoint_args)
      .start()
    )
    print(f"[INFO] Writing PREDICTIONS to Elasticsearch http://{ES_HOST}:{ES_PORT} index={ES_INDEX}")

  query.awaitTermination()


if __name__ == "__main__":
  main()
