# Flyte Task Parameters Reference

## Complete Task Parameter Examples

### 1. Basic Resource Configuration
```python
from flytekit import task, Resources
from datetime import timedelta

@task(
    # Resource management
    requests=Resources(cpu="200m", mem="256Mi"),     # Minimum guaranteed resources
    limits=Resources(cpu="1", mem="1Gi"),           # Maximum allowed resources
    
    # Execution control
    retries=2,                                      # Number of retry attempts on failure
    timeout=timedelta(minutes=30),                  # Maximum execution time
    interruptible=True,                            # Allow preemption (spot instances)
    
    # Caching
    cache=True,                                    # Enable result caching
    cache_version="1.0",                          # Version for cache invalidation
    cache_serialize=True,                         # Cache across workflow executions
    
    # Container configuration
    container_image="python:3.9-slim",           # Custom container image
    environment={"ENV_VAR": "value"},             # Environment variables
)
def basic_task_example():
    return "Hello from basic task"
```

### 2. Advanced Resource Configuration
```python
@task(
    requests=Resources(
        cpu="500m",           # 0.5 CPU cores
        mem="1Gi",           # 1 Gibibyte of memory
        gpu="1",             # 1 GPU (if available)
        storage="10Gi"       # 10 Gibibytes ephemeral storage
    ),
    limits=Resources(
        cpu="2",             # Max 2 CPU cores  
        mem="4Gi",           # Max 4 Gibibytes memory
        gpu="1",             # Max 1 GPU
        storage="20Gi"       # Max 20 Gibibytes storage
    )
)
def resource_intensive_task():
    # GPU/CPU intensive processing
    pass
```

### 3. Error Handling and Retries
```python
from flytekit.core.task import task
from flytekit.exceptions import FlyteRecoverableException

@task(
    retries=5,                              # Retry up to 5 times
    timeout=timedelta(hours=1),             # 1 hour timeout
    interruptible=False,                    # Don't allow interruption
)
def robust_task():
    try:
        # Some operation that might fail
        result = potentially_failing_operation()
        return result
    except TemporaryError as e:
        # Raise recoverable exception to trigger retry
        raise FlyteRecoverableException(f"Temporary failure: {e}")
```

### 4. Custom Container Configuration
```python
from flytekit import Secret

@task(
    container_image="my-registry.com/ml-image:v2.0",
    environment={
        "PYTHONPATH": "/opt/ml/code",
        "MODEL_DIR": "/opt/ml/model", 
        "AWS_DEFAULT_REGION": "us-west-2"
    },
    secret_requests=[
        Secret(group="aws", key="access_key_id"),
        Secret(group="aws", key="secret_access_key"),
        Secret(group="db", key="connection_string")
    ]
)
def containerized_task():
    import os
    # Access environment variables
    model_dir = os.environ.get("MODEL_DIR")
    
    # Access secrets (injected as environment variables)
    aws_key = os.environ.get("FLYTE_SECRETS_AWS_ACCESS_KEY_ID")
    return f"Using model dir: {model_dir}"
```

### 5. Platform-Specific Task Configurations

#### SageMaker Configuration
```python
@task(
    task_config={
        "platform": "sagemaker",
        "job_type": "training",
        "instance_type": "ml.m5.2xlarge",
        "instance_count": 2,
        "volume_size_gb": 50,
        "max_runtime_seconds": 7200,
        "use_spot_instances": True,
        "spot_instance_max_wait_seconds": 3600,
        "framework": "sklearn",
        "framework_version": "0.23-1",
        "hyperparameters": {
            "epochs": "100",
            "batch_size": "32",
            "learning_rate": "0.001"
        },
        "input_channels": {
            "training": "s3://bucket/train/",
            "validation": "s3://bucket/val/"
        },
        "output_location": "s3://bucket/models/"
    }
)
def sagemaker_training_task():
    # SageMaker-specific training logic
    pass
```

#### Ray Configuration
```python
from flytekitplugins.ray import RayJobConfig

@task(
    task_config=RayJobConfig(
        num_workers=4,                    # Number of Ray workers
        num_cpus_per_worker=2,           # CPUs per worker
        num_gpus_per_worker=1,           # GPUs per worker  
        memory_per_worker="4Gi",         # Memory per worker
        ray_start_params={               # Ray cluster parameters
            "dashboard-host": "0.0.0.0",
            "include-dashboard": True
        }
    )
)
def distributed_ray_task():
    import ray
    
    @ray.remote
    def parallel_work(data):
        return process_data(data)
    
    # Distributed processing
    futures = [parallel_work.remote(chunk) for chunk in data_chunks]
    results = ray.get(futures)
    return results
```

#### Spark Configuration  
```python
from flytekitplugins.spark import PySparkTask

spark_task = PySparkTask(
    name="spark_example",
    spark_conf={
        "spark.driver.memory": "2g",
        "spark.executor.memory": "4g", 
        "spark.executor.cores": "2",
        "spark.executor.instances": "3",
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true"
    },
    hadoop_conf={
        "fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    }
)

@task(task_config=spark_task)
def spark_processing_task():
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    # Spark processing logic
```

### 6. Kubernetes Pod Configuration
```python
from kubernetes.client.models import V1PodSpec, V1Container, V1ResourceRequirements
from flytekit.extras.tasks.pod import Pod

@task(
    task_config=Pod(
        pod_spec=V1PodSpec(
            containers=[
                V1Container(
                    name="main",
                    image="tensorflow/tensorflow:2.8.0-gpu",
                    command=["python", "/app/train.py"],
                    resources=V1ResourceRequirements(
                        requests={"cpu": "1", "memory": "2Gi", "nvidia.com/gpu": "1"},
                        limits={"cpu": "2", "memory": "4Gi", "nvidia.com/gpu": "1"}
                    ),
                    env=[
                        {"name": "CUDA_VISIBLE_DEVICES", "value": "0"}
                    ]
                )
            ],
            restart_policy="Never",
            node_selector={"accelerator": "nvidia-tesla-v100"}
        )
    )
)
def custom_kubernetes_task():
    # Custom Kubernetes pod execution
    pass
```

### 7. Caching Strategies
```python
# Simple caching
@task(cache=True, cache_version="1.0")
def cached_task(input_data: str) -> str:
    return expensive_computation(input_data)

# Advanced caching with custom serialization
@task(
    cache=True,
    cache_version="2.0", 
    cache_serialize=True,              # Cache across executions
    cache_ignore_input_vars=["debug"]  # Ignore certain inputs for caching
)
def advanced_cached_task(data: str, model_version: str, debug: bool = False) -> str:
    if debug:
        print("Debug mode enabled")
    return process_with_model(data, model_version)
```

### 8. Monitoring and Observability
```python
from flytekit import current_context

@task(
    retries=3,
    timeout=timedelta(minutes=45),
    environment={"LOG_LEVEL": "INFO"}
)
def monitored_task() -> str:
    ctx = current_context()
    
    # Access execution context
    print(f"Execution ID: {ctx.execution_id}")
    print(f"Task retry attempt: {ctx.retry_attempt}")
    print(f"Raw output prefix: {ctx.raw_output_prefix}")
    
    # Custom metrics/logging
    start_time = time.time()
    result = do_work()
    duration = time.time() - start_time
    
    print(f"Task completed in {duration:.2f} seconds")
    return result
```

## Parameter Categories Summary

### **Resource Management**
- `requests`: Minimum guaranteed resources
- `limits`: Maximum allowed resources  
- `timeout`: Maximum execution time
- `interruptible`: Allow preemption

### **Error Handling**
- `retries`: Number of retry attempts
- Custom exception handling with `FlyteRecoverableException`

### **Container & Environment**
- `container_image`: Custom Docker image
- `environment`: Environment variables
- `secret_requests`: Secret management

### **Performance & Optimization**
- `cache`: Enable result caching
- `cache_version`: Cache invalidation
- `cache_serialize`: Cross-execution caching

### **Platform Integration**  
- `task_config`: Platform-specific configurations
- Support for SageMaker, Ray, Spark, Kubernetes, etc.

### **Execution Context**
- Access to execution metadata via `current_context()`
- Retry attempt tracking
- Output path management

## Best Practices

1. **Always set resource requests/limits** for predictable scheduling
2. **Use caching** for expensive, deterministic computations  
3. **Set appropriate timeouts** to prevent hanging tasks
4. **Use retries** for tasks that might fail due to external factors
5. **Leverage platform-specific configs** for optimal performance
6. **Monitor execution context** for debugging and optimization
