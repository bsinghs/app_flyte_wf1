from flytekit import task, workflow, Resources
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import logging
import os
from typing import Tuple
from config import CREDIT_SCORING_DATA_PATH


@task(requests=Resources(cpu="500m", mem="500Mi"), limits=Resources(cpu="1", mem="1Gi"))
def load_data(path: str) -> pd.DataFrame:
    """Load data from S3 path"""
    return pd.read_csv(path)


@task(requests=Resources(cpu="200m", mem="200Mi"), limits=Resources(cpu="500m", mem="500Mi"))
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the dataset by removing null values"""
    df = df.dropna()
    return df


@task(requests=Resources(cpu="300m", mem="300Mi"), limits=Resources(cpu="500m", mem="500Mi"))
def features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract features and target variable"""
    if "Status" not in df.columns:
        raise ValueError("Expected column 'Status' not found in data")

    # Extract target column
    y = df.pop("Status")

    # Automatically encode all categorical columns using get_dummies
    df_encoded = pd.get_dummies(df)

    logger = logging.getLogger(__name__)
    logger.info(f"Encoded columns: {df_encoded.columns.tolist()}")

    return df_encoded, y


@task(requests=Resources(cpu="800m", mem="800Mi"), limits=Resources(cpu="1", mem="1Gi"))
def train_model(df: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """Train a Random Forest model"""
    X_train, X_test, y_train, y_test = train_test_split(df, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    return model


@task(requests=Resources(cpu="200m", mem="200Mi"), limits=Resources(cpu="500m", mem="500Mi"))
def evaluate_model(model: RandomForestClassifier, df: pd.DataFrame, y: pd.Series) -> float:
    """Evaluate model performance"""
    X_train, X_test, y_train, y_test = train_test_split(df, y, test_size=0.2, random_state=42)
    preds = model.predict(X_test)
    return float(accuracy_score(y_test, preds))


@workflow
def credit_scoring_pipeline() -> float:
    """Credit scoring ML pipeline using configured data path"""
    df = load_data(path=CREDIT_SCORING_DATA_PATH)
    df_clean = clean_data(df=df)
    df_feat, y = features(df=df_clean)
    model = train_model(df=df_feat, y=y)
    acc = evaluate_model(model=model, df=df_feat, y=y)
    return acc


@workflow
def generic_ml_pipeline(data_path: str) -> float:
    """Generic ML pipeline that can work with any dataset path"""
    df = load_data(path=data_path)
    df_clean = clean_data(df=df)
    df_feat, y = features(df=df_clean)
    model = train_model(df=df_feat, y=y)
    acc = evaluate_model(model=model, df=df_feat, y=y)
    return acc
