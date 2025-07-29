# Flyte Multi-Tenant Architecture Guide

## 🏢 Multi-Tenant Flyte Deployment Strategy

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Central EKS Cluster                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                Flyte Control Plane                     │    │
│  │  • flyte-admin (Multi-tenant API)                     │    │
│  │  • flyte-propeller (Workflow Engine)                  │    │
│  │  • flyte-datacatalog (Data Management)                │    │
│  │  • flyte-console (Multi-tenant UI)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│  ┌─────────────────────────┼─────────────────────────────────┐    │
│  │         Tenant Isolation Layer                         │    │
│  │                         │                             │    │
│  │  ┌─────────────────┬────┴────┬─────────────────┐      │    │
│  │  │   Team Alpha    │ Team Beta│   Team Gamma    │      │    │
│  │  │                 │          │                 │      │    │
│  │  │ Projects:       │Projects: │ Projects:       │      │    │
│  │  │ • ml-alpha      │• data-   │ • analytics-    │      │    │
│  │  │ • web-alpha     │  beta    │   gamma         │      │    │
│  │  │                 │• api-    │ • reports-      │      │    │
│  │  │ Domains:        │  beta    │   gamma         │      │    │
│  │  │ • dev, staging, │          │                 │      │    │
│  │  │   production    │Domains:  │ Domains:        │      │    │
│  │  │                 │• dev,    │ • dev,          │      │    │
│  │  │ Workflows:      │  prod    │   production    │      │    │
│  │  │ • Only Alpha's  │          │                 │      │    │
│  │  │   workflows     │Workflows:│ Workflows:      │      │    │
│  │  │                 │• Only    │ • Only Gamma's  │      │    │
│  │  │                 │  Beta's  │   workflows     │      │    │
│  │  │                 │  workflows│                │      │    │
│  │  └─────────────────┴──────────┴─────────────────┘      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Multi-Tenancy Configuration

### 1. Project-Based Isolation

#### Project Structure
```yaml
# flyte-projects-config.yaml
projects:
  # Team Alpha Projects
  - id: "ml-alpha"
    name: "Machine Learning - Team Alpha"
    description: "ML workflows for Team Alpha"
    domains:
      - id: "development"
        name: "Development Environment"
      - id: "staging" 
        name: "Staging Environment"
      - id: "production"
        name: "Production Environment"
    
  - id: "web-alpha"
    name: "Web Services - Team Alpha"
    description: "Web application workflows for Team Alpha"
    domains:
      - id: "development"
        name: "Development Environment"
      - id: "production"
        name: "Production Environment"

  # Team Beta Projects  
  - id: "data-beta"
    name: "Data Processing - Team Beta"
    description: "Data processing workflows for Team Beta"
    domains:
      - id: "development"
        name: "Development Environment"
      - id: "production"
        name: "Production Environment"
        
  - id: "api-beta"
    name: "API Services - Team Beta"
    description: "API workflows for Team Beta"
    domains:
      - id: "development"
        name: "Development Environment"
      - id: "production"
        name: "Production Environment"

  # Team Gamma Projects
  - id: "analytics-gamma"
    name: "Analytics - Team Gamma"
    description: "Analytics workflows for Team Gamma"
    domains:
      - id: "development"
        name: "Development Environment"
      - id: "production"
        name: "Production Environment"
```

### 2. User Authentication & Authorization

#### Identity Provider Integration
```yaml
# flyte-auth-config.yaml
auth:
  enabled: true
  
  # OIDC Configuration (e.g., Auth0, Okta, AWS Cognito)
  oidc:
    issuer: "https://your-company.auth0.com/"
    clientId: "flyte-multi-tenant-client"
    clientSecret: "your-client-secret"
    scopes: ["openid", "profile", "email", "groups"]
    
  # User attribute mapping
  userAuth:
    # Map OIDC claims to Flyte user attributes
    openId:
      baseUrl: "https://your-company.auth0.com/"
      scopes: ["openid", "profile", "email", "groups"]
      clientId: "flyte-client"
    
  # Internal service authentication
  internal:
    enabled: true
    clientId: "flyte-internal"
    clientSecretName: "flyte-internal-secret"
```

#### Role-Based Access Control (RBAC)
```yaml
# flyte-rbac-config.yaml
authorization:
  enabled: true
  
  # Define roles and their permissions
  roles:
    # Team Alpha Roles
    alpha-developer:
      permissions:
        - "workflows:create"
        - "workflows:read"
        - "workflows:execute" 
        - "launchplans:create"
        - "launchplans:read"
        - "executions:read"
        - "executions:create"
      projects: ["ml-alpha", "web-alpha"]
      domains: ["development", "staging"]
      
    alpha-senior:
      permissions:
        - "workflows:create"
        - "workflows:read"
        - "workflows:execute"
        - "workflows:update"
        - "launchplans:create"
        - "launchplans:read"
        - "launchplans:update"
        - "executions:read"
        - "executions:create"
        - "executions:terminate"
      projects: ["ml-alpha", "web-alpha"]
      domains: ["development", "staging", "production"]
    
    # Team Beta Roles  
    beta-developer:
      permissions:
        - "workflows:create"
        - "workflows:read"
        - "workflows:execute"
        - "launchplans:create"
        - "launchplans:read"
        - "executions:read"
        - "executions:create"
      projects: ["data-beta", "api-beta"]
      domains: ["development"]
      
    beta-lead:
      permissions:
        - "workflows:create"
        - "workflows:read"
        - "workflows:execute"
        - "workflows:update"
        - "launchplans:create"
        - "launchplans:read"
        - "launchplans:update"
        - "executions:read"
        - "executions:create"
        - "executions:terminate"
      projects: ["data-beta", "api-beta"]
      domains: ["development", "production"]
    
    # Team Gamma Roles
    gamma-analyst:
      permissions:
        - "workflows:create"
        - "workflows:read"
        - "workflows:execute"
        - "launchplans:create"
        - "launchplans:read"
        - "executions:read"
        - "executions:create"
      projects: ["analytics-gamma"]
      domains: ["development", "production"]
  
  # User-to-role mappings
  userRoles:
    # Team Alpha Users
    "alice@company.com":
      roles: ["alpha-developer"]
    "bob@company.com":
      roles: ["alpha-senior"]
    
    # Team Beta Users
    "charlie@company.com":
      roles: ["beta-developer"]
    "diana@company.com":
      roles: ["beta-lead"]
    
    # Team Gamma Users
    "eve@company.com":
      roles: ["gamma-analyst"]
  
  # Group-based role assignment (if using groups from OIDC)
  groupRoles:
    "team-alpha-developers":
      roles: ["alpha-developer"]
    "team-alpha-seniors":
      roles: ["alpha-senior"]
    "team-beta-developers": 
      roles: ["beta-developer"]
    "team-beta-leads":
      roles: ["beta-lead"]
    "team-gamma-analysts":
      roles: ["gamma-analyst"]
```

### 3. Namespace Isolation Strategy

#### Kubernetes Namespace Setup
```yaml
# k8s-namespace-isolation.yaml
# Namespace for each team's workflow execution
apiVersion: v1
kind: Namespace
metadata:
  name: flyte-execution-alpha
  labels:
    team: "alpha"
    flyte.org/tenant: "team-alpha"
---
apiVersion: v1
kind: Namespace
metadata:
  name: flyte-execution-beta
  labels:
    team: "beta"
    flyte.org/tenant: "team-beta"
---
apiVersion: v1
kind: Namespace
metadata:
  name: flyte-execution-gamma
  labels:
    team: "gamma"
    flyte.org/tenant: "team-gamma"
```

#### Resource Quotas per Team
```yaml
# team-resource-quotas.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-alpha-quota
  namespace: flyte-execution-alpha
spec:
  hard:
    requests.cpu: "10"      # 10 CPU cores
    requests.memory: "20Gi" # 20GB RAM
    limits.cpu: "20"        # 20 CPU cores max
    limits.memory: "40Gi"   # 40GB RAM max
    pods: "50"              # Max 50 pods
    persistentvolumeclaims: "10"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-beta-quota
  namespace: flyte-execution-beta
spec:
  hard:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
    pods: "40"
    persistentvolumeclaims: "8"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-gamma-quota
  namespace: flyte-execution-gamma
spec:
  hard:
    requests.cpu: "5"
    requests.memory: "10Gi"
    limits.cpu: "10"
    limits.memory: "20Gi"
    pods: "25"
    persistentvolumeclaims: "5"
```

### 4. Flyte Admin Configuration for Multi-Tenancy

#### Admin Service Configuration
```yaml
# flyte-admin-config.yaml
admin:
  # Project and domain management
  projectDomainAttributes:
    # Team Alpha project configurations
    ml-alpha:
      development:
        executionClusterLabel:
          value: "team-alpha-cluster"
        executionQueueAttributes:
          tags: ["team-alpha", "development"]
        workflowExecutionConfig:
          maxParallelism: 10
          securityContext:
            runAsUser: 1000
            runAsGroup: 1000
      production:
        executionClusterLabel:
          value: "team-alpha-cluster"
        executionQueueAttributes:
          tags: ["team-alpha", "production"]
        workflowExecutionConfig:
          maxParallelism: 5
          securityContext:
            runAsUser: 1000
            runAsGroup: 1000
    
    # Team Beta project configurations
    data-beta:
      development:
        executionClusterLabel:
          value: "team-beta-cluster"
        executionQueueAttributes:
          tags: ["team-beta", "development"]
        workflowExecutionConfig:
          maxParallelism: 8
      production:
        executionClusterLabel:
          value: "team-beta-cluster"
        executionQueueAttributes:
          tags: ["team-beta", "production"]
        workflowExecutionConfig:
          maxParallelism: 4
  
  # Cluster resource management
  clusters:
    clusterConfigs:
      team-alpha-cluster:
        endpoint: "https://flyte-cluster.company.com"
        auth:
          type: "Pkce"
        executionNamespace: "flyte-execution-alpha"
        
      team-beta-cluster:
        endpoint: "https://flyte-cluster.company.com" 
        auth:
          type: "Pkce"
        executionNamespace: "flyte-execution-beta"
        
      team-gamma-cluster:
        endpoint: "https://flyte-cluster.company.com"
        auth:
          type: "Pkce"
        executionNamespace: "flyte-execution-gamma"
```

## 🛠️ Implementation Guide

### Step 1: Deploy Central Flyte Cluster

#### EKS Cluster Setup
```bash
# Create EKS cluster for multi-tenant Flyte
eksctl create cluster \
  --name flyte-multi-tenant \
  --version 1.24 \
  --region us-west-2 \
  --nodegroup-name multi-tenant-nodes \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --ssh-access \
  --ssh-public-key ~/.ssh/id_rsa.pub \
  --managed

# Install Flyte with multi-tenancy enabled
helm repo add flyteorg https://flyteorg.github.io/flyte
helm repo update

# Install with custom values for multi-tenancy
helm install flyte flyteorg/flyte-core \
  --namespace flyte-system \
  --create-namespace \
  --values flyte-multi-tenant-values.yaml
```

#### Multi-Tenant Helm Values
```yaml
# flyte-multi-tenant-values.yaml
flyte-admin:
  env:
    - name: FLYTE_ADMIN_CONFIG_PATH
      value: "/etc/flyte/config/admin.yaml"
  configmap:
    adminServer:
      auth:
        enabled: true
        oidc:
          issuer: "https://your-company.auth0.com/"
          clientId: "flyte-client"
        authorizer:
          enabled: true
    
flyte-propeller:
  env:
    - name: FLYTE_PROPELLER_CONFIG_PATH
      value: "/etc/flyte/config/propeller.yaml"
  configmap:
    propeller:
      workflowNamespace: "flyte-execution-{{ .Values.tenant }}"
      
flyte-console:
  env:
    - name: ADMIN_API_URL
      value: "https://flyte-admin.company.com"
```

### Step 2: User Workflow Development

#### Team Member Workflow Creation
```python
# team_alpha_workflow.py
from flytekit import task, workflow, Resources
import pandas as pd

# Team Alpha can only register to their projects
PROJECT = "ml-alpha"  # Only Alpha projects allowed
DOMAIN = "development"  # Based on user permissions

@task(requests=Resources(cpu="200m", mem="500Mi"))
def load_alpha_data(data_path: str) -> pd.DataFrame:
    """Load data - only accessible by Team Alpha"""
    # This task will run in flyte-execution-alpha namespace
    df = pd.read_csv(data_path)
    return df

@task(requests=Resources(cpu="500m", mem="1Gi"))
def process_alpha_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process data for Team Alpha"""
    # Alpha-specific processing
    processed_df = df.groupby('category').mean()
    return processed_df

@workflow
def alpha_ml_workflow(input_path: str) -> pd.DataFrame:
    """Team Alpha ML Workflow - isolated from other teams"""
    data = load_alpha_data(data_path=input_path)
    result = process_alpha_data(df=data)
    return result
```

#### Registration with Project Specification
```bash
# Team Alpha member registers workflow
pyflyte register \
  --project ml-alpha \
  --domain development \
  --image team-alpha-registry.com/ml-workflows:v1.0 \
  team_alpha_workflow.py

# Team Beta member registers workflow (different project)
pyflyte register \
  --project data-beta \
  --domain development \
  --image team-beta-registry.com/data-workflows:v1.0 \
  team_beta_workflow.py
```

### Step 3: Access Control Verification

#### User Access Testing
```bash
# Test Team Alpha user access
flytectl get workflows \
  --project ml-alpha \
  --domain development
# ✅ Success - can see Alpha workflows

flytectl get workflows \
  --project data-beta \
  --domain development
# ❌ Access Denied - cannot see Beta workflows

# Test Team Beta user access
flytectl get workflows \
  --project data-beta \
  --domain development
# ✅ Success - can see Beta workflows

flytectl get workflows \
  --project ml-alpha \
  --domain development
# ❌ Access Denied - cannot see Alpha workflows
```

## 🔒 Security & Isolation Features

### Data Isolation
```python
# Each team has isolated data access
@task
def team_alpha_data_access():
    # Can only access Alpha S3 buckets
    return s3_client.get_object(
        Bucket='team-alpha-data-bucket',
        Key='alpha-dataset.csv'
    )

@task  
def team_beta_data_access():
    # Can only access Beta S3 buckets
    return s3_client.get_object(
        Bucket='team-beta-data-bucket', 
        Key='beta-dataset.csv'
    )
```

### Resource Isolation
```yaml
# Each team gets dedicated compute resources
executionConfig:
  taskPlugins:
    default-for-task-types:
      container:
        resources:
          requests:
            cpu: 100m
            memory: 200Mi
          limits:
            cpu: 500m
            memory: 1Gi
        # Team-specific node selectors
        nodeSelector:
          team: "{{ .Values.team }}"
```

### Network Isolation
```yaml
# Network policies for team isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: team-alpha-isolation
  namespace: flyte-execution-alpha
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
  - from:
    - namespaceSelector:
        matchLabels:
          team: alpha
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: flyte-system
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

## 📊 Multi-Tenant Operations

### Team-Specific Monitoring
```yaml
# Prometheus monitoring per team
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flyte-team-alpha-metrics
spec:
  selector:
    matchLabels:
      team: alpha
  endpoints:
  - port: metrics
    path: /metrics
```

### Audit & Compliance
```yaml
# Audit configuration for multi-tenancy
audit:
  enabled: true
  events:
    - type: "workflow.execution"
      metadata:
        - "user.id"
        - "project.id" 
        - "team.id"
        - "resource.usage"
  destinations:
    - type: "elasticsearch"
      config:
        index: "flyte-audit-{{ .Values.team }}"
```

## 🎯 Key Benefits Achieved

✅ **Complete Tenant Isolation**: Teams cannot access each other's workflows
✅ **Project-Based Organization**: Users specify projects during registration
✅ **Role-Based Permissions**: Fine-grained access control per team/role
✅ **Resource Isolation**: Dedicated compute resources per team
✅ **Data Security**: Team-specific data access patterns
✅ **Namespace Separation**: Kubernetes-level isolation
✅ **Audit Trail**: Complete visibility into multi-tenant operations
✅ **Self-Service**: Teams can create workflows within their assigned projects
✅ **Scalable Architecture**: Central cluster supports multiple teams efficiently

This architecture provides exactly what you need: a centralized Flyte cluster with secure multi-tenancy where teams can only access their own projects and workflows! 🚀
