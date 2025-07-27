# 🚀 Flyte ML Workflow Application

This is a machine learning workflow application built for deployment on Flyte orchestration platform.

## 📁 Project Structure

```
├── README.md                    # This file
├── ml_pipeline_improved.py      # Main ML workflow (credit scoring)
├── CleanCreditScoring.csv      # Training dataset
├── requirements.txt            # Python dependencies
├── config.py                   # Application configuration
├── project.yaml               # Flyte project configuration
├── pyproject.toml             # Python project metadata
├── Dockerfile                 # Container configuration
│
├── 📚 docs/                   # Documentation
│   ├── FLYTECTL_DEEP_DIVE.md
│   ├── ML_WORKFLOW_DEPLOYMENT_GUIDE.md
│   ├── S3_IAM_SETUP.md
│   ├── SECURITY_REVIEW.md
│   └── CORPORATE_OAUTH_TROUBLESHOOTING.md
│
├── 🔐 oauth-learning/         # OAuth/PKCE learning materials
│   ├── OAUTH_STORY_DOCUMENTATION.md
│   ├── complete_oauth_demo.py
│   └── oauth_test.py
│
├── ⚙️ config/                 # Configuration files
│   ├── flyte-auth-config.yaml
│   ├── flyte-config-backup.yaml
│   ├── execution_config*.yaml
│   └── s3-access-policy*.json
│
└── .flyte/                   # Flyte local development
```

## 🏃‍♂️ Quick Start

### 1. Deploy ML Workflow
```bash
# Register workflow with Flyte
flytectl register files --project flyte-ml-workflow --domain development ml_pipeline_improved.py

# Execute workflow
flytectl create execution --project flyte-ml-workflow --domain development --name my-execution ml_pipeline_improved.py training_workflow
```

### 2. Monitor Execution
```bash
# Check execution status
flytectl get execution --project flyte-ml-workflow --domain development <execution-name>

# View logs
flytectl get logs --project flyte-ml-workflow --domain development <execution-name>
```

## 📊 ML Workflow Features

- **Credit Scoring Model**: Random Forest classifier for credit risk assessment
- **Data Processing**: Automated cleaning and feature engineering
- **S3 Integration**: Secure data storage and model artifacts
- **Resource Optimization**: Configured CPU/memory limits for cost efficiency
- **Monitoring**: Comprehensive logging and execution tracking

## 🔧 Configuration

- **Flyte Project**: `flyte-ml-workflow`
- **Domain**: `development`
- **S3 Bucket**: `flyte-ml-workflow-data`
- **Resource Limits**: 500m CPU, 1Gi memory

## 📚 Documentation

- **[ML Workflow Guide](docs/ML_WORKFLOW_DEPLOYMENT_GUIDE.md)**: Complete deployment instructions
- **[Flytectl Deep Dive](docs/FLYTECTL_DEEP_DIVE.md)**: Advanced CLI usage
- **[S3 Setup](docs/S3_IAM_SETUP.md)**: AWS configuration steps
- **[Security Review](docs/SECURITY_REVIEW.md)**: Security best practices

## 🔐 OAuth Learning

For corporate authentication understanding, see the `oauth-learning/` directory which contains:
- Complete OAuth PKCE implementation
- Step-by-step authentication flow documentation
- Corporate troubleshooting guides

## 🚀 Next Steps

1. **Scale Workflow**: Add data validation and model versioning
2. **Production Deployment**: Configure production domain and resources
3. **CI/CD Integration**: Automate workflow registration and testing
4. **Monitoring**: Set up alerting and performance tracking
