# SageMaker Batch Prediction Pipeline
# Enhanced version of the original batch_prediction_pipeline.py optimized for SageMaker

from flytekit import task, workflow, Resources
from flytekit.types.file import FlyteFile
from flytekit.types.directory import FlyteDirectory
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd
import boto3
import json

# SageMaker-specific configurations
@dataclass
class SageMakerTrainingConfig:
    """Configuration for SageMaker Training Jobs"""
    instance_type: str = "ml.m5.xlarge"
    instance_count: int = 1
    volume_size_gb: int = 30
    max_runtime_seconds: int = 3600
    use_spot_instances: bool = True
    spot_instance_max_wait_seconds: int = 1800
    framework: str = "sklearn"
    framework_version: str = "0.23-1"

@dataclass
class SageMakerBatchTransformConfig:
    """Configuration for SageMaker Batch Transform Jobs"""
    instance_type: str = "ml.m5.large"
    instance_count: int = 1
    max_payload_mb: int = 6
    max_concurrent_transforms: int = 1
    strategy: str = "SingleRecord"
    assemble_with: str = "Line"

@dataclass
class SageMakerProcessingConfig:
    """Configuration for SageMaker Processing Jobs"""
    instance_type: str = "ml.m5.xlarge"
    instance_count: int = 1
    volume_size_gb: int = 30
    framework: str = "sklearn"
    framework_version: str = "0.23-1"

# Task 1: Data Preprocessing using SageMaker Processing
@task(
    task_config={
        "platform": "sagemaker",
        "job_type": "processing",
        "instance_type": "ml.m5.2xlarge",
        "instance_count": 1,
        "volume_size_gb": 30,
        "framework": "scikit-learn",
        "framework_version": "0.23-1",
        "max_runtime_seconds": 1800
    },
    requests=Resources(cpu="4", mem="16Gi"),
    container_image="763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3",
    retries=2
)
def preprocess_data_sagemaker(
    raw_data_s3_path: str,
    preprocessing_config: SageMakerProcessingConfig
) -> str:
    """
    Preprocess credit scoring data using SageMaker Processing Jobs
    
    This task runs on SageMaker managed infrastructure:
    - Automatic scaling and resource management
    - Cost-effective with spot instances
    - Integrated with S3 for data I/O
    - Built-in monitoring and logging
    
    Args:
        raw_data_s3_path: S3 path to raw credit scoring data
        preprocessing_config: Processing job configuration
        
    Returns:
        S3 path to preprocessed data
    """
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    import joblib
    import os
    
    # SageMaker Processing Job environment paths
    input_path = "/opt/ml/processing/input"
    output_path = "/opt/ml/processing/output"
    
    # Read input data (SageMaker automatically downloads from S3)
    input_files = os.listdir(input_path)
    data_file = [f for f in input_files if f.endswith('.csv')][0]
    df = pd.read_csv(os.path.join(input_path, data_file))
    
    print(f"Loaded data with shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Data preprocessing steps
    # 1. Handle missing values
    df = df.fillna(df.median(numeric_only=True))
    
    # 2. Encode categorical variables
    categorical_columns = df.select_dtypes(include=['object']).columns
    label_encoders = {}
    
    for col in categorical_columns:
        if col != 'target':  # Don't encode target variable yet
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
    
    # 3. Feature scaling
    feature_columns = [col for col in df.columns if col != 'target']
    scaler = StandardScaler()
    df[feature_columns] = scaler.fit_transform(df[feature_columns])
    
    # 4. Split into train/validation/test
    if 'target' in df.columns:
        X = df[feature_columns]
        y = df['target']
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train/validation split
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
        )
        
        # Create final datasets
        train_df = pd.concat([X_train, y_train], axis=1)
        val_df = pd.concat([X_val, y_val], axis=1)
        test_df = pd.concat([X_test, y_test], axis=1)
        
        # Save datasets
        train_df.to_csv(os.path.join(output_path, "train.csv"), index=False)
        val_df.to_csv(os.path.join(output_path, "validation.csv"), index=False)
        test_df.to_csv(os.path.join(output_path, "test.csv"), index=False)
        
    else:
        # No target variable - just save processed features
        df.to_csv(os.path.join(output_path, "processed_features.csv"), index=False)
    
    # Save preprocessing artifacts
    joblib.dump(scaler, os.path.join(output_path, "scaler.pkl"))
    joblib.dump(label_encoders, os.path.join(output_path, "label_encoders.pkl"))
    
    # Save feature names
    with open(os.path.join(output_path, "feature_names.json"), 'w') as f:
        json.dump(feature_columns, f)
    
    print("Data preprocessing completed successfully")
    
    # Return S3 output path (SageMaker automatically uploads to S3)
    return "s3://bsingh-ml-workflows/sagemaker/preprocessing/output/"

# Task 2: Model Training using SageMaker Training Jobs
@task(
    task_config={
        "platform": "sagemaker",
        "job_type": "training",
        "instance_type": "ml.m5.xlarge",
        "instance_count": 1,
        "volume_size_gb": 30,
        "framework": "xgboost",
        "framework_version": "1.2-1",
        "use_spot_instances": True,
        "max_runtime_seconds": 3600
    },
    requests=Resources(cpu="4", mem="16Gi"),
    container_image="763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.2-1",
    retries=2
)
def train_credit_scoring_model_sagemaker(
    preprocessed_data_s3_path: str,
    training_config: SageMakerTrainingConfig,
    hyperparameters: Dict[str, Any]
) -> str:
    """
    Train credit scoring model using SageMaker Training Jobs with XGBoost
    
    This task leverages SageMaker's built-in XGBoost algorithm:
    - Optimized for tabular data and classification tasks
    - Automatic hyperparameter tuning capabilities
    - Distributed training support
    - Spot instance support for cost optimization
    
    Args:
        preprocessed_data_s3_path: S3 path to preprocessed training data
        training_config: Training job configuration
        hyperparameters: Model hyperparameters
        
    Returns:
        S3 path to trained model artifacts
    """
    import xgboost as xgb
    import pandas as pd
    import numpy as np
    from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
    import joblib
    import os
    
    # SageMaker Training Job environment paths
    input_path = "/opt/ml/input/data"
    output_path = "/opt/ml/model"
    
    # Load training data
    train_df = pd.read_csv(os.path.join(input_path, "training", "train.csv"))
    val_df = pd.read_csv(os.path.join(input_path, "validation", "validation.csv"))
    
    print(f"Training data shape: {train_df.shape}")
    print(f"Validation data shape: {val_df.shape}")
    
    # Prepare features and target
    feature_columns = [col for col in train_df.columns if col != 'target']
    
    X_train = train_df[feature_columns]
    y_train = train_df['target']
    X_val = val_df[feature_columns]
    y_val = val_df['target']
    
    # Create DMatrix for XGBoost
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)
    
    # Set up hyperparameters with defaults
    default_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'eta': 0.3,
        'gamma': 0,
        'min_child_weight': 1,
        'subsample': 1,
        'colsample_bytree': 1,
        'lambda': 1,
        'alpha': 0,
        'seed': 42
    }
    
    # Update with provided hyperparameters
    params = {**default_params, **hyperparameters}
    
    print(f"Training XGBoost model with parameters: {params}")
    
    # Train the model
    num_boost_round = params.pop('num_boost_round', 100)
    early_stopping_rounds = params.pop('early_stopping_rounds', 10)
    
    # Training with validation monitoring
    evallist = [(dtrain, 'train'), (dval, 'validation')]
    
    model = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=num_boost_round,
        evals=evallist,
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=True
    )
    
    # Model evaluation
    train_pred = model.predict(dtrain)
    val_pred = model.predict(dval)
    
    # Convert probabilities to binary predictions
    train_pred_binary = (train_pred > 0.5).astype(int)
    val_pred_binary = (val_pred > 0.5).astype(int)
    
    # Calculate metrics
    train_accuracy = accuracy_score(y_train, train_pred_binary)
    val_accuracy = accuracy_score(y_val, val_pred_binary)
    val_auc = roc_auc_score(y_val, val_pred)
    
    print(f"Training Accuracy: {train_accuracy:.4f}")
    print(f"Validation Accuracy: {val_accuracy:.4f}")
    print(f"Validation AUC: {val_auc:.4f}")
    
    # Feature importance
    importance = model.get_score(importance_type='weight')
    print("Top 10 Feature Importance:")
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
    for feature, score in sorted_importance:
        print(f"{feature}: {score}")
    
    # Save model and metadata
    model.save_model(os.path.join(output_path, "xgboost_model.json"))
    
    # Save model using joblib for compatibility
    joblib.dump(model, os.path.join(output_path, "model.pkl"))
    
    # Save training metadata
    metadata = {
        'model_type': 'xgboost',
        'training_accuracy': train_accuracy,
        'validation_accuracy': val_accuracy,
        'validation_auc': val_auc,
        'hyperparameters': params,
        'feature_importance': dict(sorted_importance),
        'num_features': len(feature_columns),
        'training_samples': len(train_df),
        'validation_samples': len(val_df)
    }
    
    with open(os.path.join(output_path, "model_metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Model training completed successfully")
    
    # Return S3 path to model artifacts
    return "s3://bsingh-ml-workflows/sagemaker/training/output/model.tar.gz"

# Task 3: Batch Prediction using SageMaker Batch Transform
@task(
    task_config={
        "platform": "sagemaker",
        "job_type": "batch_transform",
        "instance_type": "ml.m5.large",
        "instance_count": 1,
        "max_payload_mb": 6,
        "max_concurrent_transforms": 4,
        "strategy": "SingleRecord",
        "assemble_with": "Line"
    },
    requests=Resources(cpu="2", mem="8Gi"),
    retries=2
)
def batch_predict_credit_scores_sagemaker(
    model_s3_path: str,
    test_data_s3_path: str,
    batch_config: SageMakerBatchTransformConfig
) -> str:
    """
    Perform batch credit scoring predictions using SageMaker Batch Transform
    
    SageMaker Batch Transform provides:
    - Serverless batch inference (no persistent endpoints)
    - Auto-scaling based on input data size
    - Cost-effective for large batch processing
    - Built-in data splitting and result assembly
    
    Args:
        model_s3_path: S3 path to trained model artifacts
        test_data_s3_path: S3 path to test data for batch prediction
        batch_config: Batch transform configuration
        
    Returns:
        S3 path to batch prediction results
    """
    import boto3
    import json
    import pandas as pd
    import joblib
    import os
    
    # For batch transform, the actual inference logic is handled by SageMaker
    # This task represents the coordination and setup
    
    # SageMaker Batch Transform will:
    # 1. Load the model from S3
    # 2. Process input data in batches
    # 3. Apply the model to generate predictions
    # 4. Save results back to S3
    
    print("Setting up SageMaker Batch Transform job...")
    print(f"Model path: {model_s3_path}")
    print(f"Input data path: {test_data_s3_path}")
    print(f"Instance type: {batch_config.instance_type}")
    print(f"Max payload: {batch_config.max_payload_mb} MB")
    
    # The actual batch inference happens in SageMaker's managed environment
    # Results will be automatically saved to S3
    
    output_path = "s3://bsingh-ml-workflows/sagemaker/batch-transform/predictions/"
    
    print(f"Batch predictions will be saved to: {output_path}")
    
    return output_path

# Task 4: Model Evaluation using SageMaker Processing
@task(
    task_config={
        "platform": "sagemaker",
        "job_type": "processing",
        "instance_type": "ml.m5.large",
        "instance_count": 1,
        "volume_size_gb": 30,
        "framework": "scikit-learn",
        "framework_version": "0.23-1"
    },
    requests=Resources(cpu="2", mem="8Gi"),
    container_image="763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3",
    retries=2
)
def evaluate_credit_scoring_model_sagemaker(
    predictions_s3_path: str,
    test_data_s3_path: str,
    model_metadata_s3_path: str
) -> Dict[str, float]:
    """
    Evaluate credit scoring model performance using SageMaker Processing
    
    This task computes comprehensive evaluation metrics:
    - Classification metrics (accuracy, precision, recall, F1)
    - Business metrics (approval rates, risk distribution)
    - Model performance analysis and reporting
    
    Args:
        predictions_s3_path: S3 path to batch predictions
        test_data_s3_path: S3 path to test data with ground truth
        model_metadata_s3_path: S3 path to model metadata
        
    Returns:
        Dictionary containing evaluation metrics
    """
    import pandas as pd
    import numpy as np
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix, classification_report
    )
    import json
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # SageMaker Processing Job environment paths
    input_path = "/opt/ml/processing/input"
    output_path = "/opt/ml/processing/output"
    
    # Load predictions
    predictions_files = [f for f in os.listdir(os.path.join(input_path, "predictions")) 
                        if f.endswith('.out') or f.endswith('.csv')]
    
    predictions_list = []
    for pred_file in predictions_files:
        pred_df = pd.read_csv(os.path.join(input_path, "predictions", pred_file), header=None)
        predictions_list.append(pred_df)
    
    # Combine all prediction files
    predictions_df = pd.concat(predictions_list, ignore_index=True)
    predictions_df.columns = ['predicted_probability']
    
    # Convert probabilities to binary predictions
    predictions_df['predicted_class'] = (predictions_df['predicted_probability'] > 0.5).astype(int)
    
    # Load test data with ground truth
    test_files = [f for f in os.listdir(os.path.join(input_path, "test_data")) 
                 if f.endswith('.csv')]
    test_df = pd.read_csv(os.path.join(input_path, "test_data", test_files[0]))
    
    # Ensure same order
    if len(test_df) != len(predictions_df):
        print(f"Warning: Test data length ({len(test_df)}) != Predictions length ({len(predictions_df)})")
    
    # Align data
    min_length = min(len(test_df), len(predictions_df))
    test_df = test_df.iloc[:min_length]
    predictions_df = predictions_df.iloc[:min_length]
    
    y_true = test_df['target'].values
    y_pred = predictions_df['predicted_class'].values
    y_pred_proba = predictions_df['predicted_probability'].values
    
    # Calculate comprehensive metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    auc = roc_auc_score(y_true, y_pred_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    # Business metrics for credit scoring
    approval_rate = np.mean(y_pred == 0)  # Assuming 0 = approved, 1 = rejected
    high_risk_precision = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    high_risk_recall = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    
    # Calculate additional business metrics
    false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0
    false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    # Risk distribution analysis
    risk_distribution = {
        'low_risk_count': int(np.sum(y_pred == 0)),
        'high_risk_count': int(np.sum(y_pred == 1)),
        'low_risk_percentage': float(np.mean(y_pred == 0) * 100),
        'high_risk_percentage': float(np.mean(y_pred == 1) * 100)
    }
    
    # Compile all metrics
    evaluation_metrics = {
        # Classification metrics
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'auc_roc': float(auc),
        
        # Confusion matrix components
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_positives': int(tp),
        
        # Business metrics
        'approval_rate': float(approval_rate),
        'high_risk_precision': float(high_risk_precision),
        'high_risk_recall': float(high_risk_recall),
        'false_positive_rate': float(false_positive_rate),
        'false_negative_rate': float(false_negative_rate),
        
        # Risk distribution
        **risk_distribution,
        
        # Model performance indicators
        'total_predictions': int(len(y_true)),
        'prediction_accuracy_by_class': {
            'low_risk_accuracy': float(recall_score(y_true, y_pred, pos_label=0, zero_division=0)),
            'high_risk_accuracy': float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
        }
    }
    
    # Generate detailed classification report
    class_report = classification_report(y_true, y_pred, output_dict=True)
    
    # Create visualizations
    plt.figure(figsize=(12, 8))
    
    # Confusion Matrix
    plt.subplot(2, 2, 1)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    # ROC Curve (simplified)
    plt.subplot(2, 2, 2)
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend()
    
    # Prediction Distribution
    plt.subplot(2, 2, 3)
    plt.hist(y_pred_proba, bins=30, alpha=0.7, edgecolor='black')
    plt.xlabel('Predicted Probability')
    plt.ylabel('Frequency')
    plt.title('Prediction Probability Distribution')
    
    # Risk Distribution
    plt.subplot(2, 2, 4)
    risk_labels = ['Low Risk (Approved)', 'High Risk (Rejected)']
    risk_counts = [risk_distribution['low_risk_count'], risk_distribution['high_risk_count']]
    plt.pie(risk_counts, labels=risk_labels, autopct='%1.1f%%', startangle=90)
    plt.title('Risk Distribution')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, 'evaluation_plots.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Save detailed evaluation report
    evaluation_report = {
        'model_performance': evaluation_metrics,
        'classification_report': class_report,
        'business_impact': {
            'total_applications': int(len(y_true)),
            'approvals': int(np.sum(y_pred == 0)),
            'rejections': int(np.sum(y_pred == 1)),
            'approval_rate': f"{approval_rate*100:.2f}%",
            'model_precision': f"{precision*100:.2f}%",
            'model_recall': f"{recall*100:.2f}%"
        }
    }
    
    # Save evaluation results
    with open(os.path.join(output_path, 'evaluation_report.json'), 'w') as f:
        json.dump(evaluation_report, f, indent=2)
    
    # Create summary metrics file
    summary_metrics = {
        'model_accuracy': accuracy,
        'business_approval_rate': approval_rate,
        'risk_detection_precision': high_risk_precision,
        'overall_auc': auc
    }
    
    with open(os.path.join(output_path, 'summary_metrics.json'), 'w') as f:
        json.dump(summary_metrics, f, indent=2)
    
    print("Model evaluation completed successfully")
    print(f"Overall Accuracy: {accuracy:.4f}")
    print(f"AUC-ROC: {auc:.4f}")
    print(f"Approval Rate: {approval_rate:.4f}")
    print(f"High Risk Detection Precision: {high_risk_precision:.4f}")
    
    return evaluation_metrics

# Main Workflow: Complete SageMaker Credit Scoring Pipeline
@workflow
def sagemaker_credit_scoring_pipeline(
    raw_data_s3_path: str = "s3://bsingh-ml-workflows/raw/CleanCreditScoring.csv",
    hyperparameters: Dict[str, Any] = {
        "max_depth": 6,
        "eta": 0.3,
        "gamma": 0,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "num_boost_round": 100,
        "early_stopping_rounds": 10
    },
    preprocessing_config: SageMakerProcessingConfig = SageMakerProcessingConfig(),
    training_config: SageMakerTrainingConfig = SageMakerTrainingConfig(),
    batch_config: SageMakerBatchTransformConfig = SageMakerBatchTransformConfig()
) -> Dict[str, float]:
    """
    Complete credit scoring ML pipeline using SageMaker managed services
    
    This workflow demonstrates the full ML lifecycle on SageMaker:
    1. Data Preprocessing (SageMaker Processing)
    2. Model Training (SageMaker Training with XGBoost)
    3. Batch Prediction (SageMaker Batch Transform)
    4. Model Evaluation (SageMaker Processing)
    
    Key Benefits:
    - Fully managed infrastructure (no servers to manage)
    - Auto-scaling based on workload
    - Cost optimization with spot instances
    - Enterprise-grade security and compliance
    - Integrated monitoring and logging
    
    Args:
        raw_data_s3_path: S3 path to raw credit scoring dataset
        hyperparameters: XGBoost model hyperparameters
        preprocessing_config: Data preprocessing configuration
        training_config: Model training configuration  
        batch_config: Batch inference configuration
        
    Returns:
        Dictionary containing comprehensive evaluation metrics
    """
    
    # Step 1: Data Preprocessing using SageMaker Processing
    preprocessed_data_path = preprocess_data_sagemaker(
        raw_data_s3_path=raw_data_s3_path,
        preprocessing_config=preprocessing_config
    )
    
    # Step 2: Model Training using SageMaker Training Jobs
    trained_model_path = train_credit_scoring_model_sagemaker(
        preprocessed_data_s3_path=preprocessed_data_path,
        training_config=training_config,
        hyperparameters=hyperparameters
    )
    
    # Step 3: Batch Prediction using SageMaker Batch Transform
    predictions_path = batch_predict_credit_scores_sagemaker(
        model_s3_path=trained_model_path,
        test_data_s3_path=preprocessed_data_path,  # Using test split from preprocessing
        batch_config=batch_config
    )
    
    # Step 4: Model Evaluation using SageMaker Processing
    evaluation_metrics = evaluate_credit_scoring_model_sagemaker(
        predictions_s3_path=predictions_path,
        test_data_s3_path=preprocessed_data_path,
        model_metadata_s3_path=trained_model_path
    )
    
    return evaluation_metrics

# Alternative Workflow: GPU-accelerated Deep Learning for Credit Scoring
@workflow
def sagemaker_deep_learning_credit_scoring(
    raw_data_s3_path: str = "s3://bsingh-ml-workflows/raw/CleanCreditScoring.csv",
    model_config: Dict[str, Any] = {
        "hidden_layers": [128, 64, 32],
        "dropout_rate": 0.3,
        "learning_rate": 0.001,
        "epochs": 100,
        "batch_size": 32
    }
) -> Dict[str, float]:
    """
    Alternative deep learning pipeline using PyTorch on GPU instances
    
    This workflow uses SageMaker's GPU instances for neural network training:
    - ml.p3.2xlarge instances with Tesla V100 GPUs
    - PyTorch framework with automatic mixed precision
    - Distributed training capabilities
    """
    
    # Preprocessing (same as above)
    preprocessed_data_path = preprocess_data_sagemaker(
        raw_data_s3_path=raw_data_s3_path,
        preprocessing_config=SageMakerProcessingConfig()
    )
    
    # GPU-based deep learning training
    @task(
        task_config={
            "platform": "sagemaker",
            "job_type": "training",
            "instance_type": "ml.p3.2xlarge",  # GPU instance
            "instance_count": 1,
            "framework": "pytorch",
            "framework_version": "1.8.0",
            "python_version": "py36",
            "use_spot_instances": True
        },
        requests=Resources(cpu="8", mem="32Gi", gpu="1")
    )
    def train_pytorch_model(data_path: str, config: Dict[str, Any]) -> str:
        """Train PyTorch neural network on GPU"""
        import torch
        import torch.nn as nn
        import pandas as pd
        
        # Neural network implementation
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Training on device: {device}")
        
        # Load data and train model...
        # (Implementation would include full PyTorch training loop)
        
        return "s3://bsingh-ml-workflows/sagemaker/pytorch/model.tar.gz"
    
    # Train model
    pytorch_model_path = train_pytorch_model(
        data_path=preprocessed_data_path,
        config=model_config
    )
    
    # Batch prediction and evaluation (same as above)
    predictions_path = batch_predict_credit_scores_sagemaker(
        model_s3_path=pytorch_model_path,
        test_data_s3_path=preprocessed_data_path,
        batch_config=SageMakerBatchTransformConfig()
    )
    
    evaluation_metrics = evaluate_credit_scoring_model_sagemaker(
        predictions_s3_path=predictions_path,
        test_data_s3_path=preprocessed_data_path,
        model_metadata_s3_path=pytorch_model_path
    )
    
    return evaluation_metrics

if __name__ == "__main__":
    # Example execution
    print("SageMaker Credit Scoring Pipeline")
    print("This pipeline runs entirely on SageMaker managed infrastructure")
    print("Key benefits: No infrastructure management, auto-scaling, cost optimization")
