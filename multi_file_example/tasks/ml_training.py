from flytekit import task, Resources
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from typing import Tuple
import logging

@task(requests=Resources(cpu="500m", mem="500Mi"), limits=Resources(cpu="800m", mem="800Mi"))
def train_model(df: pd.DataFrame, target_column: str) -> RandomForestClassifier:
    """Train a Random Forest model"""
    logger = logging.getLogger(__name__)
    
    # Separate features and target
    y = df[target_column]
    X = df.drop(target_column, axis=1)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    logger.info("Model trained successfully")
    return model

@task(requests=Resources(cpu="400m", mem="400Mi"), limits=Resources(cpu="600m", mem="600Mi"))
def evaluate_model(model: RandomForestClassifier, test_data: pd.DataFrame, target_column: str) -> dict:
    """Evaluate model performance"""
    logger = logging.getLogger(__name__)
    
    # Separate features and target
    y_test = test_data[target_column]
    X_test = test_data.drop(target_column, axis=1)
    
    # Make predictions
    predictions = model.predict(X_test)
    accuracy = (predictions == y_test).mean()
    
    results = {
        "accuracy": float(accuracy),
        "total_samples": len(y_test)
    }
    
    logger.info(f"Model evaluation: {results}")
    return results

@task(requests=Resources(cpu="300m", mem="300Mi"), limits=Resources(cpu="500m", mem="500Mi"))
def make_predictions(model: RandomForestClassifier, data: pd.DataFrame) -> pd.DataFrame:
    """Make predictions on new data"""
    logger = logging.getLogger(__name__)
    
    predictions = model.predict(data)
    prediction_probs = model.predict_proba(data)
    
    # Create results dataframe
    results = pd.DataFrame({
        'prediction': predictions,
        'confidence': prediction_probs.max(axis=1)
    })
    
    logger.info(f"Generated predictions for {len(results)} records")
    return results
