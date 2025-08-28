# SageMaker Configuration Files for Flyte Integration

## IAM Policies and Roles

### 1. SageMaker Execution Role Trust Policy
# File: iam/sagemaker-execution-role-trust-policy.json

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "sagemaker.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT:role/FlytePropellerRole"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

### 2. SageMaker Custom Policy 
# File: iam/sagemaker-custom-policy.json

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bsingh-ml-workflows",
                "arn:aws:s3:::bsingh-ml-workflows/*",
                "arn:aws:s3:::education-eks-flyte-*",
                "arn:aws:s3:::education-eks-flyte-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability", 
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/sagemaker/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}

### 3. Flyte Propeller SageMaker Access Policy
# File: iam/flyte-sagemaker-access-policy.json

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sagemaker:CreateTrainingJob",
                "sagemaker:CreateProcessingJob",
                "sagemaker:CreateTransformJob", 
                "sagemaker:CreateModel",
                "sagemaker:CreateEndpoint",
                "sagemaker:CreateEndpointConfig",
                "sagemaker:DescribeTrainingJob",
                "sagemaker:DescribeProcessingJob",
                "sagemaker:DescribeTransformJob",
                "sagemaker:DescribeModel",
                "sagemaker:DescribeEndpoint",
                "sagemaker:DescribeEndpointConfig",
                "sagemaker:StopTrainingJob",
                "sagemaker:StopProcessingJob",
                "sagemaker:StopTransformJob",
                "sagemaker:DeleteEndpoint",
                "sagemaker:DeleteEndpointConfig",
                "sagemaker:DeleteModel",
                "sagemaker:ListTrainingJobs",
                "sagemaker:ListProcessingJobs",
                "sagemaker:ListTransformJobs",
                "sagemaker:ListModels",
                "sagemaker:ListEndpoints"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow", 
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::ACCOUNT:role/SageMakerExecutionRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bsingh-ml-workflows",
                "arn:aws:s3:::bsingh-ml-workflows/*"
            ]
        }
    ]
}

## Helm Values Update

### Enhanced Flyte Values for SageMaker
# File: config/flyte-values-sagemaker.yaml

configuration:
  # Database configuration (existing)
  database:
    host: "flyte-postgres.us-east-1.rds.amazonaws.com"
    port: 5432
    username: "flyteadmin"
    passwordPath: "/etc/db/password"
    dbname: "flyteadmin"
    
  # Storage configuration (existing)
  storage:
    type: s3
    container: "s3://education-eks-flyte-metadata-xxx"
    config:
      region: "us-east-1"
      auth_type: "iam"
      
  # Enhanced Propeller configuration with SageMaker
  propeller:
    plugins:
      # Existing plugins
      k8s:
        default-cpus: "500m"
        default-memory: "500Mi"
        
      codeweave:
        endpoint: "https://api.codeweave.com"
        auth:
          type: "api-key"
          secret: "codeweave-credentials"
          
      batch:
        region: "us-east-1"
        job-queue: "flyte-batch-queue"
        
      # New SageMaker plugin configuration
      sagemaker:
        region: "us-east-1"
        execution-role: "arn:aws:iam::ACCOUNT:role/SageMakerExecutionRole"
        
        # Default configurations
        defaults:
          instance-type: "ml.m5.large"
          volume-size-gb: 30
          max-runtime-seconds: 86400
          enable-spot-instances: true
          
        # Training job configuration
        training:
          default-instance-type: "ml.m5.xlarge"
          output-path: "s3://bsingh-ml-workflows/sagemaker/training/"
          supported-frameworks:
            - name: "xgboost"
              versions: ["1.2-1", "1.3-1"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost"
            - name: "pytorch"
              versions: ["1.8.0", "1.9.0"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training"
            - name: "tensorflow"
              versions: ["2.4.1", "2.5.0"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-training"
            - name: "sklearn"
              versions: ["0.23-1", "0.24-1"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn"
              
          # Instance types by use case
          instance-types:
            cpu:
              small: "ml.m5.large"
              medium: "ml.m5.xlarge"
              large: "ml.m5.2xlarge"
              xlarge: "ml.m5.4xlarge"
            gpu:
              small: "ml.p3.2xlarge"
              medium: "ml.p3.8xlarge"
              large: "ml.p3.16xlarge"
            memory:
              small: "ml.r5.large"
              medium: "ml.r5.xlarge"
              large: "ml.r5.2xlarge"
              
        # Processing job configuration
        processing:
          default-instance-type: "ml.m5.xlarge"
          output-path: "s3://bsingh-ml-workflows/sagemaker/processing/"
          supported-frameworks:
            - name: "sklearn"
              versions: ["0.23-1"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn"
            - name: "pandas"
              versions: ["1.0.3"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn"
            - name: "spark"
              versions: ["3.0.0", "3.1.1"]
              container: "763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-spark-processing"
              
        # Batch transform configuration
        batch-transform:
          default-instance-type: "ml.m5.large"
          output-path: "s3://bsingh-ml-workflows/sagemaker/batch-transform/"
          max-payload-mb: 6
          max-concurrent-transforms: 4
          strategy: "SingleRecord"
          assemble-with: "Line"
          
        # Endpoint configuration (for real-time inference)
        endpoints:
          default-instance-type: "ml.m5.large"
          auto-scaling:
            min-capacity: 1
            max-capacity: 10
            target-value: 70.0
            scale-in-cooldown: 300
            scale-out-cooldown: 300

# Service Account annotations for SageMaker access
flyteadmin:
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: "arn:aws:iam::ACCOUNT:role/FlyteAdminRole"
      
flytepropeller:
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: "arn:aws:iam::ACCOUNT:role/FlytePropellerRole"

# Enhanced ConfigMap for SageMaker
flytepropeller-manager:
  configPath: "/etc/flyte/config/*.yaml"

## Kubernetes ConfigMaps

### SageMaker Plugin Configuration
# File: k8s/sagemaker-plugin-config.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: sagemaker-plugin-config
  namespace: flyte
data:
  sagemaker.yaml: |
    sagemaker:
      region: us-east-1
      roleArn: arn:aws:iam::ACCOUNT:role/SageMakerExecutionRole
      
      # Resource limits and defaults
      resources:
        limits:
          cpu: 4
          memory: 16Gi
        requests:
          cpu: 1
          memory: 2Gi
          
      # Training job defaults
      training:
        instanceType: ml.m5.xlarge
        volumeSizeInGB: 30
        maxRuntimeInSeconds: 86400
        useSpotInstances: true
        
        # Framework configurations
        frameworks:
          xgboost:
            image: 763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.2-1
            pythonVersion: py3
          pytorch:
            image: 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:1.8.0-gpu-py36
            pythonVersion: py36
          tensorflow:
            image: 763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-training:2.4.1-gpu-py37
            pythonVersion: py37
          sklearn:
            image: 763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3
            pythonVersion: py3
            
      # Processing job defaults
      processing:
        instanceType: ml.m5.xlarge
        volumeSizeInGB: 30
        
      # Batch transform defaults  
      batchTransform:
        instanceType: ml.m5.large
        maxPayloadInMB: 6
        maxConcurrentTransforms: 4
        
      # S3 paths
      s3:
        bucket: bsingh-ml-workflows
        keyPrefix: sagemaker/
        
      # Monitoring and logging
      monitoring:
        enableCloudWatch: true
        logLevel: INFO
        
      # Networking
      networking:
        enableNetworkIsolation: false
        securityGroupIds: []
        subnets: []

## CDAO SDK Configuration

### Enhanced SDK Configuration
# File: config/cdao-sdk-sagemaker-config.yaml

cdao_sdk:
  version: "2.0"
  
  # Flyte connection
  flyte:
    admin_endpoint: "https://flyte.your-domain.com"
    insecure: false
    
  # SageMaker configuration
  sagemaker:
    region: "us-east-1"
    execution_role: "arn:aws:iam::ACCOUNT:role/SageMakerExecutionRole"
    s3_bucket: "bsingh-ml-workflows"
    
    # Default configurations by task type
    defaults:
      training:
        instance_type: "ml.m5.xlarge"
        use_spot_instances: true
        max_runtime_seconds: 3600
        
      processing:
        instance_type: "ml.m5.large"
        volume_size_gb: 30
        
      batch_transform:
        instance_type: "ml.m5.large"
        max_payload_mb: 6
        
    # Framework-specific configurations
    frameworks:
      xgboost:
        default_instance_type: "ml.m5.xlarge"
        supported_versions: ["1.2-1", "1.3-1"]
        
      pytorch:
        default_instance_type: "ml.p3.2xlarge"  # GPU default
        supported_versions: ["1.8.0", "1.9.0"]
        
      sklearn:
        default_instance_type: "ml.m5.large"
        supported_versions: ["0.23-1", "0.24-1"]
        
  # Platform routing rules
  routing:
    rules:
      - condition: "task_type == 'training' and framework == 'xgboost'"
        platform: "sagemaker"
        config:
          instance_type: "ml.m5.xlarge"
          use_spot_instances: true
          
      - condition: "task_type == 'training' and framework == 'pytorch'"
        platform: "sagemaker"
        config:
          instance_type: "ml.p3.2xlarge"
          use_spot_instances: true
          
      - condition: "task_type == 'batch_transform'"
        platform: "sagemaker"
        config:
          instance_type: "ml.m5.large"
          
      - condition: "task_type == 'processing' and framework == 'sklearn'"
        platform: "sagemaker"
        config:
          instance_type: "ml.m5.xlarge"
          
      # Fallback to other platforms
      - condition: "duration < 300"  # Less than 5 minutes
        platform: "eks"
        
      - condition: "requires_gpu and duration > 3600"  # Long GPU jobs
        platform: "codeweave"
        
      - condition: "cost_sensitive and duration > 1800"  # Cost-sensitive long jobs
        platform: "batch"
        config:
          use_spot_instances: true

## Deployment Scripts

### SageMaker Setup Script
# File: scripts/setup-sagemaker-integration.sh

#!/bin/bash

# SageMaker Integration Setup Script
set -e

echo "Setting up SageMaker integration for Flyte..."

# Variables
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
ROLE_NAME="SageMakerExecutionRole"
FLYTE_NAMESPACE="flyte"

echo "AWS Account: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"

# 1. Create SageMaker execution role
echo "Creating SageMaker execution role..."

aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://iam/sagemaker-execution-role-trust-policy.json \
  --description "SageMaker execution role for Flyte integration" || true

# 2. Attach managed policies
echo "Attaching managed policies..."

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# 3. Create and attach custom policy
echo "Creating custom policy..."

aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name SageMakerCustomPolicy \
  --policy-document file://iam/sagemaker-custom-policy.json

# 4. Update Flyte Propeller role
echo "Updating Flyte Propeller role..."

aws iam put-role-policy \
  --role-name FlytePropellerRole \
  --policy-name SageMakerAccess \
  --policy-document file://iam/flyte-sagemaker-access-policy.json

# 5. Create S3 bucket structure
echo "Setting up S3 bucket structure..."

aws s3api put-object \
  --bucket bsingh-ml-workflows \
  --key sagemaker/training/ \
  --body /dev/null

aws s3api put-object \
  --bucket bsingh-ml-workflows \
  --key sagemaker/processing/ \
  --body /dev/null

aws s3api put-object \
  --bucket bsingh-ml-workflows \
  --key sagemaker/batch-transform/ \
  --body /dev/null

aws s3api put-object \
  --bucket bsingh-ml-workflows \
  --key sagemaker/models/ \
  --body /dev/null

# 6. Update Flyte configuration
echo "Updating Flyte configuration..."

kubectl apply -f k8s/sagemaker-plugin-config.yaml -n $FLYTE_NAMESPACE

# 7. Restart Flyte Propeller to pick up new configuration
echo "Restarting Flyte Propeller..."

kubectl rollout restart deployment/flytepropeller -n $FLYTE_NAMESPACE
kubectl rollout status deployment/flytepropeller -n $FLYTE_NAMESPACE

# 8. Verify installation
echo "Verifying SageMaker integration..."

# Check if role exists
aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1 && echo "✅ SageMaker role created successfully"

# Check if S3 structure exists
aws s3 ls s3://bsingh-ml-workflows/sagemaker/ >/dev/null 2>&1 && echo "✅ S3 structure created successfully"

# Check if Flyte Propeller is running
kubectl get deployment flytepropeller -n $FLYTE_NAMESPACE >/dev/null 2>&1 && echo "✅ Flyte Propeller is running"

echo "SageMaker integration setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test the integration with: pyflyte run src/workflows/sagemaker_batch_prediction_pipeline.py"
echo "2. Monitor SageMaker jobs in AWS Console"
echo "3. Check Flyte Console for workflow execution status"
