# Flyte Architecture & Workflow Guide

## 🏗️ Two-Level Flyte Architecture Overview

Flyte operates on a **two-level architecture** that separates orchestration from code execution, providing scalability, isolation, and flexibility.

### Level 1: Flyte Control Plane (EKS Cluster)

```
┌─────────────────────────────────────────┐
│           EKS Cluster                   │
│  ┌─────────────────────────────────┐    │
│  │     Flyte Services              │    │
│  │  • flyte-admin (API Server)    │    │
│  │  • flyte-propeller (Engine)    │    │
│  │  • flyte-datacatalog (Data)    │    │
│  │  • flyte-console (Web UI)      │    │
│  │                                 │    │
│  │  🎯 ROLE: Orchestrator Only    │    │
│  │  • Stores workflow definitions │    │
│  │  • Manages execution graph     │    │
│  │  • Creates Kubernetes pods     │    │
│  │  • NO business logic           │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Components:**
- **flyte-admin**: REST API server for workflow management
- **flyte-propeller**: Workflow execution engine
- **flyte-datacatalog**: Data lineage and metadata management
- **flyte-console**: Web-based user interface

**Key Characteristics:**
- ✅ Language-agnostic orchestration
- ✅ No business logic embedded
- ✅ Scalable and fault-tolerant
- ✅ Manages workflow state and dependencies

### Level 2: Your Application Images (Docker Registry)

```
┌─────────────────────────────────────────┐
│        Docker Registry                  │
│  ┌─────────────────────────────────┐    │
│  │    my-flyte-app:v3.0           │    │
│  │  • Ubuntu 20.04 + Python      │    │
│  │  • flytekit                    │    │
│  │  • YOUR workflow code          │    │
│  │  • YOUR dependencies           │    │
│  │  • YOUR data files             │    │
│  │                                 │    │
│  │  🎯 ROLE: Code Execution       │    │
│  │  • Contains ALL business logic │    │
│  │  • Self-contained environment  │    │
│  │  • Pulled by Flyte when needed │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Key Characteristics:**
- ✅ Self-contained execution environment
- ✅ Version-controlled code and dependencies
- ✅ Reproducible across environments
- ✅ Language and framework flexibility

## 🔄 Complete Development & Deployment Workflow

### Phase 1: Development & Building

#### Step 1: Write Your Code
```bash
# Single file approach
batch_prediction_pipeline.py

# Multi-file approach (recommended for larger projects)
my-flyte-project/
├── workflows/
│   ├── __init__.py
│   ├── batch_prediction.py
│   └── data_ingestion.py
├── tasks/
│   ├── __init__.py
│   ├── data_processing.py
│   ├── ml_training.py
│   └── reporting.py
├── utils/
│   ├── __init__.py
│   ├── data_validation.py
│   └── model_utils.py
├── config.py
├── requirements.txt
└── Dockerfile.custom
```

#### Step 2: Create Dockerfile
```dockerfile
# Example: Dockerfile.custom
FROM ubuntu:20.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    python3.9-dev \
    gcc g++ curl git

# Set Python as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

# Install flytekit
RUN pip install --no-cache-dir flytekit==1.10.3

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🔑 CRITICAL: Copy your application code
COPY . .

# Security: Create non-root user
RUN useradd -m -u 1000 flyte
RUN chown -R flyte:flyte /app
USER flyte

# Environment setup
ENV PYTHONPATH=/app
ENV FLYTE_INTERNAL_IMAGE=true
```

#### Step 3: Build Docker Image
```bash
# Build image with embedded code
docker build -f Dockerfile.custom -t my-flyte-app:v3.0 .

# Verify build
docker run --rm my-flyte-app:v3.0 ls -la /app/
```

### Phase 2: Registration

#### Step 4: Push to Registry (Production)
```bash
# Tag for registry
docker tag my-flyte-app:v3.0 your-registry.com/my-flyte-app:v3.0

# Push to registry
docker push your-registry.com/my-flyte-app:v3.0
```

#### Step 5: Register Workflows with Flyte

**Single File Registration:**
```bash
pyflyte register --image your-registry.com/my-flyte-app:v3.0 batch_prediction_pipeline.py
```

**Multi-File Registration Options:**
```bash
# Option 1: Register everything
pyflyte register --image your-registry.com/my-flyte-app:v3.0 .

# Option 2: Register specific workflow file (auto-imports tasks)
pyflyte register --image your-registry.com/my-flyte-app:v3.0 workflows/ml_workflows.py

# Option 3: Register specific directories
pyflyte register --image your-registry.com/my-flyte-app:v3.0 tasks/ workflows/
```

**What Registration Does:**
- 🔍 **Code Analysis**: Scans for `@task` and `@workflow` decorators
- 📊 **Graph Creation**: Builds workflow dependency graphs
- 🗄️ **Metadata Storage**: Stores definitions in Flyte database
- 🔗 **Image Linking**: Associates each entity with Docker image
- 📝 **Blueprint Creation**: Creates execution templates

### Phase 3: Execution

#### Step 6: Execute Workflows

**Command Line:**
```bash
# Execute workflow
flytectl execute --project myproject --domain development batch_prediction_workflow

# Execute with parameters
flytectl execute --project myproject --domain development batch_prediction_workflow \
  --input prediction_data_path=s3://bucket/data.csv
```

**Web UI:**
1. Navigate to Flyte Console
2. Select Project → Domain
3. Choose Workflow
4. Click "Launch" → Configure inputs → Execute

**What Happens During Execution:**
1. 🎯 **Lookup**: Flyte finds workflow definition in database
2. 📋 **Planning**: Creates execution plan with task dependencies
3. 🏗️ **Pod Creation**: For each task, creates Kubernetes pod
4. 🐳 **Image Pull**: Pod pulls your Docker image
5. ▶️ **Code Execution**: Runs specific task using embedded code
6. 🔄 **Data Flow**: Results flow between tasks per workflow graph
7. ✅ **Completion**: Workflow completes with final outputs

## 🎯 Key Concepts Explained

### COPY . . in Dockerfile

**Purpose**: Embeds your entire codebase into the Docker image

```dockerfile
# Before COPY . .
/app/  # Empty directory

# After COPY . .
/app/
├── batch_prediction_pipeline.py  ← Your code
├── CleanCreditScoring.csv        ← Your data
├── requirements.txt              ← Your deps
└── (all other files...)          ← Everything
```

**Why This Matters:**
- ✅ Code becomes **part of the image**
- ✅ No runtime code downloads needed
- ✅ Reproducible environments
- ✅ Version-controlled deployments

### Registration vs Execution

| Phase | Purpose | Action | Result |
|-------|---------|--------|--------|
| **Registration** | Analysis | `pyflyte register` | Workflow definitions stored |
| **Execution** | Running | `flytectl execute` | Tasks run in containers |

**Registration Time:**
- 📝 Code is **analyzed** for structure
- 🔗 Workflows are **linked** to Docker images
- 🗄️ Metadata is **stored** in Flyte database

**Execution Time:**
- 🐳 Docker images are **pulled**
- ▶️ Embedded code is **executed**
- 🔄 Results **flow** between tasks

### Multi-File Organization Benefits

**Advantages:**
- 🎯 **Separation of Concerns**: Tasks, workflows, utilities separated
- 🔄 **Reusability**: Tasks can be shared across workflows
- 🧪 **Testability**: Individual components easily tested
- 👥 **Team Collaboration**: Multiple developers can work simultaneously
- 📈 **Scalability**: Easier to manage large codebases

**Registration Behavior:**
- Imports are **automatically discovered**
- Dependencies are **resolved** during registration
- All referenced tasks are **included** in registration

## 🔧 Common Patterns & Best Practices

### Project Structure (Recommended)
```
my-flyte-project/
├── workflows/           # Workflow definitions
├── tasks/              # Reusable task definitions
├── utils/              # Helper functions
├── config/             # Configuration files
├── data/               # Sample/test data
├── tests/              # Unit tests
├── Dockerfile.custom   # Container definition
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project metadata
└── README.md          # Documentation
```

### Docker Best Practices
```dockerfile
# Multi-stage builds for smaller images
FROM python:3.9-slim as base
FROM base as dependencies
# ... install dependencies
FROM dependencies as final
# ... copy code and configure

# Use specific versions
RUN pip install flytekit==1.10.3

# Security: Non-root user
USER flyte

# Optimization: Layer caching
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # Copy code last for better caching
```

### Development Workflow
1. **Local Development**: Test tasks and workflows locally
2. **Build & Test**: Build Docker image and test functionality
3. **Register**: Register with development Flyte cluster
4. **Test Execution**: Run workflows in development environment
5. **Production Deploy**: Push to production registry and register

## � Security Architecture & Access Control

### Multi-Layer Security Model

Flyte implements defense-in-depth security across multiple layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  1. AWS IAM (Cloud Infrastructure)                 │    │
│  │     • EKS Cluster Access                           │    │
│  │     • S3 Bucket Permissions                        │    │
│  │     • ECR Registry Access                          │    │
│  │     • Cross-Account Roles                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  2. Kubernetes RBAC (Cluster Level)                │    │
│  │     • Service Account Permissions                  │    │
│  │     • Namespace Isolation                          │    │
│  │     • Pod Security Policies                        │    │
│  │     • Network Policies                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  3. Flyte Authorization (Application Level)        │    │
│  │     • Project-based Access Control                 │    │
│  │     • Domain Isolation                             │    │
│  │     • Workflow Execution Permissions               │    │
│  │     • User Authentication                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  4. Container Security (Runtime Level)             │    │
│  │     • Non-root User Execution                      │    │
│  │     • Image Vulnerability Scanning                 │    │
│  │     • Resource Limits & Quotas                     │    │
│  │     • Secrets Management                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1. AWS IAM Security Layer

#### EKS Cluster IAM Roles
```yaml
# flyte-cluster-role.yaml
apiVersion: iam.aws.amazon.com/v1
kind: Role
metadata:
  name: FlytePlatformRole
spec:
  assumeRolePolicyDocument:
    Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Principal:
          Service: eks.amazonaws.com
        Action: sts:AssumeRole
  managedPolicyArns:
    - arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
    - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
```

#### Service Account IAM Integration (IRSA)
```yaml
# flyte-sa-iam-policy.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flyte-workflow-runner
  namespace: flyte-production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/FlyteWorkflowExecutionRole
---
apiVersion: iam.aws.amazon.com/v1
kind: Policy
metadata:
  name: FlyteWorkflowExecutionPolicy
spec:
  policyDocument:
    Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - s3:GetObject
          - s3:PutObject
          - s3:DeleteObject
        Resource: 
          - "arn:aws:s3:::flyte-data-bucket/*"
      - Effect: Allow
        Action:
          - ecr:GetAuthorizationToken
          - ecr:BatchCheckLayerAvailability
          - ecr:GetDownloadUrlForLayer
        Resource: "*"
```

#### Cross-Account Access Patterns
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::DEV-ACCOUNT:role/FlyteDevRole"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "flyte-dev-external-id"
        }
      }
    }
  ]
}
```

### 2. Kubernetes RBAC Security Layer

#### Namespace-Based Isolation
```yaml
# flyte-namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: flyte-production
  labels:
    environment: production
    security-tier: high
---
apiVersion: v1
kind: Namespace
metadata:
  name: flyte-development
  labels:
    environment: development
    security-tier: medium
```

#### Service Account RBAC
```yaml
# flyte-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flyte-workflow-executor
rules:
  - apiGroups: [""]
    resources: ["pods", "configmaps", "secrets"]
    verbs: ["get", "list", "create", "update", "delete"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "create", "update", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flyte-workflow-executor-binding
subjects:
  - kind: ServiceAccount
    name: flyte-workflow-runner
    namespace: flyte-production
roleRef:
  kind: ClusterRole
  name: flyte-workflow-executor
  apiGroup: rbac.authorization.k8s.io
```

#### Pod Security Standards
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: flyte-restricted-psp
spec:
  runAsUser:
    rule: MustRunAsNonRoot
    ranges:
      - min: 1000
        max: 65535
  runAsGroup:
    rule: MustRunAs
    ranges:
      - min: 1000
        max: 65535
  fsGroup:
    rule: MustRunAs
    ranges:
      - min: 1000
        max: 65535
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'persistentVolumeClaim'
```

#### Network Policies
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flyte-isolation-policy
  namespace: flyte-production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: flyte-system
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: flyte-system
    - to: []
      ports:
        - protocol: TCP
          port: 443  # HTTPS only
```

### 3. Flyte Application Security Layer

#### Authentication Configuration
```yaml
# flyte-auth-config.yaml
auth:
  enabled: true
  # OIDC Authentication
  oidc:
    baseUrl: "https://your-identity-provider.com"
    clientId: "flyte-production-client"
    clientSecret: "secret-from-k8s-secret"
  # Internal authentication for service-to-service
  internal:
    enabled: true
    secretName: "flyte-internal-auth"
```

#### Project-Based Access Control
```yaml
# flyte-projects.yaml
projects:
  - name: "ml-production"
    domains:
      - name: "production"
        security:
          authentication: "required"
          authorization: "rbac"
          users:
            - "ml-team@company.com"
          groups:
            - "data-science-team"
      - name: "staging"
        security:
          authentication: "required"
          authorization: "rbac"
          users:
            - "ml-team@company.com"
            - "qa-team@company.com"
```

#### Role-Based Permissions
```python
# Flyte Admin RBAC Configuration
rbac_config = {
    "roles": {
        "ml_engineer": {
            "permissions": [
                "workflows:execute",
                "workflows:read",
                "launchplans:create",
                "executions:read"
            ],
            "projects": ["ml-production", "ml-development"]
        },
        "data_scientist": {
            "permissions": [
                "workflows:read",
                "executions:read",
                "data:read"
            ],
            "projects": ["ml-development"]
        },
        "platform_admin": {
            "permissions": ["*"],
            "projects": ["*"]
        }
    }
}
```

### 4. Container Security Layer

#### Secure Dockerfile Practices
```dockerfile
# Security-hardened Dockerfile
FROM ubuntu:20.04

# Install security updates first
RUN apt-get update && apt-get upgrade -y

# Install only necessary packages
RUN apt-get install -y \
    python3.9 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user EARLY in build
RUN groupadd -r flyte && useradd -r -g flyte -u 1000 flyte

# Set up secure directories
WORKDIR /app
RUN chown -R flyte:flyte /app

# Copy and install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=flyte:flyte . .

# Switch to non-root user BEFORE CMD
USER flyte

# Security headers and environment
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLYTE_INTERNAL_IMAGE=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-c", "print('Secure Flyte container ready')"]
```

#### Secrets Management
```yaml
# secrets-management.yaml
apiVersion: v1
kind: Secret
metadata:
  name: flyte-workflow-secrets
  namespace: flyte-production
type: Opaque
data:
  database-password: <base64-encoded-password>
  api-key: <base64-encoded-api-key>
---
# Secret injection in workflow
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: workflow-container
      image: my-flyte-app:v3.0
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: flyte-workflow-secrets
              key: database-password
```

#### Runtime Security Scanning
```python
# Example: Security-conscious task definition
from flytekit import task, Resources, Secret

@task(
    requests=Resources(cpu="100m", mem="128Mi"),
    limits=Resources(cpu="500m", mem="512Mi"),
    secret_requests=[Secret(group="production", key="api-key")]
)
def secure_data_processing_task(data_path: str) -> str:
    """
    Security-hardened task with:
    - Resource limits to prevent resource exhaustion
    - Secret injection for sensitive data
    - Minimal resource requests
    """
    import os
    
    # Access injected secret securely
    api_key = os.environ.get("FLYTE_SECRETS_production_api-key")
    
    # Your secure processing logic here
    return "processed_data_path"
```

### Security Best Practices Checklist

#### Infrastructure Security
- ✅ **EKS Cluster**: Private subnets, endpoint access control
- ✅ **VPC Security**: Security groups, NACLs, VPC endpoints
- ✅ **IAM Roles**: Least privilege principle, IRSA integration
- ✅ **ECR Security**: Image vulnerability scanning, lifecycle policies

#### Kubernetes Security
- ✅ **RBAC**: Granular permissions, service account isolation
- ✅ **Pod Security**: Non-root users, security contexts, admission controllers
- ✅ **Network Security**: Network policies, service mesh (optional)
- ✅ **Secrets**: Kubernetes secrets, external secret operators

#### Application Security
- ✅ **Authentication**: OIDC integration, multi-factor authentication
- ✅ **Authorization**: Project-based access, role-based permissions
- ✅ **Audit Logging**: Comprehensive audit trails, log analysis
- ✅ **Data Security**: Encryption at rest and in transit

#### Container Security
- ✅ **Base Images**: Distroless images, regular updates, vulnerability scanning
- ✅ **Runtime Security**: Non-root execution, read-only file systems
- ✅ **Resource Limits**: CPU/memory limits, resource quotas
- ✅ **Secrets Management**: External secret stores, rotation policies

### Security Monitoring & Compliance

#### Audit Configuration
```yaml
# flyte-audit-config.yaml
audit:
  enabled: true
  webhook:
    endpoint: "https://audit-collector.company.com/flyte"
  events:
    - "workflow.execution.started"
    - "workflow.execution.completed"
    - "workflow.execution.failed"
    - "user.authentication.success"
    - "user.authentication.failure"
    - "admin.configuration.changed"
```

#### Compliance Monitoring
```python
# Example: Compliance-aware workflow
from flytekit import workflow, task
from typing import Dict, Any

@task
def compliance_check(data_path: str) -> Dict[str, Any]:
    """Verify data compliance before processing"""
    return {
        "pii_detected": False,
        "data_classification": "internal",
        "compliance_status": "approved"
    }

@workflow
def compliant_ml_workflow(input_data: str) -> str:
    """Workflow with built-in compliance checks"""
    
    # Mandatory compliance verification
    compliance_result = compliance_check(data_path=input_data)
    
    # Conditional processing based on compliance
    if compliance_result["compliance_status"] == "approved":
        # Continue with ML processing
        return process_data(input_data)
    else:
        # Log and halt for non-compliant data
        raise ValueError("Data failed compliance check")
```

## �🚀 Advanced Topics

### Environment-Specific Configurations
```python
# config.py
import os

ENVIRONMENT = os.getenv('FLYTE_ENV', 'development')

if ENVIRONMENT == 'production':
    DATA_PATH = 's3://prod-bucket/data/'
    SECURITY_LEVEL = 'high'
    AUDIT_ENABLED = True
else:
    DATA_PATH = '/app/data/'
    SECURITY_LEVEL = 'medium'
    AUDIT_ENABLED = False
```

### Resource Management
```python
@task(
    requests=Resources(cpu="500m", mem="1Gi"),
    limits=Resources(cpu="1", mem="2Gi")
)
def heavy_computation_task():
    # Task implementation
    pass
```

### Error Handling & Retries
```python
@task(retries=3, timeout=timedelta(minutes=30))
def robust_task():
    # Task that might fail
    pass
```

## 🎯 Summary

**The Magic of Flyte's Two-Level Architecture:**

1. **Separation of Concerns**: Orchestration (Flyte) vs Code Execution (Your Images)
2. **Scalability**: Control plane scales independently from workloads
3. **Flexibility**: Any language, any framework, any dependencies
4. **Reproducibility**: Version-controlled images ensure consistent execution
5. **Isolation**: Each task runs in its own container environment

**Key Takeaway**: Flyte = **Smart Orchestrator** + **Your Containerized Code** 🚀

The beauty lies in this separation - Flyte handles the complex orchestration while your business logic lives in portable, reproducible Docker containers.
