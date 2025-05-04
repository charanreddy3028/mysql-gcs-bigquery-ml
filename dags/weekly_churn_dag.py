from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import os
import sys

# Debug info
print("Python executable:", sys.executable)
print("sys.path:", sys.path)

# Add scripts folder to path
SCRIPTS_DIR = os.path.abspath(os.path.dirname(__file__)) + '/../scripts'
sys.path.insert(0, SCRIPTS_DIR)
print(f"Added to sys.path: {SCRIPTS_DIR}")

# Import prediction function
try:
    from predict_churn import predict_churn
    print("✅ predict_churn imported successfully")
except Exception as e:
    print(f"❌ Failed to import predict_churn: {str(e)}")
    raise

# Set environment variable for GCP key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/keys/gcp-key.json"
print(f"GOOGLE_APPLICATION_CREDENTIALS={os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

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

def debug_predict(**kwargs):
    print("🌀 Starting predict_churn...")
    try:
        result = predict_churn()
        print("✅ predict_churn completed successfully.")
        print("Result:", result)
        return result
    except Exception as e:
        print(f"❌ Error in predict_churn: {str(e)}")
        raise

run_prediction = PythonOperator(
    task_id='predict_weekly_churn',
    python_callable=debug_predict,
    provide_context=True,
    dag=dag,
)