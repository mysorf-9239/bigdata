#!/bin/bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
java -version

export KAFKA_BROKER=localhost:9092
export KAFKA_OHLCV_1M_TOPIC=crypto_ohlcv_1m
export CHECKPOINT_DIR=/tmp/stream-checkpoint
export WRITE_TO_CONSOLE=true

spark-submit \
  --master 'local[2]' \
  --conf spark.hadoop.fs.file.impl.disable.cache=true \
  --conf spark.driver.extraJavaOptions="--add-opens java.base/javax.security.auth=ALL-UNNAMED --enable-native-access=ALL-UNNAMED" \
  --conf spark.executor.extraJavaOptions="--add-opens java.base/javax.security.auth=ALL-UNNAMED --enable-native-access=ALL-UNNAMED" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  ../services/stream/stream_processor.py