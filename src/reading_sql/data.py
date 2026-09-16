from reading_sql.config import PROJECT_ID
from reading_sql.config import GOOGLE_APPLICATION_CREDENTIALS_PATH
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS_PATH)

bigquery_client = bigquery.Client(project=PROJECT_ID)

query = """
    SELECT 
        id AS user_id,
        age,
        gender,
        country,
        traffic_source,
        created_at
    FROM `bigquery-public-data.thelook_ecommerce.users`
    WHERE country = 'Brasil'
    LIMIT 500
;
"""

df_sales = bigquery_client.query(query).to_dataframe()

print(df_sales.head())