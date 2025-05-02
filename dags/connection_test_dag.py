from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime

with DAG("test_gcp_conn", start_date=datetime(2024, 1, 1), schedule_interval=None, catchup=False) as dag:
    test = BigQueryInsertJobOperator(
        task_id="run_query",
        configuration={
            "query": {
                "query": "SELECT 1",
                "useLegacySql": False,
            }
        },
        location="US",
        gcp_conn_id="google_cloud_default"
    )
