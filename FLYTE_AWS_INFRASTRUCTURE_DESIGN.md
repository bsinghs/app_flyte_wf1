# Flyte AWS Infrastructure Design

A comprehensive guide for deploying Flyte on AWS with EKS, PostgreSQL, and multi-compute execution including external platforms like Codeweave.

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [CDAO SDK Integration](#cdao-sdk-integration)
3. [Infrastructure Components](#infrastructure-components)
4. [Flyte Propeller & Plugin Architecture](#flyte-propeller--plugin-architecture)
5. [Network Architecture](#network-architecture)
6. [Access Roles & Security](#access-roles--security)
7. [Multi-Compute Execution](#multi-compute-execution)
8. [User Workflow with CDAO SDK](#user-workflow-with-cdao-sdk)
9. [Deployment Flow](#deployment-flow)
10. [Configuration Examples](#configuration-examples)

---

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Control Plane Account - AWS"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Private Subnets"
                subgraph "EKS Cluster"
                    FA[Flyte Admin<br/>Control Plane API]
                    FP[Flyte Propeller<br/>Plugin Orchestrator]
                    FC[Flyte Console<br/>Web UI]
                    FDC[FlyteDC<br/>Data Catalog]
                end
                
                subgraph "Data Layer"
                    RDS[(PostgreSQL RDS<br/>Metadata Store)]
                    S3[S3 Buckets<br/>Artifact Storage]
                end
            end
            
            subgraph "Public Subnets"
                ALB[Application Load Balancer<br/>API Gateway]
                NAT[NAT Gateway<br/>External Access]
            end
        end
        
        subgraph "IAM Roles & Policies"
            ER[EKS Service Role]
            NR[Node Group Role]
            PR[Propeller Execution Role]
            CR[Cross-Account Role]
        end
    end
    
    subgraph "User Environment"
        subgraph "Data Scientist Workspace"
            NB[Jupyter Notebook<br/>Experimentation]
            CDAO[CDAO SDK<br/>Pre-configured Client]
            CODE[Python Code<br/>ML Workflows]
        end
    end
    
    subgraph "External Compute Platforms"
        subgraph "Codeweave Platform"
            CW[Codeweave API<br/>api.codeweave.com]
            CWE[GPU Execution Environment<br/>K8s Clusters]
        end
        
        subgraph "AWS Batch"
            BATCH[Batch Compute Environment<br/>Spot/On-Demand Instances]
        end
        
        subgraph "Amazon EMR"
            EMR[EMR Spark Clusters<br/>Big Data Processing]
        end
    end
    
    %% User Workflow
    NB --> CDAO
    CDAO --> CODE
    CODE --> ALB
    
    %% Control Plane Flow
    ALB --> FC
    ALB --> FA
    FC --> FA
    FA --> RDS
    FA --> S3
    FP --> FA
    
    %% Plugin-based External Execution
    FP --> CW
    FP --> BATCH
    FP --> EMR
    
    %% Data Flow
    CW --> S3
    BATCH --> S3
    EMR --> S3
    
    %% Styling
    classDef controlPlane fill:#663399,stroke:#fff,color:#fff
    classDef userEnv fill:#2ecc71,stroke:#fff,color:#fff
    classDef external fill:#e74c3c,stroke:#fff,color:#fff
    classDef storage fill:#3498db,stroke:#fff,color:#fff
    classDef network fill:#f39c12,stroke:#fff,color:#fff
    classDef aws fill:#ff9900,stroke:#fff,color:#fff
    
    class FA,FP,FC,FDC controlPlane
    class NB,CDAO,CODE userEnv
    class CW,CWE external
    class RDS,S3 storage
    class ALB,NAT network
    class BATCH,EMR aws
```

## 📚 CDAO SDK Integration

### SDK Architecture & User Flow

```mermaid
graph TD
    subgraph "Data Scientist Environment"
        subgraph "Jupyter Notebook"
            CELL1[Cell 1: Import CDAO SDK<br/>import cdao_sdk]
            CELL2[Cell 2: Define ML Tasks<br/>@cdao_sdk.task]
            CELL3[Cell 3: Create Workflow<br/>@cdao_sdk.workflow]
            CELL4[Cell 4: Execute Remotely<br/>cdao_sdk.run()]
        end
        
        subgraph "CDAO SDK Components"
            AUTH[Pre-configured Auth<br/>Control Plane Access]
            CLIENT[Flyte Client<br/>API Wrapper]
            DECORATORS[Task Decorators<br/>@gpu_task, @batch_task]
            EXEC[Execution Manager<br/>Remote Submission]
        end
    end
    
    subgraph "Control Plane (AWS Account)"
        FA[Flyte Admin<br/>Workflow Registration]
        FP[Flyte Propeller<br/>Plugin Coordinator]
        
        subgraph "Flyte Plugins"
            K8S_PLUGIN[K8s Plugin<br/>Local EKS Execution]
            CW_PLUGIN[Codeweave Plugin<br/>GPU Workloads]
            BATCH_PLUGIN[AWS Batch Plugin<br/>Spot Instances]
            EMR_PLUGIN[EMR Plugin<br/>Spark Jobs]
        end
    end
    
    subgraph "Execution Environments"
        EKS_POD[EKS Pods<br/>Quick Tasks]
        CW_GPU[Codeweave GPU<br/>ML Training]
        AWS_BATCH[AWS Batch<br/>Long Jobs]
        EMR_SPARK[EMR Spark<br/>Big Data]
    end
    
    %% User Flow
    CELL1 --> AUTH
    CELL2 --> DECORATORS
    CELL3 --> CLIENT
    CELL4 --> EXEC
    
    %% SDK to Control Plane
    EXEC --> FA
    FA --> FP
    
    %% Plugin Routing
    FP --> K8S_PLUGIN
    FP --> CW_PLUGIN
    FP --> BATCH_PLUGIN
    FP --> EMR_PLUGIN
    
    %% Execution
    K8S_PLUGIN --> EKS_POD
    CW_PLUGIN --> CW_GPU
    BATCH_PLUGIN --> AWS_BATCH
    EMR_PLUGIN --> EMR_SPARK
    
    %% Styling
    classDef notebook fill:#2ecc71,stroke:#fff,color:#fff
    classDef sdk fill:#3498db,stroke:#fff,color:#fff
    classDef controlPlane fill:#663399,stroke:#fff,color:#fff
    classDef plugin fill:#9b59b6,stroke:#fff,color:#fff
    classDef execution fill:#e74c3c,stroke:#fff,color:#fff
    
    class CELL1,CELL2,CELL3,CELL4 notebook
    class AUTH,CLIENT,DECORATORS,EXEC sdk
    class FA,FP controlPlane
    class K8S_PLUGIN,CW_PLUGIN,BATCH_PLUGIN,EMR_PLUGIN plugin
    class EKS_POD,CW_GPU,AWS_BATCH,EMR_SPARK execution
```

### CDAO SDK Example Usage

```python
# Cell 1: Import and configure CDAO SDK
import cdao_sdk
from cdao_sdk import task, workflow, gpu_task, batch_task

# SDK is pre-configured with control plane access
cdao_sdk.configure(
    admin_endpoint="https://flyte.your-domain.com",
    project="ml-experiments",
    domain="development"
)

# Cell 2: Define ML tasks with platform targeting
@gpu_task(
    platform="codeweave",
    gpu_type="nvidia-tesla-v100",
    memory="32Gi"
)
def train_model(dataset_path: str, model_config: dict) -> str:
    # This runs on Codeweave GPU infrastructure
    return "s3://bucket/trained-model.pkl"

@batch_task(
    platform="aws-batch",
    instance_type="c5.4xlarge",
    spot_instances=True
)
def preprocess_data(raw_data_path: str) -> str:
    # This runs on AWS Batch with spot instances
    return "s3://bucket/processed-data.parquet"

# Cell 3: Create workflow
@workflow
def ml_pipeline(data_path: str) -> str:
    processed_data = preprocess_data(raw_data_path=data_path)
    model_path = train_model(
        dataset_path=processed_data,
        model_config={"epochs": 100, "lr": 0.001}
    )
    return model_path

# Cell 4: Execute remotely
execution = cdao_sdk.run(
    workflow=ml_pipeline,
    inputs={"data_path": "s3://bucket/raw-data.csv"}
)

# Monitor execution in real-time
cdao_sdk.monitor(execution.id)
```

## 🔧 Infrastructure Components

### Core Components Architecture

```mermaid
graph TD
    subgraph "EKS Cluster (education-eks-cluster)"
        subgraph "Flyte Namespace"
            FA[Flyte Admin Pod<br/>- REST API Server<br/>- Workflow Management<br/>- Authentication]
            FP[Flyte Propeller Pod<br/>- Workflow Execution<br/>- Task Scheduling<br/>- Remote Compute Orchestration]
            FC[Flyte Console Pod<br/>- Web UI<br/>- Workflow Visualization<br/>- Execution Monitoring]
            FDC[FlyteDC Pod<br/>- Data Catalog<br/>- Artifact Management<br/>- Lineage Tracking]
        end
        
        subgraph "Application Namespace"
            WP[Workflow Pods<br/>- Task Execution<br/>- Local Compute<br/>- Data Processing]
        end
    end
    
    subgraph "AWS Managed Services"
        RDS[(PostgreSQL RDS<br/>Multi-AZ<br/>Encrypted)]
        S3M[S3 - Metadata Bucket<br/>flyte-metadata-*]
        S3U[S3 - User Data Bucket<br/>flyte-userdata-*]
        S3W[S3 - Workflow Bucket<br/>bsingh-ml-workflows]
    end
    
    subgraph "External Compute Platforms"
        CW[Codeweave<br/>- Remote Execution<br/>- GPU Acceleration<br/>- Specialized Workloads]
        AWS_BATCH[AWS Batch<br/>- Batch Processing<br/>- Auto Scaling<br/>- Cost Optimization]
        SPARK[Spark on EMR<br/>- Big Data Processing<br/>- Distributed Computing<br/>- Analytics Workloads]
    end
    
    %% Core Connections
    FA --> RDS
    FA --> S3M
    FP --> FA
    FP --> WP
    FP --> CW
    FP --> AWS_BATCH
    FP --> SPARK
    FC --> FA
    FDC --> FA
    FDC --> S3M
    
    %% Data Flow
    WP --> S3U
    WP --> S3W
    CW --> S3U
    CW --> S3W
    AWS_BATCH --> S3U
    SPARK --> S3U
    
    %% Styling
    classDef flyte fill:#663399,stroke:#fff,color:#fff
    classDef aws fill:#ff9900,stroke:#fff,color:#fff
    classDef external fill:#e74c3c,stroke:#fff,color:#fff
    classDef storage fill:#3498db,stroke:#fff,color:#fff
    
    class FA,FP,FC,FDC,WP flyte
    class RDS,S3M,S3U,S3W,AWS_BATCH storage
    class CW,SPARK external
```

## 🌐 Network Architecture

```mermaid
graph TB
    subgraph "Internet"
        INT[Internet Gateway]
    end
    
    subgraph "VPC (10.0.0.0/16)"
        subgraph "Public Subnets (10.0.1.0/24, 10.0.2.0/24)"
            ALB[Application Load Balancer<br/>Internet-facing]
            NAT1[NAT Gateway AZ-1]
            NAT2[NAT Gateway AZ-2]
        end
        
        subgraph "Private Subnets (10.0.10.0/24, 10.0.20.0/24)"
            subgraph "EKS Worker Nodes"
                WN1[Worker Node 1<br/>c5.xlarge]
                WN2[Worker Node 2<br/>c5.xlarge]
                WN3[Worker Node 3<br/>c5.xlarge]
            end
            
            subgraph "Database Subnets (10.0.30.0/24, 10.0.40.0/24)"
                RDS1[(PostgreSQL Primary<br/>AZ-1)]
                RDS2[(PostgreSQL Standby<br/>AZ-2)]
            end
        end
        
        subgraph "S3 VPC Endpoint"
            S3EP[S3 Gateway Endpoint<br/>Private Route]
        end
    end
    
    subgraph "External Connectivity"
        subgraph "Codeweave Platform"
            CWAPI[Codeweave API<br/>api.codeweave.com]
            CWEXEC[Execution Environment]
        end
        
        subgraph "AWS Services"
            ECR[Elastic Container Registry]
            BATCH[AWS Batch]
            EMR[Amazon EMR]
        end
    end
    
    %% Internet Connectivity
    INT --> ALB
    
    %% Internal VPC Traffic
    ALB --> WN1
    ALB --> WN2
    ALB --> WN3
    
    %% Database Connectivity
    WN1 -.-> RDS1
    WN2 -.-> RDS1
    WN3 -.-> RDS1
    RDS1 -.-> RDS2
    
    %% S3 Connectivity
    WN1 --> S3EP
    WN2 --> S3EP
    WN3 --> S3EP
    
    %% External Connectivity (via NAT)
    WN1 --> NAT1
    WN2 --> NAT2
    WN3 --> NAT1
    NAT1 --> INT
    NAT2 --> INT
    
    %% External Service Connections
    NAT1 -.-> CWAPI
    NAT2 -.-> CWAPI
    NAT1 -.-> ECR
    NAT1 -.-> BATCH
    NAT1 -.-> EMR
    
    %% Styling
    classDef public fill:#2ecc71,stroke:#fff,color:#fff
    classDef private fill:#3498db,stroke:#fff,color:#fff
    classDef database fill:#9b59b6,stroke:#fff,color:#fff
    classDef external fill:#e74c3c,stroke:#fff,color:#fff
    classDef endpoint fill:#f39c12,stroke:#fff,color:#fff
    
    class ALB,NAT1,NAT2 public
    class WN1,WN2,WN3 private
    class RDS1,RDS2 database
    class CWAPI,CWEXEC,ECR,BATCH,EMR external
    class S3EP endpoint
```

## 🔐 Access Roles & Security

### IAM Role Architecture

```mermaid
graph TB
    subgraph "IAM Roles & Policies"
        subgraph "EKS Cluster Roles"
            ESR[EKS Service Role<br/>AmazonEKSClusterPolicy]
            NGR[Node Group Role<br/>- AmazonEKSWorkerNodePolicy<br/>- AmazonEKS_CNI_Policy<br/>- AmazonEC2ContainerRegistryReadOnly]
        end
        
        subgraph "Flyte Component Roles"
            FAR[Flyte Admin Role<br/>- RDS Access<br/>- S3 Metadata Access<br/>- Secrets Manager]
            FPR[Flyte Propeller Role<br/>- Task Execution<br/>- Cross-Account Assume<br/>- External Compute Access]
            FER[Flyte Execution Role<br/>- S3 User Data Access<br/>- Task-specific Permissions]
        end
        
        subgraph "Cross-Account Roles"
            CAR[Cross-Account Role<br/>Codeweave Integration]
            BAR[Batch Execution Role<br/>AWS Batch Integration]
            EMR_ROLE[EMR Service Role<br/>Spark Integration]
        end
        
        subgraph "Developer Access"
            DEV_ROLE[Developer Role<br/>- kubectl Access<br/>- Flyte CLI Access<br/>- S3 Read/Write]
        end
    end
    
    subgraph "Service Accounts (Kubernetes)"
        FA_SA[flyte-admin-sa]
        FP_SA[flyte-propeller-sa]
        FE_SA[flyte-execution-sa]
    end
    
    subgraph "External Integrations"
        CW_TRUST[Codeweave Trust Policy]
        AWS_STS[AWS STS AssumeRole]
    end
    
    %% Role Mappings
    FA_SA --> FAR
    FP_SA --> FPR
    FE_SA --> FER
    
    %% Cross-account Access
    FPR --> CAR
    FPR --> BAR
    FPR --> EMR_ROLE
    
    %% External Trust
    CAR --> CW_TRUST
    CAR --> AWS_STS
    
    %% Styling
    classDef eksRole fill:#ff9900,stroke:#fff,color:#fff
    classDef flyteRole fill:#663399,stroke:#fff,color:#fff
    classDef crossAccount fill:#e74c3c,stroke:#fff,color:#fff
    classDef k8sResource fill:#2ecc71,stroke:#fff,color:#fff
    classDef external fill:#95a5a6,stroke:#fff,color:#fff
    
    class ESR,NGR eksRole
    class FAR,FPR,FER,DEV_ROLE flyteRole
    class CAR,BAR,EMR_ROLE crossAccount
    class FA_SA,FP_SA,FE_SA k8sResource
    class CW_TRUST,AWS_STS external
```

### Security Flow Diagram

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant ALB as Load Balancer
    participant FC as Flyte Console
    participant FA as Flyte Admin
    participant FP as Flyte Propeller
    participant RDS as PostgreSQL
    participant S3 as S3 Buckets
    participant CW as Codeweave
    participant STS as AWS STS
    
    Note over Dev,STS: Authentication & Authorization Flow
    
    Dev->>ALB: HTTPS Request (kubectl/flytectl)
    ALB->>FC: Forward to Flyte Console
    FC->>FA: API Request with JWT
    FA->>FA: Validate JWT Token
    
    Note over FA,RDS: Database Access
    FA->>RDS: Query (using IAM DB Auth)
    RDS-->>FA: Results
    
    Note over FP,CW: External Compute Execution
    FP->>STS: AssumeRole (Cross-Account)
    STS-->>FP: Temporary Credentials
    FP->>CW: Submit Task (with temp creds)
    CW->>S3: Access Data (using assumed role)
    S3-->>CW: Data Retrieved
    CW-->>FP: Task Completion
    
    Note over FP,S3: Result Storage
    FP->>S3: Store Results (using execution role)
    S3-->>FP: Confirmation
    FP-->>FA: Update Execution Status
    FA-->>FC: Status Update
    FC-->>Dev: Real-time Updates
```

## 🚀 Multi-Compute Execution

### Execution Platform Integration

```mermaid
graph LR
    subgraph "Flyte Propeller Decision Engine"
        FP[Flyte Propeller<br/>Task Router]
        TE[Task Evaluator<br/>Resource Requirements<br/>Cost Optimization<br/>Platform Selection]
    end
    
    subgraph "Local EKS Execution"
        EKS_POD[EKS Pod Execution<br/>- CPU Intensive Tasks<br/>- Quick Jobs<br/>- Development/Testing]
    end
    
    subgraph "Codeweave Platform"
        CW_GPU[GPU Workloads<br/>- ML Training<br/>- Deep Learning<br/>- Model Inference]
        CW_CPU[CPU Workloads<br/>- Data Processing<br/>- ETL Jobs<br/>- Batch Analysis]
    end
    
    subgraph "AWS Batch"
        BATCH_SPOT[Spot Instance Jobs<br/>- Cost-sensitive<br/>- Fault-tolerant<br/>- Long-running]
        BATCH_DEMAND[On-Demand Jobs<br/>- Time-critical<br/>- Guaranteed capacity<br/>- SLA requirements]
    end
    
    subgraph "Amazon EMR"
        EMR_SPARK[Spark Clusters<br/>- Big Data Processing<br/>- Analytics Workloads<br/>- Distributed Computing]
    end
    
    %% Task Routing Logic
    FP --> TE
    TE --> EKS_POD
    TE --> CW_GPU
    TE --> CW_CPU
    TE --> BATCH_SPOT
    TE --> BATCH_DEMAND
    TE --> EMR_SPARK
    
    %% Execution Flow
    EKS_POD --> S3[(S3 Results)]
    CW_GPU --> S3
    CW_CPU --> S3
    BATCH_SPOT --> S3
    BATCH_DEMAND --> S3
    EMR_SPARK --> S3
    
    %% Styling
    classDef flyte fill:#663399,stroke:#fff,color:#fff
    classDef local fill:#2ecc71,stroke:#fff,color:#fff
    classDef external fill:#e74c3c,stroke:#fff,color:#fff
    classDef aws fill:#ff9900,stroke:#fff,color:#fff
    classDef storage fill:#3498db,stroke:#fff,color:#fff
    
    class FP,TE flyte
    class EKS_POD local
    class CW_GPU,CW_CPU external
    class BATCH_SPOT,BATCH_DEMAND,EMR_SPARK aws
    class S3 storage
```

### Task Execution Decision Matrix

| Task Type | Resource Requirements | Duration | Cost Sensitivity | Recommended Platform | Justification |
|-----------|----------------------|----------|------------------|---------------------|---------------|
| **Model Training (Deep Learning)** | GPU (V100/A100), High Memory | Hours to Days | Medium | **Codeweave GPU** | Specialized hardware, optimized for ML |
| **Data Preprocessing** | CPU, Medium Memory | Minutes to Hours | High | **AWS Batch (Spot)** | Cost-effective, fault-tolerant |
| **Model Inference** | CPU/GPU, Low Latency | Seconds to Minutes | Low | **EKS Pods** | Low latency, quick startup |
| **ETL Processing** | CPU, High Memory | Hours | High | **AWS Batch (Spot)** | Cost optimization for long jobs |
| **Analytics Queries** | CPU, High Memory, Distributed | Minutes to Hours | Medium | **EMR Spark** | Optimized for big data analytics |
| **Development/Testing** | CPU, Low Memory | Minutes | Low | **EKS Pods** | Quick feedback, development workflow |

## 📈 Deployment Flow

```mermaid
flowchart TD
    A[📋 Infrastructure Setup] --> B[🔐 IAM Roles Creation]
    B --> C[🌐 VPC & Networking]
    C --> D[🗄️ RDS PostgreSQL Setup]
    D --> E[🪣 S3 Buckets Creation]
    E --> F[☸️ EKS Cluster Deployment]
    F --> G[🚀 Flyte Installation]
    G --> H[🔗 External Platform Integration]
    H --> I[⚙️ Configure Cross-Account Access]
    I --> J[🧪 Testing & Validation]
    J --> K[📊 Monitoring Setup]
    K --> L[✅ Production Ready]
    
    %% Parallel Flows
    H --> H1[Codeweave Integration]
    H --> H2[AWS Batch Setup]
    H --> H3[EMR Configuration]
    
    H1 --> I
    H2 --> I
    H3 --> I
    
    %% Styling
    classDef setup fill:#e1f5fe
    classDef security fill:#f3e5f5
    classDef infrastructure fill:#e8f5e8
    classDef integration fill:#fff3e0
    classDef validation fill:#fce4ec
    
    class A,C,D,E,F setup
    class B,I security
    class G,H,H1,H2,H3 integration
    class J,K,L validation
```

### Step-by-Step Deployment Commands

#### 1. 📋 Infrastructure Setup
```bash
# Set AWS profile and region
export AWS_PROFILE=adfs
export AWS_REGION=us-east-1

# Create VPC and networking
aws cloudformation create-stack \
  --stack-name flyte-vpc \
  --template-body file://cloudformation/vpc.yaml \
  --parameters ParameterKey=VpcCidr,ParameterValue=10.0.0.0/16

# Wait for VPC creation
aws cloudformation wait stack-create-complete \
  --stack-name flyte-vpc
```

#### 2. 🔐 IAM Roles Creation
```bash
# Create EKS service role
aws iam create-role \
  --role-name FlyteEKSServiceRole \
  --assume-role-policy-document file://iam/eks-service-role-trust-policy.json

# Attach required policies
aws iam attach-role-policy \
  --role-name FlyteEKSServiceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create Flyte execution role
aws iam create-role \
  --role-name FlyteExecutionRole \
  --assume-role-policy-document file://iam/flyte-execution-role-trust-policy.json

# Create cross-account role for Codeweave
aws iam create-role \
  --role-name FlyteCodeweaveRole \
  --assume-role-policy-document file://iam/codeweave-trust-policy.json
```

#### 3. 🗄️ RDS PostgreSQL Setup
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name flyte-db-subnet-group \
  --db-subnet-group-description "Flyte DB subnet group" \
  --subnet-ids subnet-xxx subnet-yyy

# Create PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier flyte-postgres \
  --db-instance-class db.r5.large \
  --engine postgres \
  --engine-version 13.7 \
  --master-username flyteadmin \
  --master-user-password SecurePassword123! \
  --allocated-storage 100 \
  --db-subnet-group-name flyte-db-subnet-group \
  --vpc-security-group-ids sg-xxx \
  --multi-az \
  --storage-encrypted
```

#### 4. 🪣 S3 Buckets Creation
```bash
# Create metadata bucket
aws s3 mb s3://education-eks-flyte-metadata-$(date +%s) \
  --region us-east-1

# Create user data bucket
aws s3 mb s3://education-eks-flyte-userdata-$(date +%s) \
  --region us-east-1

# Create workflow bucket
aws s3 mb s3://bsingh-ml-workflows \
  --region us-east-1

# Enable versioning and encryption
aws s3api put-bucket-versioning \
  --bucket education-eks-flyte-metadata-$(date +%s) \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket education-eks-flyte-metadata-$(date +%s) \
  --server-side-encryption-configuration file://s3/encryption-config.json
```

#### 5. ☸️ EKS Cluster Deployment
```bash
# Create EKS cluster
aws eks create-cluster \
  --name education-eks-flyte \
  --version 1.27 \
  --role-arn arn:aws:iam::ACCOUNT:role/FlyteEKSServiceRole \
  --resources-vpc-config subnetIds=subnet-xxx,subnet-yyy,securityGroupIds=sg-xxx

# Wait for cluster to be ready
aws eks wait cluster-active --name education-eks-flyte

# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name education-eks-flyte

# Create node group
aws eks create-nodegroup \
  --cluster-name education-eks-flyte \
  --nodegroup-name flyte-workers \
  --instance-types c5.xlarge \
  --ami-type AL2_x86_64 \
  --capacity-type ON_DEMAND \
  --scaling-config minSize=2,maxSize=10,desiredSize=3 \
  --disk-size 50 \
  --node-role arn:aws:iam::ACCOUNT:role/FlyteNodeGroupRole \
  --subnets subnet-xxx subnet-yyy
```

#### 6. 🚀 Flyte Installation
```bash
# Add Flyte Helm repository
helm repo add flyteorg https://flyteorg.github.io/flyte
helm repo update

# Create Flyte namespace
kubectl create namespace flyte

# Install Flyte with custom values
helm install flyte flyteorg/flyte-core \
  --namespace flyte \
  --values flyte-values.yaml \
  --set configuration.database.host=flyte-postgres.region.rds.amazonaws.com \
  --set configuration.database.password=SecurePassword123! \
  --set configuration.storage.metadataContainer=s3://education-eks-flyte-metadata-xxx \
  --set configuration.storage.userDataContainer=s3://education-eks-flyte-userdata-xxx
```

#### 7. 🔗 External Platform Integration

##### Codeweave Integration
```bash
# Create Kubernetes secret for Codeweave credentials
kubectl create secret generic codeweave-credentials \
  --namespace flyte \
  --from-literal=api-key=your-codeweave-api-key \
  --from-literal=endpoint=https://api.codeweave.com

# Apply Codeweave plugin configuration
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: flyte-propeller-config
  namespace flyte
data:
  plugins.yaml: |
    plugins:
      codeweave:
        endpoint: https://api.codeweave.com
        auth:
          type: "api-key"
          secret: "codeweave-credentials"
        resources:
          limits:
            cpu: "8"
            memory: "32Gi"
            nvidia.com/gpu: "1"
EOF
```

##### AWS Batch Integration
```bash
# Create Batch compute environment
aws batch create-compute-environment \
  --compute-environment-name flyte-batch-env \
  --type MANAGED \
  --state ENABLED \
  --compute-resources type=EC2,minvCpus=0,maxvCpus=1000,desiredvCpus=0,instanceTypes=optimal,subnets=subnet-xxx,securityGroupIds=sg-xxx,instanceRole=arn:aws:iam::ACCOUNT:instance-profile/ecsInstanceRole

# Create job queue
aws batch create-job-queue \
  --job-queue-name flyte-batch-queue \
  --state ENABLED \
  --priority 1 \
  --compute-environment-order order=1,computeEnvironment=flyte-batch-env
```

#### 8. ⚙️ Configure Cross-Account Access
```bash
# Create trust policy for Codeweave
cat > codeweave-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::CODEWEAVE-ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "flyte-execution-id"
        }
      }
    }
  ]
}
EOF

# Update role trust policy
aws iam update-assume-role-policy \
  --role-name FlyteCodeweaveRole \
  --policy-document file://codeweave-trust-policy.json

# Create access policy for S3 and services
aws iam put-role-policy \
  --role-name FlyteCodeweaveRole \
  --policy-name FlyteS3Access \
  --policy-document file://iam/s3-access-policy.json
```

#### 9. 🧪 Testing & Validation
```bash
# Test Flyte connectivity
kubectl port-forward -n flyte svc/flyte-binary-http 8088:8088 &
flytectl --config .flyte/config.yaml get projects

# Test database connectivity
kubectl exec -it -n flyte deployment/flyte-admin -- \
  psql -h flyte-postgres.region.rds.amazonaws.com -U flyteadmin -d flyteadmin

# Test S3 access
kubectl exec -it -n flyte deployment/flyte-admin -- \
  aws s3 ls s3://education-eks-flyte-metadata-xxx/

# Test Codeweave integration
pyflyte --config .flyte/config.yaml run \
  --project test \
  --domain development \
  --image ghcr.io/flyteorg/flytekit:py3.9-1.10.3 \
  test_codeweave_task.py
```

## 📊 Configuration Examples

### Flyte Values Configuration (`flyte-values.yaml`)

```yaml
# Flyte Core Configuration
configuration:
  # Database configuration
  database:
    host: "flyte-postgres.us-east-1.rds.amazonaws.com"
    port: 5432
    username: "flyteadmin"
    passwordPath: "/etc/db/password"
    dbname: "flyteadmin"
    
  # Storage configuration
  storage:
    type: s3
    container: "s3://education-eks-flyte-metadata-xxx"
    config:
      region: "us-east-1"
      auth_type: "iam"
      
  # Propeller configuration
  propeller:
    plugins:
      # Local Kubernetes execution
      k8s:
        default-cpus: "500m"
        default-memory: "500Mi"
        
      # Codeweave plugin
      codeweave:
        endpoint: "https://api.codeweave.com"
        auth:
          type: "assume-role"
          role-arn: "arn:aws:iam::ACCOUNT:role/FlyteCodeweaveRole"
        default-resources:
          cpu: "2"
          memory: "8Gi"
          gpu: "1"
          
      # AWS Batch plugin  
      batch:
        region: "us-east-1"
        job-queue: "flyte-batch-queue"
        execution-role: "arn:aws:iam::ACCOUNT:role/FlyteExecutionRole"
        
      # Spark on EMR plugin
      spark:
        cluster-id: "j-xxxxxxxxxxxxx"
        execution-role: "arn:aws:iam::ACCOUNT:role/EMR_EC2_DefaultRole"

# Service configuration
flyteadmin:
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: "arn:aws:iam::ACCOUNT:role/FlyteAdminRole"
      
flytepropeller:
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: "arn:aws:iam::ACCOUNT:role/FlytePropellerRole"

# Ingress configuration
ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: "alb"
    alb.ingress.kubernetes.io/scheme: "internet-facing"
    alb.ingress.kubernetes.io/target-type: "ip"
    alb.ingress.kubernetes.io/ssl-redirect: "443"
  hosts:
    - host: flyte.your-domain.com
      paths:
        - path: /*
          pathType: ImplementationSpecific
  tls:
    - secretName: flyte-tls
      hosts:
        - flyte.your-domain.com
```

### IAM Policy Examples

#### S3 Access Policy
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
                "arn:aws:s3:::education-eks-flyte-metadata-*",
                "arn:aws:s3:::education-eks-flyte-metadata-*/*",
                "arn:aws:s3:::education-eks-flyte-userdata-*", 
                "arn:aws:s3:::education-eks-flyte-userdata-*/*",
                "arn:aws:s3:::bsingh-ml-workflows",
                "arn:aws:s3:::bsingh-ml-workflows/*"
            ]
        }
    ]
}
```

#### Cross-Account Execution Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole"
            ],
            "Resource": [
                "arn:aws:iam::CODEWEAVE-ACCOUNT:role/FlyteExecutionRole",
                "arn:aws:iam::ACCOUNT:role/BatchExecutionRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "batch:SubmitJob",
                "batch:DescribeJobs",
                "batch:CancelJob"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "emr:AddJobFlowSteps",
                "emr:DescribeStep",
                "emr:DescribeCluster"
            ],
            "Resource": "*"
        }
    ]
}
```

### Workflow Task Configuration Examples

#### Local EKS Task
```python
from flytekit import task, Resources
from flytekit.configuration import Config

@task(
    requests=Resources(cpu="500m", mem="1Gi"),
    limits=Resources(cpu="1", mem="2Gi"),
    container_image="ghcr.io/flyteorg/flytekit:py3.9-1.10.3"
)
def local_processing_task(data: str) -> str:
    # CPU-intensive local processing
    return f"Processed: {data}"
```

#### Codeweave GPU Task
```python
from flytekit import task, Resources
from flytekit.extras.accelerators import GPUAccelerator

@task(
    requests=Resources(cpu="4", mem="16Gi", gpu="1"),
    limits=Resources(cpu="8", mem="32Gi", gpu="1"),
    accelerator=GPUAccelerator("nvidia-tesla-v100"),
    container_image="your-registry/ml-training:latest",
    task_config={
        "platform": "codeweave",
        "instance_type": "gpu.large"
    }
)
def gpu_training_task(model_config: dict) -> str:
    # GPU-accelerated ML training
    return "model_path.pkl"
```

#### AWS Batch Task
```python
from flytekit import task, Resources

@task(
    requests=Resources(cpu="2", mem="8Gi"),
    limits=Resources(cpu="16", mem="64Gi"),
    container_image="your-registry/data-processing:latest",
    task_config={
        "platform": "batch",
        "job_queue": "flyte-batch-queue",
        "execution_role": "arn:aws:iam::ACCOUNT:role/BatchExecutionRole"
    }
)
def batch_processing_task(large_dataset: str) -> str:
    # Large-scale batch processing
    return "processed_data_path"
```

---

## 🎯 Benefits of This Architecture

### 🔒 Security Benefits
- **Network Isolation**: All Flyte components in private subnets
- **IAM Integration**: Fine-grained access control with AWS IAM
- **Cross-Account Security**: Secure external compute platform integration
- **Data Encryption**: At-rest and in-transit encryption for all data

### 💰 Cost Optimization
- **Multi-Platform Execution**: Choose most cost-effective compute for each task
- **Spot Instance Support**: Use AWS Batch with spot instances for cost savings
- **Auto-Scaling**: EKS cluster auto-scaling based on workload demand
- **Storage Optimization**: S3 lifecycle policies for data retention

### 🚀 Performance & Scalability
- **Specialized Compute**: GPU acceleration via Codeweave for ML workloads
- **Distributed Processing**: Spark on EMR for big data analytics
- **Local Execution**: Low-latency execution for quick tasks
- **Multi-AZ Deployment**: High availability across availability zones

### 🔧 Operational Excellence
- **Managed Services**: Leverage AWS managed services (RDS, S3, EKS)
- **Monitoring**: Integrated CloudWatch and Kubernetes monitoring
- **Automation**: Infrastructure as Code with CloudFormation/Terraform
- **Disaster Recovery**: Multi-AZ RDS and S3 cross-region replication

This architecture provides a production-ready, secure, and scalable foundation for running Flyte workflows across multiple compute platforms while maintaining enterprise-grade security and compliance requirements.
