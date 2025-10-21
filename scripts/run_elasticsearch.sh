#!/bin/bash
set -e

echo "[INFO] Starting Elasticsearch..."
export ES_JAVA_HOME=$(/usr/libexec/java_home -v 17)
export JAVA_HOME=$ES_JAVA_HOME

# Check Elasticsearch running
if curl -s http://localhost:9200 >/dev/null 2>&1; then
  echo "[INFO] Elasticsearch is already running."
else
  echo "[INFO] Starting new Elasticsearch instance..."
  elasticsearch -E xpack.ml.enabled=false > logs/elasticsearch.log 2>&1 &
  echo "[INFO] Waiting for Elasticsearch to start..."
  # Wait max 60 seconds for ES up
  for i in {1..60}; do
    if curl -s http://localhost:9200 >/dev/null 2>&1; then
      echo "[INFO] Elasticsearch is now up and running!"
      break
    fi
    sleep 2
  done
  if ! curl -s http://localhost:9200 >/dev/null 2>&1; then
    echo "[ERROR] Elasticsearch failed to start within 60 seconds!"
    exit 1
  fi
fi

# When Elasticsearch ready, run Kibana
echo "[INFO] Starting Kibana..."
if pgrep -x "kibana" >/dev/null; then
  echo "[INFO] Kibana is already running."
else
  kibana > logs/kibana.log 2>&1 &
  echo "[INFO] Kibana started successfully! (Check logs/kibana.log)"
fi