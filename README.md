<<<<<<< HEAD
<<<<<<< HEAD
# MySQL to BigQuery Pipeline with Airflow

This repository contains an **end-to-end data pipeline** built using **Apache Airflow**, moving data from a **MySQL database** through **Google Cloud Storage (GCS)** to **BigQuery**.

It demonstrates:
- Extracting data from MySQL
- Uploading to GCS (Bronze Layer)
- Transforming and joining data (Silver Layer)
- Aggregating and loading into BigQuery (Golden Layer)

---

## 📁 Files Included

| File | Description |
|------|-------------|
| `dags/mysql_to_gcs.py` | Extracts data from MySQL and uploads to GCS Bronze Layer |
| `dags/gcs_bronze_to_silver.py` | Joins tables and transforms to Silver Layer |
| `dags/gcs_silver_to_golden_bigquery.py` | Aggregates customer metrics and loads to BigQuery |
| `insert_data.py` | Script to insert sample data into MySQL |

---

## 🛠️ Technologies Used

- Apache Airflow (via Docker)
- MySQL
- Google Cloud Storage (GCS)
- Google BigQuery
- Python (Pandas, Airflow Hooks)

---

## 🧪 Local Setup Instructions

### 1. Start Airflow via Docker

Make sure [Docker](https://www.docker.com/products/docker-desktop/) is running, then:

```bash
docker-compose up -d
=======
# mysql-gcs-bigquery-pipeline
>>>>>>> 0dc0e8d0e75a17cd0bab78f9cf75278cbaa39de2
=======
# mysql-gcs-bigquery-ml
>>>>>>> d15a0788215566ce900b79078adaea5c2e06819d
