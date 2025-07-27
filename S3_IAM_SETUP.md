# S3 Bucket Access and IAM Policies for Flyte Workflows

This document outlines how to set up S3 bucket access for Flyte workflows running on EKS clusters, including policy examples and commands for different scenarios.

## Overview

Flyte workflows running on EKS need proper IAM permissions to access S3 buckets for reading datasets, writing model outputs, and storing results. This is achieved by attaching IAM policies to the EKS node group roles.

## Current Setup

### EKS Cluster Information
- **Cluster Name**: `education-eks-vV8VCAqw`
- **Account ID**: `245966534215`
- **Node Groups**: 
  - `node-group-1-2025072404024606990000001e`
  - `node-group-2-2025072404024606990000001d`

### Current S3 Buckets
- **Personal ML Workflows**: `bsingh-ml-workflows`
- **Flyte System Buckets**:
  - `education-eks-vv8vcaqw-flyte-metadata-vv8vcaqw`
  - `education-eks-vv8vcaqw-flyte-userdata-vv8vcaqw`

## IAM Policy Examples

### 1. Single Bucket Access Policy

For accessing a specific bucket (like your personal ML workflows bucket):

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
                "arn:aws:s3:::bsingh-ml-workflows/*"
            ]
        }
    ]
}
```

### 2. Multiple Buckets Access Policy

For accessing multiple ML workflow buckets:

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
                "arn:aws:s3:::ml-project-1",
                "arn:aws:s3:::ml-project-1/*",
                "arn:aws:s3:::ml-project-2",
                "arn:aws:s3:::ml-project-2/*",
                "arn:aws:s3:::shared-ml-datasets",
                "arn:aws:s3:::shared-ml-datasets/*"
            ]
        }
    ]
}
```

### 3. Folder-Specific Access Policy

For accessing specific folders within a bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::shared-bucket",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "team-a/*",
                        "team-b/*"
                    ]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::shared-bucket/team-a/*",
                "arn:aws:s3:::shared-bucket/team-b/*"
            ]
        }
    ]
}
```

### 4. Read-Only Access Policy

For datasets that should only be read:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::public-datasets",
                "arn:aws:s3:::public-datasets/*"
            ]
        }
    ]
}
```

## Commands Reference

### 1. Check Current EKS Cluster Information

```bash
# Get cluster role ARN
aws eks describe-cluster --name education-eks-vV8VCAqw --profile adfs --query 'cluster.roleArn'

# List node groups
aws eks list-nodegroups --cluster-name education-eks-vV8VCAqw --profile adfs

# Get node group IAM role
aws eks describe-nodegroup --cluster-name education-eks-vV8VCAqw --nodegroup-name <nodegroup-name> --profile adfs --query 'nodegroup.nodeRole'
```

### 2. Check Current IAM Policies

```bash
# List attached policies for a role
aws iam list-attached-role-policies --role-name <role-name> --profile adfs

# List inline policies for a role
aws iam list-role-policies --role-name <role-name> --profile adfs

# Get policy details
aws iam get-policy --policy-arn <policy-arn> --profile adfs
aws iam get-policy-version --policy-arn <policy-arn> --version-id v1 --profile adfs
```

### 3. Create and Attach New S3 Access Policy

```bash
# Step 1: Create the policy JSON file
cat > s3-access-policy.json << EOF
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
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
EOF

# Step 2: Create the IAM policy
aws iam create-policy \
    --policy-name YourPolicyName \
    --policy-document file://s3-access-policy.json \
    --profile adfs

# Step 3: Attach policy to node group roles
aws iam attach-role-policy \
    --role-name <node-group-role-name> \
    --policy-arn arn:aws:iam::<account-id>:policy/YourPolicyName \
    --profile adfs
```

### 4. Create S3 Bucket with Proper Organization

```bash
# Create bucket
aws s3 mb s3://your-ml-bucket --profile adfs

# Create folder structure
aws s3api put-object --bucket your-ml-bucket --key project1/data/ --profile adfs
aws s3api put-object --bucket your-ml-bucket --key project1/models/ --profile adfs
aws s3api put-object --bucket your-ml-bucket --key project1/results/ --profile adfs

# Upload data with folder structure
aws s3 cp local-file.csv s3://your-ml-bucket/project1/data/dataset.csv --profile adfs
```

### 5. Verify Access

```bash
# Test bucket access
aws s3 ls s3://your-bucket-name --profile adfs

# Test file upload
echo "test" > test.txt
aws s3 cp test.txt s3://your-bucket-name/test.txt --profile adfs

# Test file download
aws s3 cp s3://your-bucket-name/test.txt downloaded-test.txt --profile adfs
```

## Applied Example: Current Setup

Here's what was implemented for the current project:

### 1. Created Policy
```bash
aws iam create-policy \
    --policy-name FlyteMLS3Access \
    --policy-document file://s3-access-policy.json \
    --profile adfs
```

### 2. Attached to Node Groups
```bash
# Node Group 1
aws iam attach-role-policy \
    --role-name node-group-1-eks-node-group-20250724035220727000000001 \
    --policy-arn arn:aws:iam::245966534215:policy/FlyteMLS3Access \
    --profile adfs

# Node Group 2
aws iam attach-role-policy \
    --role-name node-group-2-eks-node-group-20250724035220727200000003 \
    --policy-arn arn:aws:iam::245966534215:policy/FlyteMLS3Access \
    --profile adfs
```

### 3. Bucket Structure
```
s3://bsingh-ml-workflows/
├── credit-scoring/
│   ├── data/
│   │   └── CleanCreditScoring.csv
│   ├── models/
│   └── results/
├── fraud-detection/
│   ├── data/
│   ├── models/
│   └── results/
└── customer-segmentation/
    ├── data/
    ├── models/
    └── results/
```

## Best Practices

1. **Principle of Least Privilege**: Only grant the minimum permissions needed
2. **Separate Buckets**: Use different buckets for different projects/teams
3. **Folder Organization**: Organize data with clear folder structures
4. **Policy Naming**: Use descriptive policy names that indicate purpose
5. **Regular Audits**: Periodically review and clean up unused policies
6. **Backup Policies**: Keep copies of policy documents for disaster recovery

## Troubleshooting

### Common Issues

1. **Access Denied**: Check if policy is attached to the correct role
2. **Bucket Not Found**: Verify bucket name and region
3. **Permission Boundary**: Check if there are permission boundaries limiting access
4. **Policy Conflicts**: Ensure no explicit deny statements override permissions

### Debug Commands

```bash
# Check what role the pods are using
kubectl get pods -n flyte -o yaml | grep serviceAccount

# Check node instance profile
aws ec2 describe-instances --instance-ids <instance-id> --profile adfs --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Test from within EKS cluster
kubectl run debug-pod --image=amazon/aws-cli:latest --rm -it -- /bin/bash
# Then inside pod: aws s3 ls s3://your-bucket
```

## Security Considerations

1. **Encryption**: Enable S3 bucket encryption
2. **Versioning**: Enable versioning for important datasets
3. **Access Logging**: Enable S3 access logging
4. **VPC Endpoints**: Consider using VPC endpoints for S3 access
5. **Cross-Account Access**: Use IAM roles for cross-account access instead of access keys

---

*Last Updated: July 26, 2025*
