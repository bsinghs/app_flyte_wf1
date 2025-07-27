# ⚙️ Configuration Files

This directory contains all configuration files for the Flyte ML workflow application.

## 📁 Configuration Files

### 🔐 **Flyte Authentication**
- **`flyte-auth-config.yaml`**
  - OAuth configuration for Flyte authentication
  - Corporate SSO integration settings
  - PKCE and redirect URI configuration

- **`flyte-config-backup.yaml`**
  - Backup of working Flyte configuration
  - Fallback configuration for troubleshooting

### 🚀 **Workflow Execution**
- **`execution_config.yaml`**
  - Base execution configuration
  - Resource limits and environment settings

- **`execution_config_v2.yaml`**
  - Enhanced execution configuration
  - Improved resource allocation

- **`execution_config_v3.yaml`**
  - Latest execution configuration
  - Optimized for production workloads

### 🗄️ **AWS S3 Integration**
- **`s3-access-policy.json`**
  - IAM policy for S3 bucket access
  - Secure permissions for Flyte workflows

- **`s3-access-policy-updated.json`**
  - Updated S3 access policy
  - Enhanced security and permissions

## 🔧 Usage Guidelines

### **Development Environment**
```bash
# Use base configuration for local development
flytectl config init --config execution_config.yaml
```

### **Testing Environment**
```bash
# Use v2 configuration for testing
flytectl config init --config execution_config_v2.yaml
```

### **Production Environment**
```bash
# Use v3 configuration for production workloads
flytectl config init --config execution_config_v3.yaml
```

## 🔒 Security Notes

- **Never commit sensitive credentials** to version control
- **Use environment variables** for sensitive configuration
- **Rotate credentials regularly** in production environments
- **Follow principle of least privilege** for IAM policies

## 📝 Configuration Management

- **Version Control**: Track configuration changes
- **Environment Separation**: Different configs for dev/test/prod
- **Documentation**: Document all configuration parameters
- **Validation**: Test configurations before deployment

## 🚨 Important Files

- **`execution_config_v3.yaml`**: Current production configuration
- **`s3-access-policy-updated.json`**: Current S3 permissions
- **`flyte-auth-config.yaml`**: OAuth authentication settings

## 🔄 Updating Configurations

1. **Test locally** with new configuration
2. **Validate** with development environment
3. **Deploy** to staging for testing
4. **Promote** to production after validation
5. **Backup** previous working configuration
