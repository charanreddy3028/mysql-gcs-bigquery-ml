import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import random

np.random.seed(42)

# 5,000 customers
n_customers = 5000
customer_ids = list(range(1, n_customers + 1))

# 1. Customers Table
customers = pd.DataFrame({
    'customer_id': customer_ids,
    'first_name': np.random.choice(['John', 'Jane', 'Alex', 'Alice', 'Bob', 'Emily'], n_customers),
    'last_name': np.random.choice(['Smith', 'Doe', 'Brown', 'Davis', 'Miller', 'Wilson'], n_customers),
    'age': np.random.randint(18, 65, n_customers),
    'gender': np.random.choice(['Male', 'Female'], n_customers),
    'country': np.random.choice(['USA', 'India', 'UK', 'Canada', 'Germany'], n_customers),
    'signup_date': pd.to_datetime('2020-01-01') + pd.to_timedelta(np.random.randint(0, 1000, n_customers), unit='D')
})

# 2. Support Logs (15,000 records)
support_logs = []
issue_types = ['Login Issue', 'Payment Failed', 'Bug Report', 'Feature Request', 'Account Hacked']
ticket_id = 1

for cid in customer_ids:
    num_tickets = np.random.randint(1, 5)  # 1–4 tickets per customer
    for _ in range(num_tickets):
        support_logs.append({
            'ticket_id': ticket_id,
            'customer_id': cid,
            'ticket_date': customers.loc[customers.customer_id == cid, 'signup_date'].values[0] + 
                           np.random.randint(1, 1000) * np.timedelta64(1, 'D'),
            'issue_type': random.choice(issue_types),
            'resolution_time_mins': np.random.randint(10, 120)
        })
        ticket_id += 1

support_logs_df = pd.DataFrame(support_logs)

# 3. Product Usage Logs (15,000 records)
product_usage_logs = []
product_types = ['Mobile App', 'Web App', 'Email', 'API', 'Dashboard']
usage_id = 1

for cid in customer_ids:
    num_logs = np.random.randint(2, 4)  # 2–3 usage events per customer
    for _ in range(num_logs):
        product_usage_logs.append({
            'usage_id': usage_id,
            'customer_id': cid,
            'usage_date': customers.loc[customers.customer_id == cid, 'signup_date'].values[0] + 
                          np.random.randint(1, 1000) * np.timedelta64(1, 'D'),
            'product_type': random.choice(product_types),
            'duration_mins': round(np.random.uniform(1, 90), 2)
        })
        usage_id += 1

product_usage_df = pd.DataFrame(product_usage_logs)

# # MySQL connection settings
# MYSQL_USER = 'root'
# MYSQL_PASSWORD = 'Charan@0897'  
# MYSQL_HOST = 'localhost'
# MYSQL_PORT = '3306'
# MYSQL_DB = 'customer_data'

# # Insert into MySQL
# engine = create_engine(f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}')

engine = create_engine("mysql+pymysql://root:Charan%400897@localhost:3306/customer_data")



customers.to_sql('customers', con=engine, index=False, if_exists='replace')
support_logs_df.to_sql('support_logs', con=engine, index=False, if_exists='replace')
product_usage_df.to_sql('product_usage_logs', con=engine, index=False, if_exists='replace')

print("✅ Log data inserted into MySQL.")
