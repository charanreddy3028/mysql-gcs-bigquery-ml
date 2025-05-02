from airflow import DAG
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime
import pandas as pd
import logging
import os
import tempfile
import re
from collections import defaultdict

# Set up basic logging
logging.basicConfig(level=logging.INFO)

DAG_ID = 'gcs_bronze_to_silver'

def bronze_to_silver(**kwargs):
    try:
        # Generate timestamp for output filename
        execution_time = kwargs['ds_nodash'] + '_' + kwargs['execution_date'].strftime('%H%M%S')
        output_file_name = f"transformed_data_{execution_time}.csv"
        logging.info(f"Starting transformation at {execution_time}")

        # Temporary directory for processing
        tmp_dir = tempfile.mkdtemp()
        logging.info(f"Created temporary directory: {tmp_dir}")

        # Initialize GCS Hook
        gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')

        # List all files in bronze_layer/
        files = gcs_hook.list('mysql-to-gcs-bronze-layer', prefix='bronze_layer/')
        if not files:
            raise FileNotFoundError("No files found in bronze_layer/")
        logging.info(f"Found files in bronze layer: {files}")

        # Group files by table name and select the latest one
        table_files = defaultdict(list)
        pattern = re.compile(r"bronze_layer/([a-zA-Z0-9_]+)_data_(\d{8}_\d{6})\.csv")

        for file in files:
            match = pattern.match(file)
            if match:
                table_name = match.group(1)
                timestamp = match.group(2)
                table_files[table_name].append((file, timestamp))

        # Keep only the latest file per table
        latest_files = {}
        for table, file_list in table_files.items():
            latest_file = max(file_list, key=lambda x: x[1])  # sort by timestamp
            latest_files[table] = latest_file[0]

        if len(latest_files) < 3:
            missing_tables = set(['customers', 'product_usage_logs', 'support_logs']) - set(latest_files.keys())
            raise FileNotFoundError(f"Missing required tables in bronze layer: {missing_tables}")

        logging.info(f"Latest files selected per table: {latest_files}")

        # Download the latest files
        local_files = {}
        for table, file_path in latest_files.items():
            local_path = os.path.join(tmp_dir, os.path.basename(file_path))
            gcs_hook.download(
                bucket_name='mysql-to-gcs-bronze-layer',
                object_name=file_path,
                filename=local_path
            )
            logging.info(f"Downloaded {file_path} to {local_path}")
            local_files[table] = local_path

        # Load DataFrames
        df_customers = pd.read_csv(local_files['customers'])
        df_products = pd.read_csv(local_files['product_usage_logs'])
        df_support = pd.read_csv(local_files['support_logs'])

        # Join customers with product usage logs
        joined_df = pd.merge(df_customers, df_products, on='customer_id', how='left')

        # Join result with support logs
        joined_df = pd.merge(joined_df, df_support, on='customer_id', how='left')

        # Remove duplicate customer_id columns
        cols = [col for col in joined_df.columns if col != 'customer_id' or col == 'customer_id']
        final_columns = []
        seen = False
        for col in cols:
            if col == 'customer_id':
                if not seen:
                    seen = True
                    final_columns.append(col)
            else:
                final_columns.append(col)
        joined_df = joined_df[final_columns]

        # Save transformed DataFrame locally
        transformed_local_path = os.path.join(tmp_dir, output_file_name)
        joined_df.to_csv(transformed_local_path, index=False)
        logging.info(f"Saved transformed data to {transformed_local_path}")

        # Upload to silver_layer/
        gcs_hook.upload(
            bucket_name='mysql-to-gcs-bronze-layer',
            object_name=f"silver_layer/{output_file_name}",
            filename=transformed_local_path
        )
        logging.info(f"Uploaded {output_file_name} to silver_layer/")

    except Exception as e:
        logging.error(f"Error during transformation: {e}", exc_info=True)
        raise


with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['gcs', 'transformation'],
    max_active_runs=1,
) as dag:

    wait_for_mysql_to_gcs = ExternalTaskSensor(
        task_id='wait_for_mysql_to_gcs',
        external_dag_id='mysql_to_gcs',
        external_task_id='extract_product_usage_logs',
        mode='reschedule',
        poke_interval=60,
        timeout=3600,
        retries=3,
        soft_fail=False,
        execution_delta=None,
        check_existence=True
    )

    transform_and_upload = PythonOperator(
        task_id='transform_and_upload',
        python_callable=bronze_to_silver,
        provide_context=True,
    )

    wait_for_mysql_to_gcs >> transform_and_upload