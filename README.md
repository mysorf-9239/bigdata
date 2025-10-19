# Big Data Crypto – Lambda System

Real-time cryptocurrency data analysis system, applying **Lambda Architecture** with 3 layers:

- **Batch Layer:** historical data processing with Spark
- **Speed Layer:** Real-time data processing via Kafka + Spark Streaming
- **Serving Layer:** Display results via Flask + Elasticsearch

---

## Original structure

```
Bigdata/
│
├── services/
│   ├── producer/         # Kafka producer
│   ├── stream/           # Spark streaming
│   ├── batch/            # Batch processing
│   ├── web/              # Chứa Flask dashboard
│   └── utils/            # Helpers (API, HDFS, Elastic,...)
│
├── docker/               # Dockerfile for each service
├── k8s/                  # YAML manifests for Kubernetes
├── scripts/              # Script run, create data, setup cron
│
├── data/                 # Local test data
├── logs/                 # Log when running in practice
│
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```