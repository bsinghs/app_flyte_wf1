from flytekit import task, workflow, Resources, CronSchedule, LaunchPlan
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
from typing import Tuple
import logging
from config import CREDIT_SCORING_DATA_PATH


@task(requests=Resources(cpu="300m", mem="300Mi"), limits=Resources(cpu="500m", mem="500Mi"))
def load_prediction_data(data_path: str) -> pd.DataFrame:
    """Load new data for batch predictions"""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading prediction data from: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records for prediction")
    return df


@task(requests=Resources(cpu="200m", mem="200Mi"), limits=Resources(cpu="400m", mem="400Mi"))
def preprocess_for_prediction(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess data for prediction (same as training preprocessing)"""
    logger = logging.getLogger(__name__)
    
    # Remove rows with missing values
    df_clean = df.dropna()
    logger.info(f"After cleaning: {len(df_clean)} records")
    
    # If Status column exists (for validation), remove it
    if "Status" in df_clean.columns:
        df_clean = df_clean.drop("Status", axis=1)
        logger.info("Removed Status column for prediction")
    
    # Apply same encoding as training
    df_encoded = pd.get_dummies(df_clean)
    logger.info(f"Encoded features: {df_encoded.columns.tolist()}")
    
    return df_encoded


@task(requests=Resources(cpu="500m", mem="500Mi"), limits=Resources(cpu="800m", mem="800Mi"))
def train_model_for_predictions(training_data_path: str) -> RandomForestClassifier:
    """Train a model that will be used for batch predictions"""
    logger = logging.getLogger(__name__)
    
    # Load and prepare training data
    df = pd.read_csv(training_data_path)
    df_clean = df.dropna()
    
    if "Status" not in df_clean.columns:
        raise ValueError("Training data must contain 'Status' column")
    
    # Extract target
    y = df_clean.pop("Status")
    X = pd.get_dummies(df_clean)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    logger.info("Model trained successfully for batch predictions")
    return model


@task(requests=Resources(cpu="400m", mem="400Mi"), limits=Resources(cpu="600m", mem="600Mi"))
def make_batch_predictions(model: RandomForestClassifier, prediction_data: pd.DataFrame) -> pd.DataFrame:
    """Make predictions on batch data"""
    logger = logging.getLogger(__name__)
    
    # Make predictions
    predictions = model.predict(prediction_data)
    prediction_probabilities = model.predict_proba(prediction_data)
    
    # Create results dataframe
    results = pd.DataFrame({
        'prediction': predictions,
        'confidence_class_0': prediction_probabilities[:, 0],
        'confidence_class_1': prediction_probabilities[:, 1]
    })
    
    logger.info(f"Generated predictions for {len(results)} records")
    logger.info(f"Prediction distribution: {results['prediction'].value_counts().to_dict()}")
    
    return results


@task(requests=Resources(cpu="200m", mem="200Mi"), limits=Resources(cpu="300m", mem="300Mi"))
def save_predictions(predictions: pd.DataFrame, output_path: str) -> str:
    """Save predictions to file"""
    logger = logging.getLogger(__name__)
    
    # In a real scenario, you'd save to S3 or another storage system
    # For demo, we'll just return a summary
    summary = {
        "total_predictions": len(predictions),
        "positive_predictions": int((predictions['prediction'] == 1).sum()),
        "negative_predictions": int((predictions['prediction'] == 0).sum()),
        "average_confidence": float(predictions[['confidence_class_0', 'confidence_class_1']].max(axis=1).mean())
    }
    
    logger.info(f"Prediction Summary: {summary}")
    return f"Saved {len(predictions)} predictions. Summary: {summary}"


@workflow
def batch_prediction_workflow(prediction_data_path: str, training_data_path: str = CREDIT_SCORING_DATA_PATH) -> str:
    """
    Complete batch prediction workflow
    
    Args:
        prediction_data_path: Path to new data for predictions
        training_data_path: Path to training data (defaults to credit scoring data)
    
    Returns:
        Summary of prediction results
    """
    # Step 1: Train model on training data
    model = train_model_for_predictions(training_data_path=training_data_path)
    
    # Step 2: Load and preprocess new data for predictions
    prediction_data = load_prediction_data(data_path=prediction_data_path)
    preprocessed_data = preprocess_for_prediction(df=prediction_data)
    
    # Step 3: Make predictions
    predictions = make_batch_predictions(model=model, prediction_data=preprocessed_data)
    
    # Step 4: Save results
    output_path = f"predictions_{prediction_data_path.split('/')[-1]}"
    result_summary = save_predictions(predictions=predictions, output_path=output_path)
    
    return result_summary


@workflow 
def quick_prediction_workflow(data_path: str) -> str:
    """Simplified prediction workflow using credit scoring data for training"""
    return batch_prediction_workflow(prediction_data_path=data_path)


# Scheduled workflow that runs daily at 8 PM
@workflow
def daily_batch_prediction_workflow() -> str:
    """
    Workflow designed to run daily at 8 PM via scheduled launch plan
    
    This workflow will automatically run batch predictions using the 
    credit scoring dataset as both training and prediction data.
    In a real scenario, you'd point this to fresh daily data.
    """
    # Use the credit scoring data as prediction data for demo
    # In production, you'd typically have a daily data path like:
    # prediction_data_path = f"s3://bucket/daily-data/{datetime.now().strftime('%Y-%m-%d')}/data.csv"
    
    return batch_prediction_workflow(
        prediction_data_path=CREDIT_SCORING_DATA_PATH,
        training_data_path=CREDIT_SCORING_DATA_PATH
    )


# Create a scheduled launch plan for the workflow
daily_prediction_launch_plan = LaunchPlan.create(
    "daily_prediction_schedule",
    daily_batch_prediction_workflow,
    schedule=CronSchedule("0 20 * * ? *")  # 8 PM UTC daily
)


# Alternative: Parameterized scheduled workflow
@workflow
def daily_prediction_with_config(prediction_path: str = CREDIT_SCORING_DATA_PATH) -> str:
    """
    Scheduled workflow with configurable prediction data path
    
    This allows you to override the prediction data path when needed
    while still having a default scheduled behavior.
    """
    return batch_prediction_workflow(prediction_data_path=prediction_path)


# Create another scheduled launch plan with parameters
configurable_prediction_launch_plan = LaunchPlan.create(
    "configurable_daily_prediction",
    daily_prediction_with_config,
    schedule=CronSchedule("0 20 * * ? *"),  # 8 PM UTC daily
    default_inputs={"prediction_path": CREDIT_SCORING_DATA_PATH}
)
