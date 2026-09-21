import numpy
from sklearn.preprocessing import FunctionTransformer
from pandas import DataFrame
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from reading_sql.config import RANDOM_STATE
from reading_sql.config import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, TARGET_FEATURE

def feature_engineering(dataframe: DataFrame):
    dataframe = dataframe.copy()
    
    dataframe["media_dias_entre_pedidos"] = dataframe["tempo_relacionamento_dias"] / dataframe["total_pedidos"]
    dataframe["razao_recencia_dias_entre_pedidos"] = dataframe["recencia_dias"] / dataframe["media_dias_entre_pedidos"]
    dataframe.replace([numpy.inf, -numpy.inf], 0, inplace=True)
    
    return dataframe

FeatureEngineeringTransformer = FunctionTransformer(feature_engineering)

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ("num", "passthrough", NUMERICAL_FEATURES),
    ],
    remainder="passthrough"
)

pipeline = Pipeline(
    steps=[
        ("feature_engineering", FeatureEngineeringTransformer),
        ("preprocessing", preprocessor),
        ("model", RandomForestClassifier(random_state=RANDOM_STATE, class_weight="balanced"))        
    ]
)
