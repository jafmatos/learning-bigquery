import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS_PATH = ROOT_DIR / os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
SNAPSHOTS_PATH = ROOT_DIR / "snapshots"