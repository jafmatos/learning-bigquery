import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS_PATH = ROOT_DIR / os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
SNAPSHOTS_PATH = ROOT_DIR / "snapshots"
SQL_PATH = ROOT_DIR / "sql"
DATA_PATH = SNAPSHOTS_PATH / "churn-query.parquet"
MODEL_PATH = ROOT_DIR / "models" / "churn-predictor.joblib"

NUMERICAL_FEATURES = [
    "idade",
    "total_pedidos",
    "receita_total",
    "ticket_medio",
    "itens_devolvidos",
    "tempo_relacionamento_dias",
    "recencia_dias",
]

CATEGORICAL_FEATURES = [
    "genero",
    "pais",
    "canal_aquisicao",
]

TARGET_FEATURE = "churn"

TEST_SIZE=0.2
RANDOM_STATE=42