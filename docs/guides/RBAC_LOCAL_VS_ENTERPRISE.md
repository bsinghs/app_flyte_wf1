# RBAC in Local Development vs Enterprise Workspace Integration

## 🔧 Current State: Local Development with pyflyte/flytectl

### How RBAC Works Today (Local Development)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Local Development Setup                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               Your Local Machine                            │    │
│  │                                                             │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │                pyflyte/flytectl                     │    │    │
│  │  │                                                     │    │    │
│  │  │  • ~/.flyte/config.yaml                            │    │    │
│  │  │  • Local credentials                               │    │    │
│  │  │  • Direct API calls                                │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                            │                                        │
│                            │ HTTPS + Auth Headers                   │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                 Flyte Admin API                             │    │
│  │                                                             │    │
│  │  Authentication Methods:                                    │    │
│  │  1️⃣ No Auth (insecure=true)                                │    │
│  │  2️⃣ Basic Auth (username/password)                         │    │
│  │  3️⃣ OAuth 2.0 (client credentials)                         │    │
│  │  4️⃣ OIDC (company SSO)                                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Your Current ~/.flyte/config.yaml

```yaml
# ~/.flyte/config.yaml - What you probably have now
admin:
  endpoint: flyte-admin.company.com  # Your Flyte cluster
  insecure: false                    # HTTPS enabled
  
# Option 1: No authentication (if cluster is open)
# insecure: true

# Option 2: Basic authentication
# authType: basic
# credentials:
#   username: "your-username"
#   password: "your-password"

# Option 3: OAuth client credentials
# authType: clientSecret
# clientId: "flyte-client"
# clientSecret: "your-client-secret"

# Option 4: OIDC with your company SSO
# authType: oidc
# clientId: "flyte-local-client"
# scopes: ["openid", "profile", "email"]

project: flytesnacks    # Default project you're using
domain: development     # Default domain
```

### Current Authentication Flow

```python
# When you run: pyflyte register workflow.py
# This happens behind the scenes:

1. # pyflyte reads ~/.flyte/config.yaml
   config = load_flyte_config()
   
2. # Creates authenticated client
   if config.auth_type == "basic":
       headers = {"Authorization": f"Basic {base64_encode(username:password)}"}
   elif config.auth_type == "clientSecret":
       # OAuth flow - gets access token
       token = get_oauth_token(client_id, client_secret)
       headers = {"Authorization": f"Bearer {token}"}
   elif config.auth_type == "oidc":
       # Company SSO flow
       token = do_oidc_flow(client_id, redirect_uri)
       headers = {"Authorization": f"Bearer {token}"}
   
3. # Makes API calls to Flyte Admin
   response = requests.post(
       "https://flyte-admin.company.com/api/v1/workflows",
       headers=headers,
       json=workflow_spec
   )
```

## 🎯 RBAC Models: Current vs Enterprise

### Model 1: Basic/No RBAC (What You Likely Have Now)

```yaml
# Flyte Admin configuration - basic setup
auth:
  authenticatedUrl: "https://flyte-admin.company.com"
  useAuth: false  # 🚨 No authentication - anyone can access
  
# OR minimal auth with single admin user
auth:
  useAuth: true
  userAuth:
    openId:
      baseUrl: "https://company.okta.com"
      scopes: ["openid", "profile", "email"]
      clientId: "flyte-admin"
```

**Current Permissions:**
- ✅ **Full access** to all projects
- ✅ **Create, read, update, delete** workflows
- ✅ **Execute any workflow** in any domain
- ✅ **Access all data** (no isolation)

### Model 2: Project-Based RBAC (Intermediate)

```yaml
# Flyte Admin - project-level permissions
authorization:
  type: "adminAuthorizationServer"
  adminAuthorizationServer:
    enable: true
    
projects:
  - id: "ml-team-project"
    users:
      - id: "alice@company.com"
        role: "admin"    # Full project access
      - id: "bob@company.com" 
        role: "user"     # Read + execute only
        
  - id: "analytics-project"  
    users:
      - id: "charlie@company.com"
        role: "admin"
```

**Permissions by Role:**
```python
# Admin role
permissions = [
    "workflows:create", "workflows:read", "workflows:update", "workflows:delete",
    "launchplans:create", "launchplans:read", "launchplans:update", "launchplans:delete", 
    "executions:create", "executions:read", "executions:terminate",
    "tasks:read", "tasks:create"
]

# User role  
permissions = [
    "workflows:read", "workflows:execute",
    "launchplans:read", "launchplans:execute",
    "executions:create", "executions:read",
    "tasks:read"
]
```

### Model 3: Enterprise Workspace RBAC (Our Design)

```python
# Dynamic workspace-based RBAC
class WorkspaceRBAC:
    def __init__(self, workspace_id: str, user_id: str, role: str):
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.role = role
        
    def get_flyte_permissions(self) -> Dict[str, List[str]]:
        """Get Flyte permissions based on workspace role"""
        
        if self.role == "owner":
            return {
                "project": self.workspace_id,  # Can only access own workspace project
                "domains": ["development", "staging", "production"],
                "permissions": [
                    "workflows:*",      # Full workflow access
                    "launchplans:*",    # Full launch plan access  
                    "executions:*",     # Full execution access
                    "data:read_write",  # Read/write workspace data
                    "secrets:read"      # Access workspace secrets
                ]
            }
        elif self.role == "contributor":
            return {
                "project": self.workspace_id,
                "domains": ["development", "staging"],  # No production
                "permissions": [
                    "workflows:create", "workflows:read", "workflows:execute",
                    "launchplans:create", "launchplans:read", "launchplans:execute",
                    "executions:create", "executions:read",
                    "data:read_write",
                    "secrets:read"
                ]
            }
        else:  # viewer
            return {
                "project": self.workspace_id,
                "domains": ["development"],
                "permissions": [
                    "workflows:read",
                    "launchplans:read", 
                    "executions:read",
                    "data:read_only"
                ]
            }
```

## 🔍 How Your Current Local Setup Works

### When You Run pyflyte register

```bash
# Your command
pyflyte register --project flytesnacks --domain development workflow.py

# What happens:
1. # Reads your config
   config = load_config("~/.flyte/config.yaml")
   
2. # Authenticates (if auth enabled)
   client = FlyteClient(
       endpoint=config.endpoint,
       credentials=config.credentials
   )
   
3. # Checks permissions (if RBAC enabled)
   if client.has_permission("workflows:create", "flytesnacks", "development"):
       # Register workflow
       client.create_workflow(workflow_spec)
   else:
       raise PermissionDenied("Cannot create workflows in project flytesnacks")
```

### When You Execute a Workflow

```bash
# Your command  
pyflyte run --remote workflow.py my_workflow --input_data="s3://bucket/data.csv"

# What happens:
1. # Creates launch plan
   launch_plan = client.create_launch_plan(
       project="flytesnacks",
       domain="development", 
       workflow=workflow_spec,
       inputs={"input_data": "s3://bucket/data.csv"}
   )
   
2. # Checks execution permissions
   if client.has_permission("executions:create", "flytesnacks", "development"):
       execution = client.create_execution(launch_plan)
   else:
       raise PermissionDenied()
       
3. # Kubernetes execution (uses service account)
   # Pod runs with service account that has IAM role for S3 access
```

## 🚀 Evolution: Local → Enterprise

### Phase 1: Your Current Setup (Minimal RBAC)

```yaml
# ~/.flyte/config.yaml - Basic setup
admin:
  endpoint: flyte-admin.company.com
  insecure: true  # OR basic auth
project: flytesnacks
domain: development

# Result: Full access to everything
```

### Phase 2: Project-Based Access

```yaml
# ~/.flyte/config.yaml - Project isolation
admin:
  endpoint: flyte-admin.company.com
  authType: oidc
  clientId: "flyte-local-client"
project: ml-team-project  # Your assigned project
domain: development

# Result: Access only to ml-team-project
```

### Phase 3: Workspace Integration

```yaml
# ~/.flyte/config.yaml - Workspace context
admin:
  endpoint: flyte-admin.company.com
  authType: oidc
  clientId: "workspace-flyte-client"
  
# Workspace context (auto-detected or configured)
workspace:
  workspace_id: "ws-customer-analysis-001"  # Auto-becomes project
  data_bucket: "ws-customer-analysis-001-data"
  
# Result: Automatic project mapping + data isolation
```

### Workspace Authentication Flow

```python
# Enhanced authentication with workspace context
class WorkspaceAwareFlyteClient:
    def __init__(self):
        # Get workspace context from environment or config
        self.workspace_id = os.getenv("WORKSPACE_ID") or self.detect_workspace()
        self.user_token = self.get_user_token()  # From company SSO
        
        # Create Flyte client with workspace context
        self.client = FlyteClient(
            endpoint="flyte-admin.company.com",
            token=self.user_token,
            default_project=self.workspace_id,  # workspace_id = project_id
            headers={"X-Workspace-ID": self.workspace_id}
        )
    
    def register_workflow(self, workflow_file: str):
        """Register workflow to workspace project automatically"""
        
        # Automatic project selection based on workspace
        return self.client.register(
            workflow_file,
            project=self.workspace_id,  # No need to specify - auto-detected
            domain="development"
        )
    
    def execute_workflow(self, workflow_name: str, inputs: dict):
        """Execute with workspace data isolation"""
        
        # Automatically scope data access to workspace bucket
        workspace_inputs = self.scope_inputs_to_workspace(inputs)
        
        return self.client.execute(
            workflow_name,
            project=self.workspace_id,
            inputs=workspace_inputs
        )
```

## 🎯 Key Differences Summary

| Aspect | Current Local Setup | Enterprise Workspace |
|--------|-------------------|---------------------|
| **Authentication** | Manual config, basic/OAuth | Company SSO + workspace context |
| **Project Access** | Static project assignment | Dynamic workspace = project |
| **Data Access** | Manual S3 paths | Auto-scoped to workspace bucket |
| **User Management** | Admin-managed project users | Automatic workspace role mapping |
| **Isolation** | Project-level | Workspace-level (stronger) |
| **Scalability** | Manual project creation | Auto-provisioned on workspace creation |

The key insight is that your current local setup likely has minimal RBAC (or none), giving you full access to experiment. The enterprise workspace integration adds automatic context detection, stronger isolation, and seamless integration with your company's existing user management! 🚀
