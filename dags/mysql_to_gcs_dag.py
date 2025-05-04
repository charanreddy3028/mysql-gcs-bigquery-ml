from airflow import DAG
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG level

DAG_ID = 'mysql_to_gcs'

def extract_and_upload(table_name, **kwargs):
    try:
        logging.debug(f"[START] Task for table: {table_name}")

        # Use execution_date to generate a short timestamp
        execution_time = kwargs['ds_nodash'] + '_' + kwargs['execution_date'].strftime('%H%M%S')
        logging.info(f"Starting extraction for table: {table_name}, timestamp: {execution_time}")

        # Step 1: Connect to PostgreSQL
        logging.debug("[CONNECTING] To PostgreSQL database...")
        pg_hook = PostgresHook(postgres_conn_id='postgres_customer_data')
        conn = pg_hook.get_conn()
        logging.debug("[CONNECTION SUCCESS] PostgreSQL connection established.")

        # Step 2: Query data
        logging.debug(f"[QUERYING] Data from table: {table_name}")
        sql = f"SELECT * FROM {table_name}"
        df = pg_hook.get_pandas_df(sql)
        logging.info(f"[QUERY SUCCESS] Retrieved {len(df)} rows from table '{table_name}'")

        # Step 3: Save to local CSV
        tmp_dir = '/tmp/postgres_extract'
        logging.debug(f"[SAVING FILE] Preparing directory: {tmp_dir}")
        os.makedirs(tmp_dir, exist_ok=True)

        file_name = f"{table_name}_data_{execution_time}.csv"
        local_path = os.path.join(tmp_dir, file_name)
        logging.debug(f"[WRITING CSV] Saving to: {local_path}")
        df.to_csv(local_path, index=False)
        logging.info(f"[CSV SAVED] File saved at: {local_path}")

        # Step 4: Upload to GCS
        logging.debug("[UPLOADING TO GCS] Starting upload process...")
        gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')
        gcs_hook.upload(
            bucket_name='mysql-to-gcs-bronze-layer',
            object_name=f"bronze_layer/{file_name}",
            filename=local_path
        )
        logging.info(f"[UPLOAD SUCCESS] Uploaded {file_name} to GCS bucket.")

        # Clean up (optional)
        os.remove(local_path)
        logging.debug(f"[CLEANUP] Temporary file removed: {local_path}")

        logging.debug(f"[END] Successfully completed task for table: {table_name}")

    except Exception as e:
        logging.error(f"[ERROR] Error occurred in extract_and_upload: {str(e)}", exc_info=True)
        raise


with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['postgres', 'gcs'],
    max_active_runs=3,
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