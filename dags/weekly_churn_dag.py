from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import os
import sys

# Add scripts folder to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + '/../scripts')

# Import prediction function
from predict_churn import predict_churn

# Set environment variable for GCP key (optional; override in Docker Compose for production)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/keys/gcp_key.json"

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 5),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'weekly_churn_prediction',
    default_args=default_args,
    description='A weekly DAG to run churn predictions using BigQuery data',
    schedule_interval='@weekly',
)

run_prediction = PythonOperator(
    task_id='predict_weekly_churn',
    python_callable=predict_churn,
    dag=dag,
)