# Automatic Project Creation in Workspace-as-Project Mapping

## 🔄 Detailed Flow: How Projects Are Automatically Created

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Automatic Project Creation Flow                  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  1. Workspace Management Service                            │    │
│  │     • Workspace creation API                               │    │
│  │     • Service selection (SageMaker, Flyte, Bedrock...)     │    │
│  │     • User management                                      │    │
│  └─────────────────────────┬───────────────────────────────────┘    │
│                            │                                        │
│                            │ API Call                              │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  2. Workspace-Flyte Integration Service                     │    │
│  │     • Listens for workspace events                         │    │
│  │     • Validates Flyte service selection                    │    │
│  │     • Triggers project creation                            │    │
│  └─────────────────────────┬───────────────────────────────────┘    │
│                            │                                        │
│                            │ Creates                               │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  3. Flyte Admin API                                         │    │
│  │     • Creates project with workspace_id                    │    │
│  │     • Sets up domains (dev, staging, prod)                 │    │
│  │     • Configures project metadata                          │    │
│  └─────────────────────────┬───────────────────────────────────┘    │
│                            │                                        │
│                            │ Provisions                            │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  4. Kubernetes Resources                                    │    │
│  │     • Creates dedicated namespace                           │    │
│  │     • Applies resource quotas                              │    │
│  │     • Sets up RBAC permissions                             │    │
│  │     • Configures network policies                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Step-by-Step Implementation

### Step 1: Workspace Service Integration

#### Workspace Creation Event Handler
```python
# workspace_service.py (Your existing workspace management system)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import httpx
import asyncio

app = FastAPI(title="Workspace Management Service")

class ServiceConfig(BaseModel):
    service_type: str  # "sagemaker", "flyte", "bedrock", etc.
    config: dict = {}

class WorkspaceRequest(BaseModel):
    workspace_name: str
    owner_email: str
    services: List[ServiceConfig]
    users: List[dict]

@app.post("/workspaces")
async def create_workspace(request: WorkspaceRequest):
    """Create workspace with selected services"""
    
    # 1. Generate unique workspace ID
    workspace_id = f"ws-{request.workspace_name.lower().replace(' ', '-')}-{generate_id()}"
    
    # 2. Create workspace infrastructure
    workspace_data = {
        "workspace_id": workspace_id,
        "workspace_name": request.workspace_name,
        "owner_email": request.owner_email,
        "users": request.users,
        "services": request.services,
        "data_bucket": f"{workspace_id}-data",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # 3. Store workspace metadata
    await store_workspace_metadata(workspace_data)
    
    # 4. Provision selected services
    service_results = {}
    
    for service in request.services:
        if service.service_type == "flyte":
            # 🎯 THIS IS WHERE FLYTE PROJECT GETS AUTO-CREATED
            flyte_result = await provision_flyte_service(workspace_data)
            service_results["flyte"] = flyte_result
        elif service.service_type == "sagemaker":
            sagemaker_result = await provision_sagemaker_service(workspace_data)
            service_results["sagemaker"] = sagemaker_result
        # ... other services
    
    return {
        "workspace_id": workspace_id,
        "status": "created",
        "services": service_results,
        "console_urls": {
            "flyte": f"https://flyte-console.company.com/console/projects/{workspace_id}" if "flyte" in service_results else None
        }
    }

async def provision_flyte_service(workspace_data: dict):
    """Automatically provision Flyte project for workspace"""
    
    # Call the Workspace-Flyte Integration Service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://workspace-flyte-integration:8080/provision",
            json=workspace_data,
            timeout=30.0
        )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to provision Flyte: {response.text}"
        )
```

### Step 2: Workspace-Flyte Integration Service

#### Automatic Project Creation Logic
```python
# workspace_flyte_integration.py
from fastapi import FastAPI, HTTPException
from flytekit.clients.friendly import SynchronousFlyteClient
from flytekit.models import Project, Domain
from kubernetes import client, config
import asyncio
import yaml

app = FastAPI(title="Workspace-Flyte Integration")

class FlyteProjectProvisioner:
    def __init__(self):
        # Initialize Flyte client
        self.flyte_client = SynchronousFlyteClient("flyte-admin.company.com:443")
        
        # Initialize Kubernetes client
        config.load_incluster_config()  # Running inside K8s
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()
        self.k8s_rbac_v1 = client.RbacAuthorizationV1Api()
        self.k8s_networking_v1 = client.NetworkingV1Api()
    
    async def auto_create_project(self, workspace_data: dict):
        """Automatically create Flyte project from workspace data"""
        
        workspace_id = workspace_data["workspace_id"]
        workspace_name = workspace_data["workspace_name"]
        users = workspace_data["users"]
        
        try:
            # 🎯 STEP 1: CREATE FLYTE PROJECT
            project = await self.create_flyte_project(workspace_id, workspace_name)
            
            # 🎯 STEP 2: CREATE KUBERNETES NAMESPACE
            namespace = await self.create_k8s_namespace(workspace_id)
            
            # 🎯 STEP 3: SETUP RESOURCE QUOTAS
            quota = await self.create_resource_quota(workspace_id)
            
            # 🎯 STEP 4: CONFIGURE USER PERMISSIONS
            rbac = await self.setup_user_permissions(workspace_id, users)
            
            # 🎯 STEP 5: SETUP DATA ACCESS
            data_access = await self.configure_data_access(workspace_id, workspace_data["data_bucket"])
            
            # 🎯 STEP 6: CONFIGURE NETWORK POLICIES
            network_policy = await self.create_network_policy(workspace_id)
            
            return {
                "status": "success",
                "project_id": workspace_id,
                "project_name": f"Flyte - {workspace_name}",
                "namespace": f"flyte-{workspace_id}",
                "console_url": f"https://flyte-console.company.com/console/projects/{workspace_id}",
                "details": {
                    "project": project,
                    "namespace": namespace,
                    "quota": quota,
                    "rbac": rbac,
                    "data_access": data_access,
                    "network_policy": network_policy
                }
            }
            
        except Exception as e:
            # Cleanup on failure
            await self.cleanup_failed_provisioning(workspace_id)
            raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")
    
    async def create_flyte_project(self, workspace_id: str, workspace_name: str):
        """Create Flyte project using Admin API"""
        
        # Define project with workspace mapping
        project = Project(
            id=workspace_id,  # 🎯 WORKSPACE ID BECOMES PROJECT ID
            name=f"Flyte - {workspace_name}",
            description=f"Auto-created Flyte project for workspace {workspace_id}",
            domains=[
                Domain(id="development", name="Development Environment"),
                Domain(id="staging", name="Staging Environment"),
                Domain(id="production", name="Production Environment")
            ]
        )
        
        # Create project via Flyte Admin API
        created_project = self.flyte_client.create_project(project)
        
        # Configure project-level settings
        await self.configure_project_settings(workspace_id)
        
        return {
            "project_id": workspace_id,
            "domains": ["development", "staging", "production"],
            "status": "created"
        }
    
    async def create_k8s_namespace(self, workspace_id: str):
        """Create dedicated Kubernetes namespace for workspace"""
        
        namespace_name = f"flyte-{workspace_id}"
        
        # Create namespace manifest
        namespace_manifest = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=namespace_name,
                labels={
                    "workspace-id": workspace_id,
                    "flyte.org/tenant": workspace_id,
                    "managed-by": "workspace-service",
                    "service": "flyte"
                },
                annotations={
                    "workspace.company.com/created-by": "auto-provisioning",
                    "workspace.company.com/workspace-name": workspace_id
                }
            )
        )
        
        # Create namespace
        created_namespace = self.k8s_core_v1.create_namespace(namespace_manifest)
        
        return {
            "namespace": namespace_name,
            "status": "created",
            "labels": created_namespace.metadata.labels
        }
    
    async def create_resource_quota(self, workspace_id: str):
        """Create resource quota for workspace"""
        
        namespace_name = f"flyte-{workspace_id}"
        
        # Define resource limits based on workspace tier
        quota_manifest = client.V1ResourceQuota(
            metadata=client.V1ObjectMeta(
                name=f"{workspace_id}-quota",
                namespace=namespace_name
            ),
            spec=client.V1ResourceQuotaSpec(
                hard={
                    "requests.cpu": "20",        # 20 CPU cores
                    "requests.memory": "40Gi",   # 40GB RAM
                    "limits.cpu": "40",          # 40 CPU cores max
                    "limits.memory": "80Gi",     # 80GB RAM max
                    "pods": "100",               # Max 100 pods
                    "persistentvolumeclaims": "20"
                }
            )
        )
        
        # Create quota
        created_quota = self.k8s_core_v1.create_namespaced_resource_quota(
            namespace=namespace_name,
            body=quota_manifest
        )
        
        return {
            "quota_name": f"{workspace_id}-quota",
            "limits": quota_manifest.spec.hard,
            "status": "created"
        }
    
    async def setup_user_permissions(self, workspace_id: str, users: List[dict]):
        """Setup RBAC for workspace users"""
        
        namespace_name = f"flyte-{workspace_id}"
        rbac_results = []
        
        for user in users:
            user_id = user["user_id"]
            role = user["role"]  # "owner" or "contributor"
            
            # Determine permissions based on role
            if role == "owner":
                permissions = [
                    # Full workflow management
                    {"apiGroups": [""], "resources": ["pods", "configmaps", "secrets"], "verbs": ["*"]},
                    {"apiGroups": ["batch"], "resources": ["jobs"], "verbs": ["*"]},
                    {"apiGroups": ["apps"], "resources": ["deployments"], "verbs": ["get", "list"]}
                ]
            else:  # contributor
                permissions = [
                    # Limited workflow management
                    {"apiGroups": [""], "resources": ["pods", "configmaps"], "verbs": ["get", "list", "create"]},
                    {"apiGroups": ["batch"], "resources": ["jobs"], "verbs": ["get", "list", "create"]}
                ]
            
            # Create role for user
            role_manifest = client.V1Role(
                metadata=client.V1ObjectMeta(
                    name=f"{workspace_id}-{user_id}-role",
                    namespace=namespace_name
                ),
                rules=[client.V1PolicyRule(**perm) for perm in permissions]
            )
            
            # Create role binding
            role_binding_manifest = client.V1RoleBinding(
                metadata=client.V1ObjectMeta(
                    name=f"{workspace_id}-{user_id}-binding",
                    namespace=namespace_name
                ),
                subjects=[client.V1Subject(
                    kind="User",
                    name=user_id,
                    api_group="rbac.authorization.k8s.io"
                )],
                role_ref=client.V1RoleRef(
                    kind="Role",
                    name=f"{workspace_id}-{user_id}-role",
                    api_group="rbac.authorization.k8s.io"
                )
            )
            
            # Apply RBAC
            created_role = self.k8s_rbac_v1.create_namespaced_role(
                namespace=namespace_name,
                body=role_manifest
            )
            
            created_binding = self.k8s_rbac_v1.create_namespaced_role_binding(
                namespace=namespace_name,
                body=role_binding_manifest
            )
            
            rbac_results.append({
                "user_id": user_id,
                "role": role,
                "k8s_role": f"{workspace_id}-{user_id}-role",
                "status": "created"
            })
            
            # Also update Flyte authorization
            await self.update_flyte_user_permissions(workspace_id, user_id, role)
        
        return rbac_results
    
    async def configure_data_access(self, workspace_id: str, data_bucket: str):
        """Setup workspace-specific data access"""
        
        namespace_name = f"flyte-{workspace_id}"
        
        # Create service account with IAM role annotation
        service_account_manifest = client.V1ServiceAccount(
            metadata=client.V1ObjectMeta(
                name=f"flyte-{workspace_id}-runner",
                namespace=namespace_name,
                annotations={
                    "eks.amazonaws.com/role-arn": f"arn:aws:iam::ACCOUNT:role/FlyteWorkspace-{workspace_id}-Role"
                }
            )
        )
        
        # Create service account
        created_sa = self.k8s_core_v1.create_namespaced_service_account(
            namespace=namespace_name,
            body=service_account_manifest
        )
        
        # Note: IAM role creation would be handled by your existing AWS infrastructure
        # This service account will be used by all Flyte tasks in this workspace
        
        return {
            "service_account": f"flyte-{workspace_id}-runner",
            "data_bucket": data_bucket,
            "iam_role": f"FlyteWorkspace-{workspace_id}-Role",
            "status": "configured"
        }

# API endpoint that workspace service calls
@app.post("/provision")
async def provision_flyte_project(workspace_data: dict):
    """Auto-provision Flyte project when workspace is created"""
    
    provisioner = FlyteProjectProvisioner()
    result = await provisioner.auto_create_project(workspace_data)
    
    return result
```

### Step 3: Event-Driven Updates

#### Workspace Change Handler
```python
# workspace_change_handler.py
import asyncio
from kubernetes import client, config, watch
import json

class WorkspaceChangeWatcher:
    """Watches for workspace changes and updates Flyte accordingly"""
    
    def __init__(self):
        config.load_incluster_config()
        self.k8s_core = client.CoreV1Api()
        self.provisioner = FlyteProjectProvisioner()
    
    async def watch_workspace_events(self):
        """Watch for workspace ConfigMap changes"""
        
        w = watch.Watch()
        
        # Watch workspace configuration changes
        for event in w.stream(
            self.k8s_core.list_config_map_for_all_namespaces,
            label_selector="app=workspace-config"
        ):
            event_type = event['type']
            config_map = event['object']
            
            workspace_data = json.loads(config_map.data.get('workspace.json', '{}'))
            workspace_id = workspace_data.get('workspace_id')
            
            if not workspace_id:
                continue
                
            # Check if Flyte is enabled for this workspace
            services = workspace_data.get('services', [])
            flyte_enabled = any(s.get('service_type') == 'flyte' for s in services)
            
            if event_type == "ADDED" and flyte_enabled:
                # New workspace with Flyte - auto-create project
                await self.provisioner.auto_create_project(workspace_data)
                
            elif event_type == "MODIFIED" and flyte_enabled:
                # Workspace users changed - update permissions
                await self.provisioner.setup_user_permissions(
                    workspace_id, 
                    workspace_data.get('users', [])
                )
                
            elif event_type == "DELETED":
                # Workspace deleted - cleanup Flyte resources
                await self.provisioner.cleanup_workspace_resources(workspace_id)
```

## 🎯 Complete Integration Flow

### Example: Data Scientist Creates Workspace

```bash
# 1. Data scientist creates workspace through your company's portal
curl -X POST https://workspace-api.company.com/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "workspace_name": "Customer Segmentation Analysis",
    "owner_email": "alice@company.com",
    "services": [
      {"service_type": "sagemaker", "config": {}},
      {"service_type": "flyte", "config": {}},        # 🎯 This triggers auto-creation
      {"service_type": "bedrock", "config": {}}
    ],
    "users": [
      {"user_id": "alice", "email": "alice@company.com", "role": "owner"},
      {"user_id": "bob", "email": "bob@company.com", "role": "contributor"}
    ]
  }'

# 2. System automatically:
#    ✅ Generates workspace_id: "ws-customer-segmentation-analysis-001"
#    ✅ Creates Flyte project: "ws-customer-segmentation-analysis-001"
#    ✅ Creates K8s namespace: "flyte-ws-customer-segmentation-analysis-001"
#    ✅ Sets up RBAC for alice (owner) and bob (contributor)
#    ✅ Configures data access to "ws-customer-segmentation-analysis-001-data" bucket

# 3. Response includes Flyte access info
{
  "workspace_id": "ws-customer-segmentation-analysis-001",
  "status": "created",
  "services": {
    "flyte": {
      "project_id": "ws-customer-segmentation-analysis-001",
      "console_url": "https://flyte-console.company.com/console/projects/ws-customer-segmentation-analysis-001",
      "status": "provisioned"
    }
  }
}
```

### User Workflow Registration

```python
# Alice can now register workflows to her auto-created project
# workspace_id automatically becomes the project_id

# The workspace context is automatically set
@workflow
def customer_segmentation_workflow(customer_data: str) -> str:
    # Automatically uses workspace data bucket
    data = load_workspace_data(customer_data)
    segments = analyze_customer_segments(data)
    return save_results(segments)

# Registration uses workspace project automatically
# pyflyte register customer_segmentation_workflow.py
# Project: ws-customer-segmentation-analysis-001 (auto-detected from workspace context)
```

## 🎯 Key Benefits

✅ **Zero Manual Configuration**: Project creation is 100% automatic
✅ **Workspace-Native**: Flyte becomes just another workspace service  
✅ **Seamless Integration**: Works with existing workspace infrastructure
✅ **Event-Driven**: Real-time updates when workspace changes
✅ **Scalable**: Handles thousands of workspaces automatically
✅ **Consistent**: Same experience across all workspace services

The magic is that when a data scientist selects "Flyte" as a service in their workspace, everything happens automatically behind the scenes! 🚀
