from airflow import DAG
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime
import pandas as pd
import logging
import os
import tempfile
import re
from collections import defaultdict
from google.cloud import bigquery  # Required for dataset creation

# Set up basic logging
logging.basicConfig(level=logging.INFO)

DAG_ID = 'gcs_silver_to_golden_bigquery'

def silver_to_golden(**kwargs):
    try:
        # Generate timestamp for output filename
        execution_time = kwargs['ds_nodash'] + '_' + kwargs['execution_date'].strftime('%H%M%S')
        output_file_name = f"golden_data_{execution_time}.csv"
        logging.info(f"Starting transformation at {execution_time}")

        # Temporary directory for processing
        tmp_dir = tempfile.mkdtemp()
        logging.info(f"Created temporary directory: {tmp_dir}")

        # Initialize GCS Hook
        gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')

        # List all files in silver_layer/
        files = gcs_hook.list('mysql-to-gcs-bronze-layer', prefix='silver_layer/')
        if not files:
            raise FileNotFoundError("No files found in silver_layer/")
        logging.info(f"Found files in silver layer: {files}")

        # Extract timestamps and pick latest file
        pattern = re.compile(r"silver_layer/transformed_data_(\d{8}_\d{6})\.csv")
        valid_files = []

        for file in files:
            match = pattern.match(file)
            if match:
                timestamp = match.group(1)
                valid_files.append((file, timestamp))

        if not valid_files:
            raise FileNotFoundError("No valid transformed data files found in silver_layer/")

        # Pick latest file
        latest_file = max(valid_files, key=lambda x: x[1])[0]
        logging.info(f"Selected latest file: {latest_file}")

        # Download latest file
        local_silver_path = os.path.join(tmp_dir, os.path.basename(latest_file))
        gcs_hook.download(
            bucket_name='mysql-to-gcs-bronze-layer',
            object_name=latest_file,
            filename=local_silver_path
        )
        logging.info(f"Downloaded {latest_file} to {local_silver_path}")

        # Load DataFrame
        df = pd.read_csv(local_silver_path)

        # Apply transformation using your SQL-like logic
        golden_df = df.groupby(['customer_id']).agg(
            first_name=('first_name', 'first'),
            last_name=('last_name', 'first'),
            age=('age', 'first'),
            gender=('gender', 'first'),
            country=('country', 'first'),
            signup_date=('signup_date', 'first'),
            products_bought=('usage_id', 'nunique'),
            time_spent=('duration_mins', 'sum'),
            no_of_tickets_raised=('ticket_id', 'nunique'),
            resolution_time=('resolution_time_mins', 'sum')
        ).reset_index()

        # Save transformed data locally
        golden_df['signup_date'] = pd.to_datetime(golden_df['signup_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        golden_df['resolution_time'] = golden_df['resolution_time'].astype(float)  
        golden_df['time_spent'] = golden_df['time_spent'].astype(float)            
        transformed_local_path = os.path.join(tmp_dir, output_file_name)
        golden_df.to_csv(transformed_local_path, index=False)
        logging.info(f"Saved golden data to {transformed_local_path}")

        # Upload to golden_layer/
        gcs_hook.upload(
            bucket_name='mysql-to-gcs-bronze-layer',
            object_name=f"golden_layer/{output_file_name}",
            filename=transformed_local_path
        )
        logging.info(f"Uploaded {output_file_name} to golden_layer/")

        # BigQuery setup
        bq_hook = BigQueryHook(
            gcp_conn_id='google_cloud_default',
            use_legacy_sql=False
        )

        project_id = bq_hook.project_id
        dataset_id = 'golden_layer'
        table_id = 'golden_customer_summary'

        # Create dataset if not exists
        def create_bq_dataset_if_not_exists(dataset_id, project_id, bq_hook):
            client = bq_hook.get_client(project_id)
            dataset_ref = client.dataset(dataset_id)

            try:
                client.get_dataset(dataset_ref)
                logging.info(f"Dataset {dataset_id} already exists.")
            except:
                logging.info(f"Dataset {dataset_id} not found. Creating it...")
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"  # Change if needed
                dataset.description = "Golden Layer Dataset"
                client.create_dataset(dataset, timeout=30)
                logging.info(f"Created dataset {dataset_id}")

        create_bq_dataset_if_not_exists(dataset_id, project_id, bq_hook)

        uri = f"gs://mysql-to-gcs-bronze-layer/golden_layer/{output_file_name}"

        # Run load using old-style args supported by Airflow < 2.5
        bq_hook.run_load(
            destination_project_dataset_table=f"{dataset_id}.{table_id}",
            source_uris=[uri],
            schema_fields=[
                {'name': 'customer_id', 'type': 'INT64', 'mode': 'NULLABLE'},
                {'name': 'first_name', 'type': 'STRING', 'mode': 'NULLABLE'},
                {'name': 'last_name', 'type': 'STRING', 'mode': 'NULLABLE'},
                {'name': 'age', 'type': 'INT64', 'mode': 'NULLABLE'},
                {'name': 'gender', 'type': 'STRING', 'mode': 'NULLABLE'},
                {'name': 'country', 'type': 'STRING', 'mode': 'NULLABLE'},
                {'name': 'signup_date', 'type': 'DATE', 'mode': 'NULLABLE'},
                {'name': 'products_bought', 'type': 'INT64', 'mode': 'NULLABLE'},
                {'name': 'time_spent', 'type': 'FLOAT64', 'mode': 'NULLABLE'},
                {'name': 'no_of_tickets_raised', 'type': 'INT64', 'mode': 'NULLABLE'},
                {'name': 'resolution_time', 'type': 'FLOAT64', 'mode': 'NULLABLE'}
            ],
            source_format='CSV',
            write_disposition='WRITE_TRUNCATE',
            skip_leading_rows=1,
            create_disposition='CREATE_IF_NEEDED'
        )

        logging.info(f"Loaded data into BigQuery table {dataset_id}.{table_id}")

    except Exception as e:
        logging.error(f"Error during transformation or upload: {e}", exc_info=True)
        raise


with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['gcs', 'bigquery', 'transformation'],
    max_active_runs=1,
) as dag:

    wait_for_silver = ExternalTaskSensor(
        task_id='wait_for_silver',
        external_dag_id='gcs_bronze_to_silver',
        external_task_id='transform_and_upload',
        mode='reschedule',
        poke_interval=60,
        timeout=3600,
        retries=3,
        soft_fail=False,
        check_existence=True
    )

    transform_and_upload_golden = PythonOperator(
        task_id='transform_and_upload_golden',
        python_callable=silver_to_golden,
        provide_context=True,
    )

    wait_for_silver >> transform_and_upload_golden