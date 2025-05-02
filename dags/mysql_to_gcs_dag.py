from airflow import DAG
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

DAG_ID = 'mysql_to_gcs'

def extract_and_upload(table_name, **kwargs):
    try:
        # Use execution_date to generate a short timestamp
        execution_time = kwargs['ds_nodash'] + '_' + kwargs['execution_date'].strftime('%H%M%S')
        logging.info(f"Starting extraction for table: {table_name}, timestamp: {execution_time}")

        # MySQL Hook
        mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
        sql = f"SELECT * FROM {table_name}"
        df = mysql_hook.get_pandas_df(sql)

        # Local file handling
        tmp_dir = '/tmp/mysql_extract'
        os.makedirs(tmp_dir, exist_ok=True)
        file_name = f"{table_name}_data_{execution_time}.csv"
        local_path = os.path.join(tmp_dir, file_name)
        df.to_csv(local_path, index=False)
        logging.info(f"Saved CSV to: {local_path}")

        # Upload to GCS
        gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')
        gcs_hook.upload(
            bucket_name='mysql-to-gcs-bronze-layer',
            object_name=f"bronze_layer/{file_name}",
            filename=local_path
        )
        logging.info(f"Uploaded {file_name} to GCS bucket.")

    except Exception as e:
        logging.error(f"Error in extract_and_upload: {e}", exc_info=True)
        raise


with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['mysql', 'gcs'],
    max_active_runs=3,  # Allow multiple concurrent runs if needed
) as dag:

    extract_customers = PythonOperator(
        task_id='extract_customers',
        python_callable=extract_and_upload,
        op_kwargs={'table_name': 'customers'},
    )

    extract_support_logs = PythonOperator(
        task_id='extract_support_logs',
        python_callable=extract_and_upload,
        op_kwargs={'table_name': 'support_logs'},
    )

    extract_product_usage_logs = PythonOperator(
        task_id='extract_product_usage_logs',
        python_callable=extract_and_upload,
        op_kwargs={'table_name': 'product_usage_logs'},
    )

    extract_customers >> [extract_support_logs, extract_product_usage_logs]