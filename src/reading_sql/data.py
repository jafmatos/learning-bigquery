from reading_sql.config import TARGET_FEATURE
from reading_sql.config import NUMERICAL_FEATURES
from reading_sql.config import CATEGORICAL_FEATURES
from sklearn.model_selection import train_test_split
from reading_sql.config import RANDOM_STATE
from reading_sql.config import TEST_SIZE
from reading_sql.config import SQL_PATH
import os
import pandas
from reading_sql.config import SNAPSHOTS_PATH
from reading_sql.config import PROJECT_ID
from reading_sql.config import GOOGLE_APPLICATION_CREDENTIALS_PATH
from google.cloud import bigquery

def generate_parquet_snapshot_from_bigquery():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS_PATH)

    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("reference_date", "DATE", "2026-01-01")
        ]
    )

    query = SQL_PATH / "churn_features.sql"

    dataframe = client.query(query.read_text(encoding="utf-8"), job_config=job_config).to_dataframe()
    dataframe.to_parquet(SNAPSHOTS_PATH / "churn-query.parquet", index=False)

if __name__ == "__main__":
    generate_parquet_snapshot_from_bigquery()

dataframe = pandas.read_parquet(SNAPSHOTS_PATH / "churn-query.parquet")

X = dataframe[CATEGORICAL_FEATURES + NUMERICAL_FEATURES]
y = dataframe[TARGET_FEATURE]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)