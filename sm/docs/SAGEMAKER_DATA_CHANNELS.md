# SageMaker Data Access Channels in Flyte

## Overview

SageMaker provides standardized data access patterns through filesystem channels. Each SageMaker job type has specific channel conventions for accessing input data and storing outputs.

## Channel Types by Job Type

### 1. Processing Jobs
```python
@task(task_config={
    "platform": "sagemaker",
    "job_type": "processing",
    "input_channels": {
        "data": "s3://bucket/input/data/",
        "config": "s3://bucket/config/"
    },
    "output_channels": {
        "processed": "s3://bucket/output/processed/",
        "metrics": "s3://bucket/output/metrics/"
    }
})
def process_data():
    # Access input data
    input_path = "/opt/ml/processing/input"
    data_df = pd.read_csv(f"{input_path}/data/dataset.csv")
    config = json.load(open(f"{input_path}/config/config.json"))
    
    # Process data...
    
    # Save outputs
    output_path = "/opt/ml/processing/output"
    processed_df.to_csv(f"{output_path}/processed/clean_data.csv")
    metrics.to_json(f"{output_path}/metrics/metrics.json")
```

### 2. Training Jobs
```python
@task(task_config={
    "platform": "sagemaker", 
    "job_type": "training",
    "input_channels": {
        "training": "s3://bucket/train/",
        "validation": "s3://bucket/val/",
        "test": "s3://bucket/test/"
    },
    "hyperparameters": {
        "epochs": "100",
        "batch_size": "32"
    }
})
def train_model():
    # Standard SageMaker training paths
    input_path = "/opt/ml/input/data"
    model_path = "/opt/ml/model"
    
    # Access training data by channel name
    train_df = pd.read_csv(f"{input_path}/training/train.csv")
    val_df = pd.read_csv(f"{input_path}/validation/val.csv")
    test_df = pd.read_csv(f"{input_path}/test/test.csv")
    
    # Train model...
    
    # Save model artifacts
    model.save(f"{model_path}/model.pkl")
    joblib.dump(scaler, f"{model_path}/scaler.pkl")
```

### 3. Batch Transform Jobs
```python
@task(task_config={
    "platform": "sagemaker",
    "job_type": "batch_transform",
    "model_name": "my-trained-model",
    "input_location": "s3://bucket/batch-input/",
    "output_location": "s3://bucket/batch-output/",
    "instance_type": "ml.m5.large"
})
def batch_inference():
    # Batch Transform handles I/O automatically
    # Input data is provided via S3
    # Predictions are written to output S3 location
    pass
```

## Channel Mapping Examples

### Multi-Channel Processing
```python
# SageMaker Configuration
channels = {
    "raw_data": "s3://my-bucket/raw/",
    "reference_data": "s3://my-bucket/reference/", 
    "config": "s3://my-bucket/config/"
}

# Container Access Paths
input_paths = {
    "raw_data": "/opt/ml/processing/input/raw_data/",
    "reference_data": "/opt/ml/processing/input/reference_data/",
    "config": "/opt/ml/processing/input/config/"
}
```

### Training with Multiple Data Sources
```python
# SageMaker Training Channels
training_channels = {
    "training": {
        "ContentType": "text/csv",
        "CompressionType": "None", 
        "RecordWrapperType": "None",
        "S3DataType": "S3Prefix",
        "S3DataDistributionType": "FullyReplicated",
        "S3Uri": "s3://bucket/train/"
    },
    "validation": {
        "ContentType": "text/csv",
        "S3Uri": "s3://bucket/validation/"
    },
    "metadata": {
        "ContentType": "application/json",
        "S3Uri": "s3://bucket/metadata/"
    }
}

# Container Access
def access_training_data():
    base_path = "/opt/ml/input/data"
    
    # Each channel becomes a subdirectory
    train_data = pd.read_csv(f"{base_path}/training/data.csv")
    val_data = pd.read_csv(f"{base_path}/validation/data.csv") 
    metadata = json.load(open(f"{base_path}/metadata/meta.json"))
```

## Channel Data Types and Formats

### Supported Content Types
- **CSV**: `text/csv` - Most common for tabular data
- **JSON**: `application/json` - Configuration and metadata
- **Parquet**: `application/x-parquet` - Efficient columnar storage
- **Images**: `image/jpeg`, `image/png` - Computer vision workloads
- **Text**: `text/plain` - NLP datasets
- **Binary**: `application/octet-stream` - Custom formats

### Compression Options
```python
channel_config = {
    "CompressionType": "Gzip",  # None, Gzip
    "RecordWrapperType": "None"  # None, RecordIO
}
```

## Best Practices

### 1. Channel Naming
- Use descriptive names: `training`, `validation`, `test`
- Separate data types: `images`, `labels`, `metadata`
- Environment specific: `dev_data`, `prod_data`

### 2. Data Organization
```
s3://bucket/
├── training/
│   ├── features.csv
│   └── labels.csv
├── validation/
│   ├── features.csv  
│   └── labels.csv
└── config/
    ├── hyperparams.json
    └── model_config.json
```

### 3. Access Patterns
```python
def robust_data_access():
    input_base = "/opt/ml/processing/input"
    
    # Check available channels
    available_channels = os.listdir(input_base)
    print(f"Available channels: {available_channels}")
    
    # Robust file discovery
    for channel in available_channels:
        channel_path = os.path.join(input_base, channel)
        files = os.listdir(channel_path)
        print(f"Channel '{channel}' contains: {files}")
```

### 4. Output Organization
```python
def structured_output():
    output_base = "/opt/ml/processing/output"
    
    # Create output subdirectories
    os.makedirs(f"{output_base}/models", exist_ok=True)
    os.makedirs(f"{output_base}/reports", exist_ok=True)
    os.makedirs(f"{output_base}/metrics", exist_ok=True)
    
    # Save to appropriate channels
    model.save(f"{output_base}/models/trained_model.pkl")
    report.to_csv(f"{output_base}/reports/analysis.csv")
    metrics.to_json(f"{output_base}/metrics/performance.json")
```

## Environment Variables

SageMaker provides additional context through environment variables:

```python
import os

# Job information
job_name = os.environ.get('SAGEMAKER_JOB_NAME')
region = os.environ.get('AWS_DEFAULT_REGION')

# Resource information  
instance_type = os.environ.get('SM_CURRENT_INSTANCE_TYPE')
instance_count = os.environ.get('SM_NUM_INSTANCES')

# Channel information
training_channel = os.environ.get('SM_CHANNEL_TRAINING')
validation_channel = os.environ.get('SM_CHANNEL_VALIDATION')

# Model directory
model_dir = os.environ.get('SM_MODEL_DIR')  # /opt/ml/model
```

## Error Handling

```python
def safe_channel_access(channel_name, file_name):
    """Safely access files from SageMaker channels"""
    try:
        base_path = "/opt/ml/processing/input"
        file_path = os.path.join(base_path, channel_name, file_name)
        
        if not os.path.exists(file_path):
            # List available files for debugging
            channel_path = os.path.join(base_path, channel_name)
            available_files = os.listdir(channel_path) if os.path.exists(channel_path) else []
            raise FileNotFoundError(f"File {file_name} not found in channel {channel_name}. Available files: {available_files}")
        
        return pd.read_csv(file_path)
        
    except Exception as e:
        print(f"Error accessing {channel_name}/{file_name}: {str(e)}")
        raise
```

This channel system provides a standardized way to access data across different SageMaker job types while maintaining consistency in your Flyte workflows.
