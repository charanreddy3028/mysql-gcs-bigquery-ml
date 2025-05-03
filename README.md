# 🚀 End-to-End Data Pipeline: MySQL → GCS → BigQuery → Local Analytics

[![Airflow DAGs](https://img.shields.io/badge/Airflow-DAGs-blue)](https://airflow.apache.org/)  
[![BigQuery](https://img.shields.io/badge/BigQuery-GCP-yellow)](https://cloud.google.com/bigquery)  
[![GCS](https://img.shields.io/badge/Storage-GCS-blueviolet)](https://cloud.google.com/storage)  
[![Python](https://img.shields.io/badge/Python-Local--ML-green)](https://www.python.org/)  

---

## 📌 Project Overview

This project implements a scalable, automated data pipeline that extracts data from MySQL, transforms it through three logical layers (**Bronze → Silver → Gold**), and integrates with **Google Cloud Storage** and **BigQuery**. It enables both cloud-based querying and local analytics, including daily machine learning predictions.

---

## 🔁 Data Flow Architecture

       ┌──────────┐
       │  MySQL   │
       └────┬─────┘
            ▼
 ┌────────────────────┐
 │   Bronze Layer     │ → Raw data from MySQL stored in GCS
 └────────────────────┘
            ▼
 ┌────────────────────┐
 │   Silver Layer     │ → Cleaned/validated data stored in GCS
 └────────────────────┘
            ▼
 ┌────────────────────┐
 │   Gold Layer       │ → Final transformed data stored in GCS
 └────────────────────┘
            ▼
 ┌────────────────────┐
 │    BigQuery        │ ← Only Gold Layer is loaded here
 └────────────────────┘
            ▼
 ┌────────────────────┐
 │   Local System     │ → Advanced analytics & ML training
 └────────────────────┘
            ▼
 ┌────────────────────┐
 │   Predictions      │ → Sent back to BigQuery
 └────────────────────┘

    [ Orchestrated Daily via Airflow DAGs ]


---

## 🛠️ Tech Stack

| Layer           | Tool/Service             |
|-----------------|--------------------------|
| Data Source     | MySQL                    |
| Storage         | Google Cloud Storage     |
| Data Warehouse  | Google BigQuery          |
| Workflow Engine | Apache Airflow           |
| ML/Analytics    | Python (Local)           |

---

## 📈 Key Features

- ✅ Modular architecture using Bronze, Silver, and Gold layers  
- ☁️ Scalable cloud storage and compute using GCS & BigQuery  
- 🔁 Automated ETL and model training using Airflow DAGs  
- 🧠 Local system used for ML pipelines & advanced analytics  
- 📤 Daily predictions pushed back to BigQuery

---

## 🚀 Getting Started

### Prerequisites

- Google Cloud Project (GCS & BigQuery enabled)  
- Apache Airflow setup (locally or via Cloud Composer)  
- Python 3.8+ environment for local ML processing  
- MySQL access credentials  

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
Configure MySQL and GCP credentials
Add your credentials in the .env or config.py as needed.

Set up DAGs in Airflow
Place DAG scripts in your Airflow /dags folder.
Trigger or schedule DAGs.

Run local analytics

bash
Copy
Edit
python analytics/predict.py
View results
See results in BigQuery or Looker Studio.

📅 Automation
All pipeline steps are orchestrated via Airflow DAGs, which:

Extract data from MySQL daily

Stage and transform data into GCS

Load Gold Layer to BigQuery

Trigger local scripts for ML training & predictions

