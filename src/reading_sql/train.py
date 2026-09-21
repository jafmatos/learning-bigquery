import joblib
from reading_sql.config import MODEL_PATH
from reading_sql.pipeline import pipeline
from reading_sql.data import X_train, y_train

def train_and_save_model():
    pipeline.fit(X_train, y_train)

    joblib.dump(pipeline, MODEL_PATH)

if __name__ == "__main__":
    train_and_save_model()