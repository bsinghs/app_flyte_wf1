# FastAPI Service Deployment Architecture

## 🏗️ Where Does the FastAPI Integration Service Run?

### Architecture Options & Recommendations

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Company Infrastructure                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              OPTION 1: Same EKS Cluster (Recommended)      │    │
│  │                                                             │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │            Central Flyte EKS Cluster               │    │    │
│  │  │                                                     │    │    │
│  │  │  ┌─────────────────┬─────────────────────────────┐  │    │    │
│  │  │  │   Flyte System  │    Platform Services        │  │    │    │
│  │  │  │   Namespace     │       Namespace             │  │    │    │
│  │  │  │                 │                             │  │    │    │
│  │  │  │ • flyte-admin   │ • workspace-flyte-integration│ │    │    │
│  │  │  │ • flyte-console │ • workspace-config-controller│ │    │    │
│  │  │  │ • flyte-datacatalog │ • rbac-manager         │  │    │    │
│  │  │  │ • flyte-propeller   │ • monitoring           │  │    │    │
│  │  │  └─────────────────┴─────────────────────────────┘  │    │    │
│  │  │                                                     │    │    │
│  │  │  ┌─────────────────────────────────────────────┐    │    │    │
│  │  │  │         Tenant Workspaces                  │    │    │    │
│  │  │  │  flyte-ws-001, flyte-ws-002, etc.         │    │    │    │
│  │  │  └─────────────────────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              OPTION 2: Separate Platform Cluster          │    │
│  │                                                             │    │
│  │  ┌─────────────────────────┬─────────────────────────────┐  │    │
│  │  │    Platform EKS         │     Flyte EKS Cluster       │  │    │
│  │  │                         │                             │  │    │
│  │  │ • workspace-service     │ • flyte-admin               │  │    │
│  │  │ • user-management       │ • flyte-console             │  │    │
│  │  │ • service-registry      │ • flyte-datacatalog         │  │    │
│  │  │ • workspace-flyte-      │ • flyte-propeller           │  │    │
│  │  │   integration 🎯        │ • tenant workspaces         │  │    │
│  │  └─────────────────────────┴─────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │         OPTION 3: Existing Company Platform Cluster        │    │
│  │                                                             │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │       Company Platform Services EKS                 │    │    │
│  │  │                                                     │    │    │
│  │  │ • existing-workspace-service                        │    │    │
│  │  │ • identity-management                               │    │    │
│  │  │ • service-mesh                                      │    │    │
│  │  │ • workspace-flyte-integration 🎯 (NEW)             │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 **RECOMMENDED: Option 1 - Same EKS Cluster**

### Why Run in the Same Flyte EKS Cluster?

#### ✅ **Network Advantages**
```bash
# Internal cluster communication - no network latency
workspace-flyte-integration.platform-services.svc.cluster.local
↓ (internal DNS, sub-millisecond)
flyte-admin.flyte-system.svc.cluster.local

# VS External communication across clusters
workspace-flyte-integration.platform-eks.company.com
↓ (external network, 10-50ms + security overhead)
flyte-admin.flyte-eks.company.com
```

#### ✅ **Security Benefits**
- **Same cluster RBAC**: Service accounts can directly access Flyte APIs
- **No external endpoints**: All communication stays within cluster
- **Simplified secrets management**: Shared secret stores and service mesh
- **Network policies**: Direct pod-to-pod communication control

#### ✅ **Operational Simplicity**
- **Single cluster to manage** for Flyte operations
- **Unified monitoring** and logging
- **Consistent deployment patterns**
- **Shared infrastructure** (load balancers, ingress, etc.)

## 🚀 Deployment Configuration

### Namespace Layout in Flyte EKS Cluster

```yaml
# flyte-cluster-namespaces.yaml
---
# Core Flyte services
apiVersion: v1
kind: Namespace
metadata:
  name: flyte-system
  labels:
    purpose: flyte-core
---
# Platform integration services
apiVersion: v1
kind: Namespace
metadata:
  name: platform-services
  labels:
    purpose: platform-integration
---
# Workspace monitoring and management
apiVersion: v1
kind: Namespace
metadata:
  name: workspace-management
  labels:
    purpose: workspace-ops
```

### FastAPI Service Deployment

```yaml
# workspace-flyte-integration-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workspace-flyte-integration
  namespace: platform-services  # 🎯 In same cluster, different namespace
  labels:
    app: workspace-flyte-integration
    component: platform-integration
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: workspace-flyte-integration
  template:
    metadata:
      labels:
        app: workspace-flyte-integration
    spec:
      serviceAccountName: workspace-flyte-integration-sa
      containers:
      - name: integration-service
        image: company-registry.com/workspace-flyte-integration:v1.2.0
        ports:
        - containerPort: 8080
          name: http
        env:
        # 🎯 Internal cluster communication
        - name: FLYTE_ADMIN_ENDPOINT
          value: "flyte-admin.flyte-system.svc.cluster.local:81"  # Internal DNS
        - name: FLYTE_CONSOLE_URL
          value: "https://flyte-console.company.com"
        # Company workspace service integration
        - name: WORKSPACE_API_ENDPOINT
          value: "https://workspace-api.company.com"  # External - your existing service
        - name: WORKSPACE_WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: workspace-integration-secrets
              key: webhook-secret
        # Kubernetes API access
        - name: KUBERNETES_NAMESPACE_PREFIX
          value: "flyte-"
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: workspace-flyte-integration
  namespace: platform-services
spec:
  selector:
    app: workspace-flyte-integration
  ports:
  - port: 80
    targetPort: 8080
    name: http
  type: ClusterIP  # Internal service only
---
# Optional: Ingress for external access (if needed for debugging)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: workspace-flyte-integration-ingress
  namespace: platform-services
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8"  # Internal only
spec:
  tls:
  - hosts:
    - workspace-flyte-internal.company.com
    secretName: workspace-flyte-tls
  rules:
  - host: workspace-flyte-internal.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: workspace-flyte-integration
            port:
              number: 80
```

### Service Account with Cluster Permissions

```yaml
# workspace-flyte-integration-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workspace-flyte-integration-sa
  namespace: platform-services
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: workspace-flyte-integration-role
rules:
# Namespace management
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list", "create", "update", "delete"]
# Resource quota management
- apiGroups: [""]
  resources: ["resourcequotas"]
  verbs: ["get", "list", "create", "update", "delete"]
# Service account management for workspaces
- apiGroups: [""]
  resources: ["serviceaccounts"]
  verbs: ["get", "list", "create", "update", "delete"]
# RBAC management for workspaces
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings"]
  verbs: ["get", "list", "create", "update", "delete"]
# Network policy management
- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies"]
  verbs: ["get", "list", "create", "update", "delete"]
# ConfigMap management for workspace configs
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "create", "update", "delete", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: workspace-flyte-integration-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: workspace-flyte-integration-role
subjects:
- kind: ServiceAccount
  name: workspace-flyte-integration-sa
  namespace: platform-services
```

## 🔄 Communication Flow

### Internal Cluster Communication

```python
# workspace_flyte_integration.py - Updated for cluster deployment
from fastapi import FastAPI
from flytekit.clients.friendly import SynchronousFlyteClient
import os

app = FastAPI(title="Workspace-Flyte Integration")

class FlyteWorkspaceManager:
    def __init__(self):
        # 🎯 Internal cluster communication - no TLS overhead
        flyte_admin_endpoint = os.getenv(
            "FLYTE_ADMIN_ENDPOINT", 
            "flyte-admin.flyte-system.svc.cluster.local:81"
        )
        
        # Use internal endpoint for fast communication
        self.flyte_client = SynchronousFlyteClient(
            endpoint=flyte_admin_endpoint,
            insecure=True  # Internal cluster communication
        )
        
    async def provision_flyte_service(self, workspace_data: dict):
        """Provision Flyte project - runs in same cluster as Flyte Admin"""
        
        try:
            # Direct API call to Flyte Admin (same cluster)
            project = await self.create_flyte_project(workspace_data)
            
            # Direct Kubernetes API calls (same cluster)
            namespace = await self.create_k8s_namespace(workspace_data["workspace_id"])
            
            return {
                "status": "success",
                "project_id": workspace_data["workspace_id"],
                "console_url": f"{os.getenv('FLYTE_CONSOLE_URL')}/console/projects/{workspace_data['workspace_id']}"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "cluster": "flyte-eks",
        "namespace": "platform-services"
    }
```

### External Integration with Your Workspace Service

```python
# Your existing workspace service calls this endpoint
import httpx
import asyncio

async def create_workspace_with_flyte(workspace_data):
    """Your workspace service calls our FastAPI integration"""
    
    # Call FastAPI service running in Flyte EKS cluster
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://workspace-flyte-integration.platform-services.svc.cluster.local/provision",
            json=workspace_data,
            timeout=30.0
        )
        
        # Or external endpoint if needed:
        # "https://workspace-flyte-internal.company.com/provision"
    
    return response.json()
```

## 🎯 Alternative: If You Need Separate Clusters

### Option 2: Platform Cluster Communication

```yaml
# If you must run in separate cluster, use external endpoints
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workspace-flyte-integration
  namespace: platform-services
spec:
  template:
    spec:
      containers:
      - name: integration-service
        env:
        # 🔄 External cluster communication
        - name: FLYTE_ADMIN_ENDPOINT
          value: "flyte-admin.flyte-eks.company.com:443"  # External endpoint
        - name: FLYTE_ADMIN_TLS_ENABLED
          value: "true"
        - name: FLYTE_ADMIN_CLIENT_CERT
          valueFrom:
            secretKeyRef:
              name: flyte-client-certs
              key: client.crt
```

## 🏆 **Final Recommendation: Same Cluster**

### Deploy FastAPI Integration Service in Flyte EKS Cluster

**Namespace**: `platform-services`  
**Cluster**: Same as Flyte (your central EKS cluster)  
**Network**: Internal cluster communication  
**Scaling**: 3 replicas with HPA  

### Benefits Summary:
- ⚡ **Fastest communication** with Flyte Admin API
- 🔒 **Most secure** - no external network exposure
- 🛠️ **Simplest operations** - single cluster management
- 💰 **Most cost-effective** - shared infrastructure
- 🔄 **Best reliability** - fewer network hops

The FastAPI service becomes a "platform service" that bridges your existing workspace infrastructure with the Flyte ecosystem! 🚀
