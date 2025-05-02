from google.cloud import bigquery
import pandas as pd
import joblib
import os

# Set path to GCP key (set in DAG or environment)
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

def predict_churn():
    # Initialize BigQuery client
    client = bigquery.Client.from_service_account_json(KEY_PATH)

    print("✅ BigQuery client initialized")

    # Query latest customer data
    query = """
    SELECT * FROM `bigquery-email-454109.golden_layer.golden_customer_summary`
    """
    df = client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} rows from BigQuery")

    # Load model
    model = joblib.load("churn_model.pkl")
    print("✅ Model loaded")

    # Make predictions
    X = df  # Assuming all columns are features
    df['predicted_churn'] = model.predict(X)

    # Upload results back to BigQuery
    table_id = "bigquery-email-454109.golden_layer.weekly_churn_predictions"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    client.load_table_from_dataframe(df[['predicted_churn']], table_id, job_config=job_config)
    print("✅ Predictions uploaded to BigQuery")

if __name__ == "__main__":
    predict_churn()