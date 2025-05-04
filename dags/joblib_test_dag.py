from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import joblib
import numpy as np

# Add user site-packages to PYTHONPATH if needed
sys.path.append('/home/airflow/.local/lib/python3.8/site-packages')

MODEL_PATH = '/opt/airflow/models/my_model.joblib'

def load_and_predict(**kwargs):
    try:
        # Load model
        model = joblib.load(MODEL_PATH)
        print("✅ Model loaded successfully!")

        # Example input (replace with real logic)
        input_data = np.array([[5.1, 3.5, 1.4, 0.2]])  # dummy input
        prediction = model.predict(input_data)

        print(f"🔢 Prediction: {prediction}")
        
        # Push result to XCom for downstream tasks (optional)
        kwargs['ti'].xcom_push(key='prediction', value=str(prediction))

    except Exception as e:
        raise RuntimeError(f"❌ Failed to load or run model: {str(e)}")

with DAG(
    dag_id='run_model_prediction',
    start_date=datetime(2025, 1, 1),
    schedule='@once',
    catchup=False
) as dag:

    predict_task = PythonOperator(
        task_id='load_and_predict',
        python_callable=load_and_predict,
        provide_context=True
    )