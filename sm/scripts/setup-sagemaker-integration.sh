#!/bin/bash

# SageMaker Integration Setup Script for Flyte
# This script sets up SageMaker integration with your existing Flyte infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Variables
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "UNKNOWN")
AWS_REGION=${AWS_REGION:-us-east-1}
SAGEMAKER_ROLE_NAME="SageMakerExecutionRole"
FLYTE_PROPELLER_ROLE="FlytePropellerRole"
FLYTE_NAMESPACE="flyte"
S3_BUCKET="bsingh-ml-workflows"

print_header "🚀 Setting up SageMaker integration for Flyte"
echo "=========================================="
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "SageMaker Role: $SAGEMAKER_ROLE_NAME"
echo "S3 Bucket: $S3_BUCKET"
echo "=========================================="

# Check prerequisites
print_status "Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not found. Please install kubectl first."
    exit 1
fi

# Check AWS credentials
if [ "$AWS_ACCOUNT_ID" == "UNKNOWN" ]; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if connected to Kubernetes cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to Kubernetes cluster. Please configure kubectl first."
    exit 1
fi

print_status "Prerequisites check passed ✅"

# Step 1: Create IAM policies and roles
print_header "Step 1: Creating IAM roles and policies"

# Create SageMaker execution role trust policy
print_status "Creating SageMaker execution role trust policy..."
cat > /tmp/sagemaker-trust-policy.json << EOF
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
                "AWS": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${FLYTE_PROPELLER_ROLE}"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create SageMaker execution role
print_status "Creating SageMaker execution role..."
aws iam create-role \
    --role-name $SAGEMAKER_ROLE_NAME \
    --assume-role-policy-document file:///tmp/sagemaker-trust-policy.json \
    --description "SageMaker execution role for Flyte integration" 2>/dev/null || print_warning "Role may already exist"

# Attach AWS managed SageMaker policy
print_status "Attaching SageMaker managed policy..."
aws iam attach-role-policy \
    --role-name $SAGEMAKER_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# Create custom S3 and ECR access policy for SageMaker
print_status "Creating custom SageMaker policy..."
cat > /tmp/sagemaker-custom-policy.json << EOF
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
                "arn:aws:s3:::${S3_BUCKET}",
                "arn:aws:s3:::${S3_BUCKET}/*"
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
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name $SAGEMAKER_ROLE_NAME \
    --policy-name SageMakerCustomPolicy \
    --policy-document file:///tmp/sagemaker-custom-policy.json

# Create Flyte Propeller SageMaker access policy
print_status "Creating Flyte Propeller SageMaker access policy..."
cat > /tmp/flyte-sagemaker-policy.json << EOF
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
                "sagemaker:ListTransformJobs"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${SAGEMAKER_ROLE_NAME}"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name $FLYTE_PROPELLER_ROLE \
    --policy-name SageMakerAccess \
    --policy-document file:///tmp/flyte-sagemaker-policy.json

print_status "IAM setup completed ✅"

# Step 2: Set up S3 bucket structure
print_header "Step 2: Setting up S3 bucket structure"

print_status "Creating S3 directories for SageMaker..."

# Create directory structure in S3
aws s3api put-object --bucket $S3_BUCKET --key sagemaker/ --body /dev/null 2>/dev/null || print_warning "S3 bucket may not exist or no permissions"
aws s3api put-object --bucket $S3_BUCKET --key sagemaker/training/ --body /dev/null 2>/dev/null || true
aws s3api put-object --bucket $S3_BUCKET --key sagemaker/processing/ --body /dev/null 2>/dev/null || true
aws s3api put-object --bucket $S3_BUCKET --key sagemaker/batch-transform/ --body /dev/null 2>/dev/null || true
aws s3api put-object --bucket $S3_BUCKET --key sagemaker/models/ --body /dev/null 2>/dev/null || true

print_status "S3 structure created ✅"

# Step 3: Update Flyte configuration
print_header "Step 3: Updating Flyte configuration"

print_status "Creating SageMaker plugin configuration..."

# Create ConfigMap for SageMaker plugin
cat > /tmp/sagemaker-plugin-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: sagemaker-plugin-config
  namespace: $FLYTE_NAMESPACE
data:
  sagemaker.yaml: |
    sagemaker:
      region: $AWS_REGION
      roleArn: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${SAGEMAKER_ROLE_NAME}
      
      # Training job defaults
      training:
        instanceType: ml.m5.xlarge
        volumeSizeInGB: 30
        maxRuntimeInSeconds: 86400
        useSpotInstances: true
        
      # Processing job defaults
      processing:
        instanceType: ml.m5.xlarge
        volumeSizeInGB: 30
        
      # Batch transform defaults
      batchTransform:
        instanceType: ml.m5.large
        maxPayloadInMB: 6
        maxConcurrentTransforms: 4
        
      # S3 configuration
      s3:
        bucket: $S3_BUCKET
        keyPrefix: sagemaker/
EOF

# Apply the ConfigMap
kubectl apply -f /tmp/sagemaker-plugin-config.yaml

# Update Flyte Propeller configuration to include SageMaker plugin
print_status "Updating Flyte Propeller configuration..."

kubectl patch configmap flyte-propeller-config -n $FLYTE_NAMESPACE --type merge -p '{
  "data": {
    "plugins.yaml": "plugins:\n  k8s:\n    default-cpus: \"500m\"\n    default-memory: \"500Mi\"\n  sagemaker:\n    region: \"'$AWS_REGION'\"\n    execution-role: \"arn:aws:iam::'$AWS_ACCOUNT_ID':role/'$SAGEMAKER_ROLE_NAME'\"\n    default-instance-type: \"ml.m5.large\"\n    enable-spot-instances: true\n    training:\n      output-path: \"s3://'$S3_BUCKET'/sagemaker/training/\"\n    processing:\n      output-path: \"s3://'$S3_BUCKET'/sagemaker/processing/\"\n    batch-transform:\n      output-path: \"s3://'$S3_BUCKET'/sagemaker/batch-transform/\""
  }
}' 2>/dev/null || print_warning "ConfigMap may not exist, creating new one..."

# If patch fails, create the ConfigMap
if [ $? -ne 0 ]; then
    cat > /tmp/flyte-propeller-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: flyte-propeller-config
  namespace: $FLYTE_NAMESPACE
data:
  plugins.yaml: |
    plugins:
      k8s:
        default-cpus: "500m"
        default-memory: "500Mi"
      sagemaker:
        region: "$AWS_REGION"
        execution-role: "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${SAGEMAKER_ROLE_NAME}"
        default-instance-type: "ml.m5.large"
        enable-spot-instances: true
        training:
          output-path: "s3://${S3_BUCKET}/sagemaker/training/"
        processing:
          output-path: "s3://${S3_BUCKET}/sagemaker/processing/"
        batch-transform:
          output-path: "s3://${S3_BUCKET}/sagemaker/batch-transform/"
EOF
    kubectl apply -f /tmp/flyte-propeller-config.yaml
fi

print_status "Flyte configuration updated ✅"

# Step 4: Restart Flyte Propeller
print_header "Step 4: Restarting Flyte Propeller"

print_status "Restarting Flyte Propeller to pick up new configuration..."
kubectl rollout restart deployment/flytepropeller -n $FLYTE_NAMESPACE

print_status "Waiting for Propeller to be ready..."
kubectl rollout status deployment/flytepropeller -n $FLYTE_NAMESPACE --timeout=300s

print_status "Flyte Propeller restarted ✅"

# Step 5: Verification
print_header "Step 5: Verifying installation"

print_status "Running verification checks..."

# Check if SageMaker role exists
if aws iam get-role --role-name $SAGEMAKER_ROLE_NAME >/dev/null 2>&1; then
    print_status "✅ SageMaker execution role created successfully"
else
    print_error "❌ SageMaker execution role not found"
fi

# Check if S3 structure exists
if aws s3 ls s3://$S3_BUCKET/sagemaker/ >/dev/null 2>&1; then
    print_status "✅ S3 structure created successfully"
else
    print_warning "⚠️  S3 structure verification failed (bucket may not be accessible)"
fi

# Check if Flyte Propeller is running
if kubectl get deployment flytepropeller -n $FLYTE_NAMESPACE >/dev/null 2>&1; then
    PROPELLER_STATUS=$(kubectl get deployment flytepropeller -n $FLYTE_NAMESPACE -o jsonpath='{.status.readyReplicas}')
    if [ "$PROPELLER_STATUS" -gt 0 ] 2>/dev/null; then
        print_status "✅ Flyte Propeller is running and ready"
    else
        print_warning "⚠️  Flyte Propeller is not ready yet"
    fi
else
    print_error "❌ Flyte Propeller deployment not found"
fi

# Cleanup temporary files
rm -f /tmp/sagemaker-trust-policy.json
rm -f /tmp/sagemaker-custom-policy.json
rm -f /tmp/flyte-sagemaker-policy.json
rm -f /tmp/sagemaker-plugin-config.yaml
rm -f /tmp/flyte-propeller-config.yaml

print_header "🎉 SageMaker integration setup completed!"
echo ""
echo "=========================================="
echo "✅ Setup Summary:"
echo "- SageMaker execution role: $SAGEMAKER_ROLE_NAME"
echo "- AWS Region: $AWS_REGION"
echo "- S3 Bucket: $S3_BUCKET"
echo "- Flyte Propeller updated with SageMaker plugin"
echo ""
echo "🚀 Next Steps:"
echo "1. Test the integration:"
echo "   pyflyte run src/workflows/sagemaker_batch_prediction_pipeline.py sagemaker_credit_scoring_pipeline"
echo ""
echo "2. Monitor execution:"
echo "   - Flyte Console: https://flyte.your-domain.com"
echo "   - AWS SageMaker Console: https://console.aws.amazon.com/sagemaker/"
echo ""
echo "3. Check logs:"
echo "   kubectl logs -n $FLYTE_NAMESPACE deployment/flytepropeller -f"
echo ""
echo "📚 Documentation:"
echo "   See FLYTE_SAGEMAKER_INTEGRATION.md for detailed usage examples"
echo "=========================================="
