# Files to sanitize before public commit

## Files containing organizational info:
1. **s3-access-policy-updated.json** - Contains account ID and cluster names
2. **ML_WORKFLOW_DEPLOYMENT_GUIDE.md** - Contains cluster names, account IDs
3. **S3_IAM_SETUP.md** - Contains full infrastructure details
4. **execution_config*.yaml** - May contain version IDs (less sensitive)

## Recommended replacements:
- `245966534215` → `YOUR_ACCOUNT_ID`
- `education-eks-vV8VCAqw` → `YOUR_CLUSTER_NAME`  
- `bsingh-ml-workflows` → `your-ml-workflows`
- Node group names → `YOUR_NODE_GROUP_NAME`

## Keep as-is (safe):
- ml_pipeline_improved.py
- config.py (after sanitizing bucket name)
- requirements.txt
- pyproject.toml
- Dockerfile
