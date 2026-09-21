import joblib
from sklearn.metrics import classification_report
from reading_sql.config import MODEL_PATH
from reading_sql.data import X_test
from reading_sql.data import y_test

model = joblib.load(MODEL_PATH)

y_pred = model.predict(X_test)

print(f"""
Classification Report
{classification_report(y_test, y_pred)}
""")

