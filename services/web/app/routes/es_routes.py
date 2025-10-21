from fastapi import APIRouter, Query
import os, requests
from datetime import datetime
from typing import Any, Dict, List, Optional

router = APIRouter()

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "crypto_ohlcv_1m_pred")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASS")


def es_request(path: str, body: Optional[Dict] = None, method: str = "GET") -> Dict[str, Any]:
  url = f"{ES_URL.rstrip('/')}/{path.lstrip('/')}"
  auth = (ES_USER, ES_PASS) if ES_USER and ES_PASS else None
  headers = {"Content-Type": "application/json"}
  if method.upper() == "GET":
    r = requests.get(url, auth=auth, headers=headers)
  else:
    r = requests.post(url, json=body or {}, auth=auth, headers=headers)
  r.raise_for_status()
  return r.json()


def time_range_filter(minutes: int) -> Dict[str, Any]:
  return {"range": {"@timestamp": {"gte": f"now-{minutes}m", "lte": "now"}}}


@router.get("/counts")
def counts(minutes: int = Query(15, ge=1, le=1440)):
  body = {
    "size": 0,
    "query": {"bool": {"filter": [time_range_filter(minutes)]}},
    "aggs": {"by_pred": {"terms": {"field": "prediction.keyword", "size": 5}}}
  }
  res = es_request(f"{ES_INDEX}/_search", body, "POST")
  buckets = res.get("aggregations", {}).get("by_pred", {}).get("buckets", [])
  return {b["key"]: b["doc_count"] for b in buckets}


@router.get("/timeseries")
def timeseries(minutes: int = Query(60), interval: str = Query("1m")):
  body = {
    "size": 0,
    "query": {"bool": {"filter": [time_range_filter(minutes)]}},
    "aggs": {
      "ts": {
        "date_histogram": {"field": "@timestamp", "fixed_interval": interval, "min_doc_count": 0},
        "aggs": {"by_pred": {"terms": {"field": "prediction.keyword", "size": 5}}}
      }
    }
  }
  res = es_request(f"{ES_INDEX}/_search", body, "POST")
  buckets = res.get("aggregations", {}).get("ts", {}).get("buckets", [])
  series: Dict[str, List[List[int]]] = {}
  for b in buckets:
    ts_ms = int(datetime.fromisoformat(b["key_as_string"].replace("Z", "+00:00")).timestamp() * 1000)
    for pred in b["by_pred"]["buckets"]:
      series.setdefault(pred["key"], []).append([ts_ms, pred["doc_count"]])
  return series


@router.get("/top-symbols")
def top_symbols(minutes: int = Query(60), size: int = Query(10)):
  body = {
    "size": 0,
    "query": {"bool": {"filter": [time_range_filter(minutes)]}},
    "aggs": {"by_symbol": {"terms": {"field": "symbol.keyword", "size": size}}}
  }
  res = es_request(f"{ES_INDEX}/_search", body, "POST")
  buckets = res.get("aggregations", {}).get("by_symbol", {}).get("buckets", [])
  return [{"symbol": b["key"], "count": b["doc_count"]} for b in buckets]


@router.get("/latest")
def latest(size: int = Query(50)):
  body = {
    "size": 0,
    "aggs": {
      "symbols": {
        "terms": {"field": "symbol.keyword", "size": size},
        "aggs": {
          "latest": {
            "top_hits": {
              "size": 1,
              "sort": [{"@timestamp": {"order": "desc"}}],
              "_source": {
                "includes": [
                  "@timestamp",
                  "symbol",
                  "exchange",
                  "open",
                  "high",
                  "low",
                  "close",
                  "volume",
                  "prediction",
                ]
              },
            }
          }
        },
      }
    },
  }
  res = es_request(f"{ES_INDEX}/_search", body, "POST")
  out = []
  for b in res.get("aggregations", {}).get("symbols", {}).get("buckets", []):
    hits = b["latest"]["hits"]["hits"]
    if hits:
      out.append(hits[0]["_source"])
  out.sort(key=lambda x: x["@timestamp"], reverse=True)
  return out
