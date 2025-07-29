# ML Workflow Deployment & Debugging Guide

This guide provides step-by-step commands for deploying and debugging ML workflows on Flyte, based on our credit scoring pipeline implementation.

## Table of Contents
1. [Prerequisites & Setup](#prerequisites--setup)
2. [Deployment Commands](#deployment-commands)
3. [Execution Commands](#execution-commands)
4. [Debugging Commands](#debugging-commands)
5. [Troubleshooting Common Issues](#troubleshooting-common-issues)
6. [Monitoring & Management](#monitoring--management)
7. [Security & Permissions](#security--permissions)

---

## Prerequisites & Setup

### 1. Environment Setup
```bash
# Ensure you're in the project directory
cd /Users/bsingh/Documents/Dev/app_flyte_wf1

# Verify required tools are installed
flytectl version          # Flyte CLI
kubectl version --client  # Kubernetes CLI
aws --version             # AWS CLI
python --version          # Python 3.9+
```

### 2. AWS Authentication
```bash
# Configure AWS credentials (use your ADFS profile)
aws configure list --profile adfs

# Update EKS kubeconfig
aws eks update-kubeconfig --region us-east-1 --name education-eks-vV8VCAqw --profile adfs
```

### 3. Connect to Flyte Cluster
```bash
# Set up port forwarding to access Flyte services
kubectl port-forward -n flyte svc/flyte-binary-grpc 8089:8089 &
kubectl port-forward -n flyte svc/flyte-binary-http 8088:8088 &

# Verify Flyte services are running
kubectl get pods -n flyte
```

### 4. Configure Flyte CLI
```bash
# Create Flyte configuration
mkdir -p .flyte
cat > .flyte/config.yaml << EOF
admin:
  endpoint: localhost:8089
  authType: Pkce
  insecure: true
logger:
  show-source: true
  level: 0
EOF

# Test connection
flytectl --config .flyte/config.yaml get projects
```

---

## Deployment Commands

### 1. Project Management

#### Create Project
```bash
# Create a new project for your ML workflows
flytectl --config .flyte/config.yaml create project \
  --id ml-workflows \
  --name "ML Workflows" \
  --description "Machine Learning workflows for credit scoring and other ML tasks"

# Verify project creation
flytectl --config .flyte/config.yaml get projects
```

#### List Existing Projects
```bash
# List all projects you have access to
flytectl --config .flyte/config.yaml get projects

# Get specific project details
flytectl --config .flyte/config.yaml get project ml-workflows
```

### 2. Workflow Registration

#### Register ML Pipeline (Recommended - Public Image)
```bash
# ✅ RECOMMENDED: Use public Flytekit image
# This is what you should use for most development work
pyflyte --config .flyte/config.yaml register \
  --project ml-workflows \
  --domain development \
  --image ghcr.io/flyteorg/flytekit:py3.9-1.10.3 \
  ml_pipeline_improved.py

# Verify registration
flytectl --config .flyte/config.yaml get workflows \
  --project ml-workflows \
  --domain development
```

#### Register with Custom Image (Advanced - Only if Needed)
```bash
# ⚠️  ADVANCED: Only use if you need custom dependencies not available in requirements.txt
# You must first build and push your custom Docker image to a registry
pyflyte --config .flyte/config.yaml register \
  --project ml-workflows \
  --domain development \
  --image your-registry/ml-workflows:v1.0 \
  ml_pipeline_improved.py
```

#### View Registered Workflows
```bash
# List all workflows in project
flytectl --config .flyte/config.yaml get workflows \
  --project ml-workflows \
  --domain development

# Get specific workflow details
flytectl --config .flyte/config.yaml get workflow \
  --project ml-workflows \
  --domain development \
  ml_pipeline_improved.credit_scoring_pipeline

# View all versions of a workflow
flytectl --config .flyte/config.yaml get workflow \
  --project ml-workflows \
  --domain development \
  ml_pipeline_improved.credit_scoring_pipeline \
  --version all
```

### 3. Launch Plan Management

#### View Launch Plans
```bash
# List launch plans (deployment configurations)
flytectl --config .flyte/config.yaml get launchplan \
  --project ml-workflows \
  --domain development \
  ml_pipeline_improved.credit_scoring_pipeline

# Get specific version
flytectl --config .flyte/config.yaml get launchplan \
  --project ml-workflows \
  --domain development \
  --version <VERSION_ID> \
  ml_pipeline_improved.credit_scoring_pipeline
```

---

## Execution Commands

### 1. Generate Execution Configuration

#### Create Execution Config File
```bash
# Generate execution configuration template
flytectl --config .flyte/config.yaml get launchplan \
  --project ml-workflows \
  --domain development \
  --version <VERSION_ID> \
  ml_pipeline_improved.credit_scoring_pipeline \
  --execFile execution_config.yaml

# View generated config
cat execution_config.yaml
```

#### Example Execution Config
```yaml
# execution_config.yaml
iamRoleARN: ""
inputs: {}
envs: {}
kubeServiceAcct: ""
targetDomain: ""
targetProject: ""
version: aEArKwFZv_gHocuye06JqQ
workflow: ml_pipeline_improved.credit_scoring_pipeline
```

### 2. Execute Workflows

#### Start Credit Scoring Pipeline
```bash
# Execute the credit scoring workflow
flytectl --config .flyte/config.yaml create execution \
  --project ml-workflows \
  --domain development \
  --execFile execution_config.yaml

# Output: execution identifier project:"ml-workflows" domain:"development" name:"<EXECUTION_ID>"
```

#### Execute Generic ML Pipeline with Custom Data
```bash
# For generic pipeline, create config with inputs
cat > generic_execution.yaml << EOF
iamRoleARN: ""
inputs:
  data_path: "s3://bsingh-ml-workflows/new-dataset/data.csv"
envs: {}
kubeServiceAcct: ""
targetDomain: ""
targetProject: ""
version: <VERSION_ID>
workflow: ml_pipeline_improved.generic_ml_pipeline
EOF

# Execute with custom data path
flytectl --config .flyte/config.yaml create execution \
  --project ml-workflows \
  --domain development \
  --execFile generic_execution.yaml
```

### 3. Monitor Executions

#### List Recent Executions
```bash
# List all executions in project
flytectl --config .flyte/config.yaml get executions \
  --project ml-workflows \
  --domain development

# List last 10 executions
flytectl --config .flyte/config.yaml get executions \
  --project ml-workflows \
  --domain development \
  --limit 10

# Filter by status
flytectl --config .flyte/config.yaml get executions \
  --project ml-workflows \
  --domain development \
  --filter "phase=RUNNING"

flytectl --config .flyte/config.yaml get executions \
  --project ml-workflows \
  --domain development \
  --filter "phase=SUCCEEDED"

flytectl --config .flyte/config.yaml get executions \
  --project ml-workflows \
  --domain development \
  --filter "phase=FAILED"
```

#### Check Specific Execution
```bash
# Get execution status
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID>

# Get detailed execution information
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o yaml

# Get execution results (outputs)
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o json | jq '.closure.outputs'
```

---

## Debugging Commands

### 1. Execution-Level Debugging

#### Get Full Execution Details
```bash
# Get complete execution information with errors
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o yaml

# Extract just the error message
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o yaml | grep -A 20 "error:"

# Get execution timeline
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o json | jq '.closure'
```

#### Check Execution Inputs/Outputs
```bash
# View execution inputs
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o json | jq '.spec.inputs'

# View execution outputs (if successful)
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o json | jq '.closure.outputs'
```

### 2. Kubernetes-Level Debugging

#### Check Pod Status
```bash
# List pods for your executions
kubectl get pods -n ml-workflows-development

# Get pod details
kubectl describe pod <POD_NAME> -n ml-workflows-development

# Check pod logs
kubectl logs <POD_NAME> -n ml-workflows-development

# Get pod YAML configuration
kubectl get pod <POD_NAME> -n ml-workflows-development -o yaml
```

#### Node and Resource Debugging
```bash
# Check node resources
kubectl get nodes
kubectl describe nodes

# Check resource usage
kubectl top nodes  # Requires metrics server

# Check pod resource requests vs limits
kubectl describe pod <POD_NAME> -n ml-workflows-development | grep -A 10 "Requests"
```

### 3. Task-Level Debugging

#### Check Individual Tasks
```bash
# List tasks in your project
flytectl --config .flyte/config.yaml get task \
  --project ml-workflows \
  --domain development

# Get specific task details
flytectl --config .flyte/config.yaml get task \
  --project ml-workflows \
  --domain development \
  ml_pipeline_improved.load_data \
  --version <VERSION_ID>

# Get task configuration
flytectl --config .flyte/config.yaml get task \
  --project ml-workflows \
  --domain development \
  ml_pipeline_improved.load_data \
  --version <VERSION_ID> \
  -o yaml
```

---

## Troubleshooting Common Issues

### 1. Pod Scheduling Issues

#### Insufficient Resources
```bash
# Symptom: Pod stuck in "Pending" state
# Check:
kubectl describe pod <POD_NAME> -n ml-workflows-development

# Look for: "Insufficient cpu" or "Insufficient memory"
# Solution: Reduce resource requests in your task decorators
```

**Fix in Code:**
```python
@task(requests=Resources(cpu="500m", mem="500Mi"), limits=Resources(cpu="1", mem="1Gi"))
def my_task():
    # Your task code
```

#### Node Affinity Issues
```bash
# Check if pods can be scheduled on available nodes
kubectl get nodes -o custom-columns="NAME:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory"

# Check node labels and taints
kubectl describe nodes
```

### 2. Image Pull Issues

#### Image Not Found
```bash
# Symptom: "ErrImagePull" or "ImagePullBackOff"
# Check pod events:
kubectl describe pod <POD_NAME> -n ml-workflows-development | grep -A 10 Events

# Use working images:
# ✅ ghcr.io/flyteorg/flytekit:py3.9-1.10.3
# ✅ python:3.9-slim (if you install dependencies)
# ❌ ml-workflows:latest (doesn't exist publicly)
```

**Fix Registration:**
```bash
# Re-register with working image
pyflyte --config .flyte/config.yaml register \
  --project ml-workflows \
  --domain development \
  --image ghcr.io/flyteorg/flytekit:py3.9-1.10.3 \
  ml_pipeline_improved.py
```

### 3. S3 Access Issues

#### Permission Denied
```bash
# Symptom: "Forbidden" or "Access Denied" in execution logs
# Check current S3 policy:
aws iam get-policy-version \
  --policy-arn arn:aws:iam::245966534215:policy/FlyteMLS3Access \
  --version-id v2 \
  --profile adfs
```

**Update S3 Policy:**
```bash
# Update policy to include all required buckets
aws iam create-policy-version \
  --policy-arn arn:aws:iam::245966534215:policy/FlyteMLS3Access \
  --policy-document file://s3-access-policy-updated.json \
  --set-as-default \
  --profile adfs
```

#### Check S3 Bucket Access
```bash
# Test bucket access
aws s3 ls s3://bsingh-ml-workflows/ --profile adfs
aws s3 ls s3://education-eks-vv8vcaqw-flyte-metadata-vv8vcaqw/ --profile adfs
aws s3 ls s3://education-eks-vv8vcaqw-flyte-userdata-vv8vcaqw/ --profile adfs
```

### 4. Authentication Issues

#### Port Forward Timeout
```bash
# Symptom: "connection refused" or "server has asked for credentials"
# Solution: Restart port forwarding

# Kill existing port forwards
pkill -f "port-forward"

# Restart port forwarding
kubectl port-forward -n flyte svc/flyte-binary-grpc 8089:8089 &
kubectl port-forward -n flyte svc/flyte-binary-http 8088:8088 &

# Test connection
flytectl --config .flyte/config.yaml get projects
```

#### Kubeconfig Expired
```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name education-eks-vV8VCAqw \
  --profile adfs

# Verify access
kubectl get pods -n flyte
```

---

## Monitoring & Management

### 1. Real-time Monitoring

#### Watch Execution Progress
```bash
# Monitor execution in real-time
watch -n 5 "flytectl --config .flyte/config.yaml get execution --project ml-workflows --domain development <EXECUTION_ID>"

# Monitor all running executions
watch -n 10 "flytectl --config .flyte/config.yaml get executions --project ml-workflows --domain development --filter 'phase=RUNNING'"

# Monitor pods
watch -n 5 "kubectl get pods -n ml-workflows-development"
```

#### Access Flyte UI
```bash
# Ensure port forwarding is active
kubectl port-forward -n flyte svc/flyte-binary-http 8088:8088 &

# Open in browser
open http://localhost:8088/console
# Or navigate manually to: http://localhost:8088/console
```

### 2. Execution Management

#### Archive Completed Executions
```bash
# Archive execution (hide from UI)
flytectl --config .flyte/config.yaml update execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  --archive

# Activate archived execution
flytectl --config .flyte/config.yaml update execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  --activate
```

### 3. Performance Analysis

#### Resource Usage Analysis
```bash
# Check execution duration
flytectl --config .flyte/config.yaml get execution \
  --project ml-workflows \
  --domain development \
  <EXECUTION_ID> \
  -o json | jq '.closure.duration'

# Compare execution times
flytectl --config .flyte/config.yaml get executions \
  --project ml-workflows \
  --domain development \
  --limit 10 \
  -o json | jq '.executions[] | {name: .id.name, duration: .closure.duration, phase: .closure.phase}'
```

---

## Security & Permissions

### 1. IAM Policy Management

#### Current S3 Policy
```json
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
                "arn:aws:s3:::education-eks-vv8vcaqw-flyte-metadata-vv8vcaqw",
                "arn:aws:s3:::education-eks-vv8vcaqw-flyte-metadata-vv8vcaqw/*",
                "arn:aws:s3:::education-eks-vv8vcaqw-flyte-userdata-vv8vcaqw",
                "arn:aws:s3:::education-eks-vv8vcaqw-flyte-userdata-vv8vcaqw/*"
            ]
        }
    ]
}
```

#### Verify IAM Permissions
```bash
# Check attached policies on node groups
aws iam list-attached-role-policies \
  --role-name node-group-1-eks-node-group-20250724035220727000000001 \
  --profile adfs

aws iam list-attached-role-policies \
  --role-name node-group-2-eks-node-group-20250724035220727200000003 \
  --profile adfs
```

### 2. Network Security

#### Port Forward Security
```bash
# ⚠️  WARNING: Port forwarding bypasses authentication
# Only use for development environments
# For production, use proper Flyte authentication

# Check active port forwards
ps aux | grep port-forward

# Kill port forwards when done
pkill -f "port-forward"
```

---

## Quick Command Reference

### Daily Operations
```bash
# 1. Connect to cluster
kubectl port-forward -n flyte svc/flyte-binary-grpc 8089:8089 &
kubectl port-forward -n flyte svc/flyte-binary-http 8088:8088 &

# 2. Deploy workflow
pyflyte --config .flyte/config.yaml register --project ml-workflows --domain development --image ghcr.io/flyteorg/flytekit:py3.9-1.10.3 ml_pipeline_improved.py

# 3. Execute workflow
flytectl --config .flyte/config.yaml create execution --project ml-workflows --domain development --execFile execution_config.yaml

# 4. Monitor execution
flytectl --config .flyte/config.yaml get execution --project ml-workflows --domain development <EXECUTION_ID>

# 5. Debug if needed
kubectl get pods -n ml-workflows-development
kubectl describe pod <POD_NAME> -n ml-workflows-development
```

### Emergency Debugging
```bash
# Quick status check
flytectl --config .flyte/config.yaml get executions --project ml-workflows --domain development --limit 5

# Quick error check
flytectl --config .flyte/config.yaml get execution --project ml-workflows --domain development <EXECUTION_ID> -o yaml | grep -A 20 error

# Quick pod check
kubectl get pods -n ml-workflows-development
kubectl describe pod <POD_NAME> -n ml-workflows-development | tail -20
```

---

This guide provides all the commands you need to successfully deploy, execute, and debug your ML workflows on Flyte. Keep this as a reference for your daily operations!
