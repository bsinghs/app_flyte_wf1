from flytekit import workflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Import tasks from other modules
from tasks.data_processing import load_data, clean_data, encode_features
from tasks.ml_training import train_model, evaluate_model, make_predictions

@workflow
def training_workflow(data_path: str, target_column: str) -> dict:
    """
    Complete ML training workflow using tasks from multiple files
    
    Args:
        data_path: Path to training data
        target_column: Name of the target column
    
    Returns:
        Model evaluation results
    """
    # Data processing pipeline
    raw_data = load_data(data_path=data_path)
    clean_data_result = clean_data(df=raw_data)
    encoded_data = encode_features(df=clean_data_result)
    
    # ML pipeline
    trained_model = train_model(df=encoded_data, target_column=target_column)
    evaluation_results = evaluate_model(
        model=trained_model, 
        test_data=encoded_data, 
        target_column=target_column
    )
    
    return evaluation_results

@workflow 
def prediction_workflow(
    training_data_path: str, 
    prediction_data_path: str, 
    target_column: str
) -> pd.DataFrame:
    """
    Complete prediction workflow using tasks from multiple files
    
    Args:
        training_data_path: Path to training data
        prediction_data_path: Path to data for predictions  
        target_column: Name of the target column
    
    Returns:
        Prediction results
    """
    # Train model on training data
    training_data = load_data(data_path=training_data_path)
    clean_training = clean_data(df=training_data)
    encoded_training = encode_features(df=clean_training)
    trained_model = train_model(df=encoded_training, target_column=target_column)
    
    # Process prediction data
    prediction_data = load_data(data_path=prediction_data_path)
    clean_prediction = clean_data(df=prediction_data)
    encoded_prediction = encode_features(df=clean_prediction)
    
    # Make predictions
    predictions = make_predictions(model=trained_model, data=encoded_prediction)
    
    return predictions
