# flytectl Deep Dive: Commands, Security, and Operations

## Table of Contents
1. [What is flytectl?](#what-is-flytectl)
2. [How flytectl Works Under the Hood](#how-flytectl-works-under-the-hood)
3. [Authentication & Authorization](#authentication--authorization)
4. [Essential Commands by Category](#essential-commands-by-category)
5. [Debugging Commands](#debugging-commands)
6. [Security Considerations](#security-considerations)
7. [Real-world Examples from Our Session](#real-world-examples-from-our-session)

---

## What is flytectl?

`flytectl` is the **command-line interface (CLI)** for Flyte - it's your primary tool for:
- 🚀 **Managing workflows** (register, execute, monitor)
- 🔍 **Debugging executions** (logs, status, errors)
- 🏗️ **Project management** (create projects, domains)
- 📊 **Resource monitoring** (tasks, launch plans, executions)

Think of it as the "kubectl for Flyte" - just like kubectl manages Kubernetes resources, flytectl manages Flyte resources.

---

## How flytectl Works Under the Hood

### Architecture Overview
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   flytectl  │────│ Flyte Admin  │────│ Flyte Backend   │
│   (Client)  │    │   Service    │    │ (K8s Cluster)   │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   │                      │
       │                   │                      │
   gRPC/HTTP          gRPC API            Kubernetes API
```

### What Happens When You Run flytectl?

1. **Configuration Loading**
   ```bash
   # flytectl looks for config in this order:
   # 1. --config flag
   # 2. ~/.flyte/config.yaml
   # 3. Environment variables
   ```

2. **Connection Establishment**
   - Connects to Flyte Admin Service (gRPC endpoint)
   - Authenticates using configured method (OAuth, certificates, etc.)
   - Establishes secure channel

3. **API Call Translation**
   ```bash
   flytectl get projects
   # Translates to:
   # gRPC call: AdminService.ListProjects()
   # HTTP equivalent: GET /api/v1/projects
   ```

4. **Response Processing**
   - Receives protobuf response
   - Formats output (table, YAML, JSON)
   - Displays results

### Network Flow Example
```
Your Machine                 EKS Cluster
┌─────────────┐             ┌─────────────────┐
│  flytectl   │   Port      │ flyte-binary    │
│ localhost   │  Forward    │ Service         │
│    :8089    │◄───────────►│    :8089        │
└─────────────┘             └─────────────────┘
```

---

## Authentication & Authorization

### Authentication Methods

#### 1. **PKCE (OAuth2)** - Most Secure
```yaml
# .flyte/config.yaml
admin:
  endpoint: your-flyte-cluster.com
  authType: Pkce
  insecure: false
```
- Uses OAuth2 with Proof Key for Code Exchange
- Redirects to browser for authentication
- Stores tokens securely
- **Best for production environments**

#### 2. **Client Credentials** - Service Accounts
```yaml
admin:
  endpoint: your-flyte-cluster.com
  authType: ClientSecret
  clientId: "your-client-id"
  clientSecret: "your-secret"
```
- Machine-to-machine authentication
- Uses client ID and secret
- **Best for CI/CD pipelines**

#### 3. **Port Forwarding** - Development (What we used)
```yaml
admin:
  endpoint: localhost:8089
  insecure: true  # No TLS/authentication
```
- Direct connection through kubectl port-forward
- **Only for development/testing**
- Inherits kubectl authentication

### Authorization Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  flytectl   │    │ Flyte Admin  │    │ Identity Provider│
│             │    │              │    │ (OAuth/OIDC)    │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   │                      │
   1.  │ Request resource  │                      │
       │──────────────────►│                      │
   2.  │                   │ Validate token       │
       │                   │─────────────────────►│
   3.  │                   │ User permissions     │
       │                   │◄─────────────────────│
   4.  │ Response/Deny     │                      │
       │◄──────────────────│                      │
```

---

## Essential Commands by Category

### 🚀 **Application Lifecycle Commands**

#### Starting/Deploying Workflows
```bash
# 1. Register workflow (deploy to cluster)
pyflyte register --project my-project --domain development --image my-image:latest workflow.py

# 2. Create execution (start workflow)
flytectl create execution --project my-project --domain development my.workflow.name

# 3. Create with inputs
flytectl create execution --execFile execution_config.yaml
```

#### Stopping/Managing Executions
```bash
# Abort running execution
flytectl update execution --project my-project --domain development exec-id --archive

# Note: There's no "stop" - workflows run to completion or failure
# You can only archive them (hide from UI)
```

### 📋 **Resource Management Commands**

#### Project Management
```bash
# List projects
flytectl get projects

# Create project
flytectl create project --id my-project --name "My Project"

# Get project details
flytectl get project my-project
```

#### Workflow Management
```bash
# List workflows
flytectl get workflows --project my-project --domain development

# Get specific workflow
flytectl get workflow --project my-project --domain development my.workflow.name

# Get workflow versions
flytectl get workflow --project my-project --domain development my.workflow.name --version all
```

#### Execution Management
```bash
# List executions
flytectl get executions --project my-project --domain development

# Get execution status
flytectl get execution --project my-project --domain development exec-id

# Get execution with full details
flytectl get execution --project my-project --domain development exec-id -o yaml
```

### 🔍 **Monitoring Commands**

```bash
# Monitor all executions in a project
flytectl get executions --project my-project --domain development --limit 50

# Filter by status
flytectl get executions --project my-project --domain development --filter "phase=RUNNING"

# Get execution timeline
flytectl get execution --project my-project --domain development exec-id -o json | jq '.closure'
```

---

## Debugging Commands

### 🐛 **Essential Debugging Workflow**

#### 1. **Identify the Problem**
```bash
# Check execution status
flytectl get execution --project ml-workflows --domain development exec-id

# Quick status check
flytectl get executions --project ml-workflows --domain development --limit 10
```

#### 2. **Get Detailed Error Information**
```bash
# Full execution details with errors
flytectl get execution --project ml-workflows --domain development exec-id -o yaml

# Focus on error message
flytectl get execution --project ml-workflows --domain development exec-id -o yaml | grep -A 20 "error:"
```

#### 3. **Examine Individual Tasks**
```bash
# List tasks in workflow
flytectl get task --project ml-workflows --domain development

# Get specific task details
flytectl get task --project ml-workflows --domain development my.task.name --version latest
```

#### 4. **Node-Level Debugging**
```bash
# Get execution node details (shows individual task executions)
flytectl get execution --project ml-workflows --domain development exec-id -o yaml | grep -A 50 "nodeExecutions"
```

### 🔧 **Advanced Debugging Commands**

#### Resource Analysis
```bash
# Check launch plans (deployment configurations)
flytectl get launchplan --project ml-workflows --domain development workflow.name

# Generate execution config for testing
flytectl get launchplan --project ml-workflows --domain development workflow.name --execFile debug_config.yaml
```

#### Data Flow Debugging
```bash
# Check input/output data paths
flytectl get execution --project ml-workflows --domain development exec-id -o json | jq '.spec.inputs'
flytectl get execution --project ml-workflows --domain development exec-id -o json | jq '.closure.outputs'
```

### 🚨 **Common Error Patterns & Debugging**

#### 1. **Image Pull Errors**
```bash
# Symptom: ErrImagePull, ImagePullBackOff
# Debug:
flytectl get execution exec-id -o yaml | grep -i image
# Shows which image is failing

# Solution: Check image exists and registry access
```

#### 2. **Resource Constraint Errors**
```bash
# Symptom: Pod stays in Pending state
# Debug:
kubectl describe pod pod-name -n namespace
# Shows resource requirements vs availability

# Solution: Adjust task resource requests/limits
```

#### 3. **S3/Storage Access Errors**
```bash
# Symptom: "Forbidden" or "Access Denied" in logs
# Debug:
flytectl get execution exec-id -o yaml | grep -A 10 "Failed to get data"
# Shows exact S3 path and error

# Solution: Check IAM permissions
```

---

## Security Considerations

### 🔒 **Security Best Practices**

#### 1. **Network Security**
```bash
# Production: Use proper TLS endpoints
admin:
  endpoint: https://flyte.company.com
  insecure: false

# Development: Port forwarding (less secure)
admin:
  endpoint: localhost:8089
  insecure: true  # Only for dev!
```

#### 2. **Authentication Security**
```bash
# GOOD: OAuth2 with PKCE
authType: Pkce

# AVOID: No authentication (only for local dev)
# This bypasses all security!
```

#### 3. **Access Control**
```bash
# Check your permissions
flytectl get projects  # Shows what projects you can access

# Different domains provide isolation
flytectl get executions --domain production   # Prod data
flytectl get executions --domain development  # Dev data
```

### ⚠️ **Security Risks & Mitigations**

#### Port Forwarding Risks
```bash
# RISK: Anyone on your machine can access Flyte
kubectl port-forward -n flyte svc/flyte-binary-http 8088:8088

# MITIGATION: Use proper authentication in production
# Only use port forwarding for development
```

#### IAM/RBAC Considerations
```bash
# Your flytectl permissions = your kubectl permissions
# If you can run:
kubectl get pods -n flyte
# Then you can likely access Flyte admin

# MITIGATION: Use least-privilege IAM roles
```

---

## Real-world Examples from Our Session

### 🎯 **What We Actually Did**

#### 1. **Project Setup**
```bash
# Connected to cluster via port forwarding
kubectl port-forward -n flyte svc/flyte-binary-grpc 8089:8089

# Configured flytectl
cat > .flyte/config.yaml << EOF
admin:
  endpoint: localhost:8089
  insecure: true
EOF

# Created project
flytectl create project --id ml-workflows --name "ML Workflows"
```

#### 2. **Workflow Deployment**
```bash
# Registered workflow with different images
pyflyte register --project ml-workflows --domain development --image ml-workflows:latest ml_pipeline_improved.py
# Failed: Image didn't exist

pyflyte register --project ml-workflows --domain development --image ghcr.io/flyteorg/flytekit:py3.9-1.10.3 ml_pipeline_improved.py
# Success: Used official Flyte image
```

#### 3. **Execution Management**
```bash
# Generated execution config
flytectl get launchplan --project ml-workflows --domain development ml_pipeline_improved.credit_scoring_pipeline --execFile execution_config.yaml

# Started execution
flytectl create execution --project ml-workflows --domain development --execFile execution_config.yaml

# Monitored progress
flytectl get execution --project ml-workflows --domain development exec-id
```

#### 4. **Debugging Issues**
```bash
# Issue: Resource constraints
# Debug: kubectl describe pod showed "Insufficient cpu"
# Solution: Added resource limits to tasks

# Issue: Image pull errors
# Debug: flytectl get execution -o yaml showed image path
# Solution: Used different image

# Issue: S3 permissions
# Debug: Error showed "Forbidden" accessing S3 bucket
# Solution: Updated IAM policy
```

### 📝 **Key Lessons**

1. **Always check execution status**: `flytectl get execution` is your best friend
2. **Use YAML output for debugging**: `-o yaml` shows full error details
3. **Resource management matters**: Small nodes need small resource requests
4. **Security is layered**: Network → Authentication → Authorization → IAM

### 🎓 **Quick Reference Card**

```bash
# Essential Daily Commands
flytectl get projects                                    # List your projects
flytectl get executions --project X --domain Y         # Check recent runs
flytectl get execution --project X --domain Y exec-id  # Check specific run
flytectl create execution --execFile config.yaml       # Start new run

# Debugging Commands
flytectl get execution exec-id -o yaml | grep -A 20 error  # Find errors
kubectl get pods -n project-domain                         # Check K8s status
kubectl describe pod pod-name -n namespace                 # Detailed pod info

# Management Commands
pyflyte register --project X --domain Y --image img file.py  # Deploy workflow
flytectl get workflows --project X --domain Y                # List workflows
flytectl update execution --project X --domain Y exec-id --archive  # Archive execution
```

This deep dive should give you a solid foundation for understanding flytectl from both operational and security perspectives!
