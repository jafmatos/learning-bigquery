from reading_sql.config import PROJECT_ID
from reading_sql.config import GOOGLE_APPLICATION_CREDENTIALS_PATH
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS_PATH)

bigquery_client = bigquery.Client(project=PROJECT_ID)

query = """
SELECT 
    id as user_id
FROM `bigquery-public-data.thelook_ecommerce.users`
TABLESAMPLE SYSTEM (0.00001 PERCENT);
"""


dataframe = bigquery_client.query(query).to_dataframe()

load_job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",
    autodetect=True
)

load_job = bigquery_client.load_table_from_dataframe(dataframe, f"{PROJECT_ID}.meu_dataset.nova_tabela3", job_config=load_job_config)

print("Acabou")