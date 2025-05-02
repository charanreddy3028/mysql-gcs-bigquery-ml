from google.cloud import bigquery
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import joblib
from sklearn.metrics import accuracy_score
from google.cloud import bigquery

# Initialize BigQuery client
key_path = 'C:/Users/HP/airflow-docker/keys/gcp_key.json'
client = bigquery.Client.from_service_account_json(key_path)

# Query data
query = """
SELECT * FROM `bigquery-email-454109.golden_layer.golden_customer_summary`
"""
df = client.query(query).to_dataframe()

# Add random churn if not present
df['churn'] = np.random.randint(0, 2, size=len(df))

# Split features and target
X = df.drop('churn', axis=1)
y = df['churn']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Preprocessing and model pipeline
numerical_cols = X.select_dtypes(include=['number']).columns
categorical_cols = X.select_dtypes(include=['object']).columns

preprocessor = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler())
])

model = Pipeline(steps=[
    ('preprocessor', ColumnTransformer(transformers=[('num', preprocessor, numerical_cols)])),
    ('classifier', XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
])

# Train model
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2%}")

# Save model
joblib.dump(model, "churn_model.pkl")
print("✅ Model saved to churn_model.pkl")

# Upload predictions (optional)
X_test['predicted_churn'] = y_pred
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
table_id = "bigquery-email-454109.golden_layer.weekly_churn_predictions"
client.load_table_from_dataframe(X_test[['predicted_churn']], table_id, job_config=job_config)
print("✅ Predictions uploaded to BigQuery.")