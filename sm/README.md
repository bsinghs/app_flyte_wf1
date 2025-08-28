# SageMaker Integration for Flyte

This directory contains all SageMaker-related files and configurations for integrating Amazon SageMaker with your Flyte workflows.

## Directory Structure

```
sm/
├── README.md                           # This file
├── docs/
│   └── FLYTE_SAGEMAKER_INTEGRATION.md  # Comprehensive integration guide
├── workflows/
│   └── sagemaker_batch_prediction_pipeline.py  # Enhanced batch prediction pipeline
├── config/
│   └── sagemaker-integration-config.md # Configuration files and IAM policies
└── scripts/
    └── setup-sagemaker-integration.sh  # Automated setup script
```

## Quick Start

1. **Read the Integration Guide**: Start with `docs/FLYTE_SAGEMAKER_INTEGRATION.md` for a comprehensive overview of the architecture and integration approach.

2. **Review Configuration**: Check `config/sagemaker-integration-config.md` for IAM roles, policies, and Kubernetes configurations.

3. **Run Setup Script**: Execute `scripts/setup-sagemaker-integration.sh` to automatically configure your environment.

4. **Deploy Workflow**: Use the enhanced pipeline in `workflows/sagemaker_batch_prediction_pipeline.py` for your ML workloads.

## Key Features

- **SageMaker Training Jobs**: Scalable model training with spot instances
- **Batch Transform**: Large-scale inference with cost optimization
- **Processing Jobs**: Data preprocessing and feature engineering
- **Real-time Endpoints**: Low-latency model serving
- **Cost Optimization**: Automatic spot instance management and resource scaling

## 🔄 Integration with Other Compute Backends

This SageMaker integration works alongside other Flyte plugins:

- **Ray Plugin**: Use for custom distributed computing within your Kubernetes cluster
- **AWS Batch**: For large-scale batch processing with spot instances
- **Spark on EMR**: For big data processing workflows
- **Local K8s**: For development and small-scale tasks

### **Multi-Cloud ML Platform Support**
SageMaker is part of a broader **managed ML platform** category. Similar integrations are possible with:

- **🔵 Google Vertex AI**: Google Cloud's managed ML platform
- **🟦 Azure ML**: Microsoft's managed ML platform  
- **🟠 Databricks**: Multi-cloud ML platform

**Example Multi-Platform Workflow:**
```python
@workflow
def multi_cloud_ml_pipeline():
    # Data preprocessing with Ray (in-cluster)
    processed_data = ray_preprocessing_task()
    
    # Training on AWS SageMaker
    aws_model = sagemaker_training_task(processed_data)
    
    # Alternative training on Google Vertex AI (future)
    # gcp_model = vertex_training_task(processed_data)
    
    # Batch inference with cost optimization
    predictions = sagemaker_batch_transform(aws_model, test_data)
    
    return predictions
```

**Platform Selection Criteria:**
```python
# Choose platform based on requirements
@task
def intelligent_platform_routing(data_size: int, budget: float):
    if data_size > 1_000_000 and budget > 1000:
        return "sagemaker"  # AWS - best for large scale
    elif budget < 500:
        return "vertex_ai"  # GCP - cost-effective for smaller workloads
    else:
        return "ray"        # In-cluster - maximum control
```

## Prerequisites

- AWS CLI configured with appropriate permissions
- Kubernetes cluster with Flyte installed
- Helm 3.x for configuration updates
- Python 3.8+ with required dependencies

## Support

For issues or questions, refer to the troubleshooting section in the integration guide or check the main project documentation.
