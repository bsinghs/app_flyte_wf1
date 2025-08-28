# Multi-Runtime Flyte Workflow Examples

## Overview

Flyte allows you to run different tasks in the same workflow on completely different compute backends. This enables optimal resource utilization and cost optimization.

## Mixed Runtime Workflow Examples

### 1. Complete Multi-Runtime ML Pipeline

```python
from flytekit import task, workflow, Resources
from flytekitplugins.ray import RayJobConfig
from datetime import timedelta
import pandas as pd

# Task 1: Data preprocessing on LOCAL Kubernetes
@task(
    requests=Resources(cpu="500m", mem="1Gi"),
    limits=Resources(cpu="1", mem="2Gi"),
    # No task_config = runs on local Kubernetes cluster
)
def preprocess_data_local(raw_data_path: str) -> pd.DataFrame:
    """Runs on your local Kubernetes cluster"""
    print("🏠 Running data preprocessing on LOCAL Kubernetes")
    df = pd.read_csv(raw_data_path)
    # Light preprocessing on local cluster
    df_clean = df.dropna()
    return df_clean

# Task 2: Feature engineering with RAY (distributed)
@task(
    task_config=RayJobConfig(
        num_workers=4,
        num_cpus_per_worker=2,
        memory_per_worker="2Gi"
    )
)
def feature_engineering_ray(data: pd.DataFrame) -> pd.DataFrame:
    """Runs on Ray cluster for distributed computing"""
    print("⚡ Running feature engineering on RAY cluster")
    import ray
    
    @ray.remote
    def process_chunk(chunk):
        # Heavy feature engineering per chunk
        return compute_features(chunk)
    
    # Distribute work across Ray workers
    chunks = split_dataframe(data, num_chunks=4)
    futures = [process_chunk.remote(chunk) for chunk in chunks]
    results = ray.get(futures)
    
    return pd.concat(results)

# Task 3: Model training on SAGEMAKER
@task(
    task_config={
        "platform": "sagemaker",
        "job_type": "training",
        "instance_type": "ml.m5.2xlarge",
        "instance_count": 1,
        "use_spot_instances": True,
        "framework": "sklearn",
        "framework_version": "0.23-1"
    }
)
def train_model_sagemaker(features: pd.DataFrame) -> str:
    """Runs on SageMaker managed infrastructure"""
    print("🚀 Running model training on SAGEMAKER")
    
    # SageMaker training environment
    input_path = "/opt/ml/input/data"
    model_path = "/opt/ml/model"
    
    from sklearn.ensemble import RandomForestClassifier
    import joblib
    
    # Train model
    X = features.drop('target', axis=1)
    y = features['target']
    
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    
    # Save model
    joblib.dump(model, f"{model_path}/model.pkl")
    
    return "s3://bucket/models/trained_model.tar.gz"

# Task 4: Batch inference on AWS BATCH (spot instances)
@task(
    task_config={
        "platform": "aws_batch",
        "queue": "spot-queue",
        "job_definition": "ml-inference-job",
        "vcpus": 2,
        "memory": 4096
    }
)
def batch_inference_aws_batch(model_path: str, test_data: pd.DataFrame) -> pd.DataFrame:
    """Runs on AWS Batch with spot instances for cost optimization"""
    print("💰 Running batch inference on AWS BATCH (spot instances)")
    
    # Load model and make predictions
    import joblib
    model = joblib.load(model_path)
    predictions = model.predict(test_data)
    
    return pd.DataFrame({'predictions': predictions})

# Task 5: Model evaluation back on LOCAL
@task(
    requests=Resources(cpu="200m", mem="512Mi"),
    # Runs on local cluster for final analysis
)
def evaluate_model_local(predictions: pd.DataFrame, ground_truth: pd.DataFrame) -> dict:
    """Final evaluation on local cluster"""
    print("🏠 Running model evaluation on LOCAL Kubernetes")
    
    from sklearn.metrics import accuracy_score, classification_report
    
    accuracy = accuracy_score(ground_truth['actual'], predictions['predictions'])
    
    return {
        "accuracy": accuracy,
        "total_predictions": len(predictions),
        "runtime_summary": "Mixed: Local → Ray → SageMaker → AWS Batch → Local"
    }

# The workflow orchestrates all different runtimes
@workflow
def multi_runtime_ml_workflow(data_path: str, test_data_path: str) -> dict:
    """
    A complete ML workflow using 4 different compute backends:
    1. Local Kubernetes - Data preprocessing  
    2. Ray - Distributed feature engineering
    3. SageMaker - Managed model training
    4. AWS Batch - Cost-effective batch inference
    5. Local Kubernetes - Final evaluation
    """
    
    # Step 1: Preprocess on local K8s
    clean_data = preprocess_data_local(raw_data_path=data_path)
    
    # Step 2: Feature engineering on Ray
    features = feature_engineering_ray(data=clean_data)
    
    # Step 3: Train model on SageMaker
    model_path = train_model_sagemaker(features=features)
    
    # Step 4: Load test data locally
    test_data = preprocess_data_local(raw_data_path=test_data_path)
    
    # Step 5: Batch inference on AWS Batch
    predictions = batch_inference_aws_batch(
        model_path=model_path, 
        test_data=test_data
    )
    
    # Step 6: Evaluate locally
    results = evaluate_model_local(
        predictions=predictions,
        ground_truth=test_data
    )
    
    return results
```

### 2. Cost-Optimized Runtime Selection

```python
@workflow
def cost_optimized_workflow(data_size: int, budget: float) -> str:
    """
    Intelligently route tasks based on cost and performance requirements
    """
    
    # Small preprocessing always on local
    if data_size < 1000:
        result = preprocess_data_local(data_path="small_dataset.csv")
        
    # Medium data on Ray for speed
    elif data_size < 100000:
        result = feature_engineering_ray(data=input_data)
        
    # Large data on AWS Batch for cost
    else:
        result = batch_process_aws_batch(data=input_data)
    
    # Training decision based on budget
    if budget > 1000:
        # High budget: Use SageMaker for managed experience
        model = train_model_sagemaker(features=result)
    else:
        # Low budget: Use spot instances on local cluster
        model = train_model_local_spot(features=result)
    
    return f"Processed {data_size} records within ${budget} budget"
```

### 3. Development vs Production Runtime Routing

```python
import os

# Environment-based runtime selection
ENVIRONMENT = os.environ.get("FLYTE_ENV", "development")

@task(
    task_config={
        "platform": "sagemaker" if ENVIRONMENT == "production" else None,
        "instance_type": "ml.m5.large" if ENVIRONMENT == "production" else None
    } if ENVIRONMENT == "production" else {},
    requests=Resources(cpu="500m", mem="1Gi") if ENVIRONMENT == "development" else None
)
def adaptive_training_task(data: pd.DataFrame) -> str:
    """
    Runs on SageMaker in production, local K8s in development
    """
    if ENVIRONMENT == "production":
        print("🚀 Production training on SageMaker")
        # SageMaker-specific code
        input_path = "/opt/ml/input/data"
        model_path = "/opt/ml/model"
    else:
        print("🛠️ Development training on local cluster")
        # Local development code
        input_path = "/tmp/data"
        model_path = "/tmp/model"
    
    # Common training logic
    model = train_model(data)
    save_model(model, model_path)
    
    return f"Model trained in {ENVIRONMENT} environment"
```

### 4. Failure Resilience with Runtime Fallbacks

```python
from flytekit.exceptions import FlyteRecoverableException

@task(
    task_config={
        "platform": "sagemaker",
        "instance_type": "ml.m5.xlarge"
    },
    retries=1  # Allow one retry
)
def primary_sagemaker_task(data: pd.DataFrame) -> str:
    """Primary task on SageMaker with fallback capability"""
    try:
        # SageMaker-specific processing
        return process_on_sagemaker(data)
    except Exception as e:
        # Trigger fallback by raising recoverable exception
        raise FlyteRecoverableException(f"SageMaker failed: {e}")

@task(
    requests=Resources(cpu="1", mem="2Gi"),
    # Fallback to local processing
)
def fallback_local_task(data: pd.DataFrame) -> str:
    """Fallback task on local cluster"""
    print("⚠️ Falling back to local processing")
    return process_locally(data)

@workflow
def resilient_workflow(data: pd.DataFrame) -> str:
    """
    Try SageMaker first, fallback to local if it fails
    """
    try:
        # Attempt primary processing on SageMaker
        result = primary_sagemaker_task(data=data)
        return f"✅ Completed on SageMaker: {result}"
    except:
        # Fallback to local processing
        result = fallback_local_task(data=data)
        return f"⚠️ Completed on local fallback: {result}"
```

## Runtime Selection Strategy

### **Task Assignment Guidelines**

| **Task Type** | **Recommended Runtime** | **Reason** |
|---------------|------------------------|------------|
| **Data Preprocessing** | Local K8s | Fast I/O, low cost |
| **Feature Engineering** | Ray | Distributed computing |
| **Model Training** | SageMaker | Managed ML infrastructure |
| **Batch Inference** | AWS Batch | Cost-effective spot instances |
| **Real-time Serving** | Local K8s/SageMaker Endpoints | Low latency |
| **Development/Testing** | Local K8s | Fast iteration |
| **Large-scale ETL** | Spark on EMR | Big data processing |

### **Configuration Management**

```python
# centralized runtime configuration
RUNTIME_CONFIG = {
    "development": {
        "training": {"platform": None},  # Local K8s
        "inference": {"platform": None}   # Local K8s
    },
    "staging": {
        "training": {"platform": "sagemaker", "instance_type": "ml.m5.large"},
        "inference": {"platform": "aws_batch"}
    },
    "production": {
        "training": {"platform": "sagemaker", "instance_type": "ml.m5.2xlarge"},
        "inference": {"platform": "sagemaker", "job_type": "batch_transform"}
    }
}

def get_task_config(task_type: str) -> dict:
    env = os.environ.get("FLYTE_ENV", "development")
    return RUNTIME_CONFIG[env][task_type]

@task(task_config=get_task_config("training"))
def environment_aware_training():
    pass
```

## Benefits of Multi-Runtime Workflows

### **🎯 Optimization Benefits**
- **Cost**: Use spot instances for non-critical tasks
- **Performance**: Ray for distributed computing, SageMaker for ML
- **Resource Efficiency**: Right-size each task to its needs
- **Development Speed**: Local for iteration, cloud for production

### **🔄 Operational Benefits**  
- **Flexibility**: Change runtimes without code changes
- **Resilience**: Fallback options if one runtime fails
- **Compliance**: Route sensitive workloads to specific environments
- **Experimentation**: A/B test different compute backends

This multi-runtime capability is what makes Flyte incredibly powerful for production ML workflows! 🚀
