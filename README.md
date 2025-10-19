# Big Data Crypto – Lambda System

Hệ thống phân tích dữ liệu tiền điện tử theo thời gian thực, áp dụng kiến trúc **Lambda Architecture** gồm 3 tầng:

- **Batch Layer:** xử lý dữ liệu lịch sử bằng Spark
- **Speed Layer:** xử lý dữ liệu real-time qua Kafka + Spark Streaming
- **Serving Layer:** hiển thị kết quả qua Flask + Elasticsearch

---

## Cấu trúc ban đầu

```
Big_Data_Pr/
│
├── services/
│   ├── producer/         # Kafka producer
│   ├── stream/           # Spark streaming
│   ├── batch/            # Batch processing
│   ├── web/              # Chứa Flask dashboard
│   └── utils/            # Các helper (API, HDFS, Elastic,...)
│
├── docker/               # Dockerfile cho từng service
├── k8s/                  # YAML manifests cho Kubernetes
├── scripts/              # Script chạy, tạo dữ liệu, setup cron
│
├── data/                 # Dữ liệu test local
├── logs/                 # Log khi chạy thực tế
│
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Cài đặt ban đầu

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```