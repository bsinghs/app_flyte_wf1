# Flyte ML Workflow Project

A comprehensive machine learning workflow project built with Flyte, featuring enterprise workspace integration and multi-tenant architecture.

## 📁 Project Structure

```
├── src/                              # Source code
│   ├── workflows/                    # Flyte workflow definitions
│   │   ├── ml_pipeline_improved.py   # Main ML pipeline
│   │   ├── batch_prediction_pipeline.py
│   │   ├── scheduled_ml_pipeline.py
│   │   └── resource_card.py
│   ├── configs/                      # Configuration files
│   │   ├── config.py                 # Python configuration
│   │   ├── project.yaml              # Flyte project config
│   │   ├── pyflyte.config           # Flyte CLI config
│   │   ├── pyproject.toml           # Python project config
│   │   └── requirements.txt         # Dependencies
│   └── data/                        # Data files
│       └── CleanCreditScoring.csv   # Sample dataset
├── containers/                      # Docker configurations
│   ├── Dockerfile                   # Basic Docker image
│   ├── Dockerfile.custom           # Custom ML image
│   └── Dockerfile.multistage       # Multi-stage build
├── scripts/                        # Build and deployment scripts
│   └── docker-build.sh            # Docker build automation
├── docs/                           # Documentation
│   ├── README.md                   # Main documentation
│   ├── architecture/               # Architecture documentation
│   │   ├── FLYTE_ARCHITECTURE_GUIDE.md
│   │   └── LAYERED_ARCHITECTURE_DIAGRAM.md
│   ├── guides/                     # Implementation guides
│   │   ├── FLYTE_MULTI_TENANT_GUIDE.md
│   │   ├── WORKSPACE_FLYTE_INTEGRATION.md
│   │   ├── AUTOMATIC_PROJECT_CREATION_FLOW.md
│   │   └── RBAC_LOCAL_VS_ENTERPRISE.md
│   └── deployment/                 # Deployment documentation
│       └── DEPLOYMENT_ARCHITECTURE.md
├── examples/                       # Example projects
│   ├── multi_file_example/         # Multi-file workflow example
│   └── oauth-learning/             # OAuth integration example
├── tests/                          # Test files
├── utils/                          # Utility functions
└── config/                         # Legacy config directory
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker
- Flyte cluster access

### Local Development
```bash
# Install dependencies
pip install -r src/configs/requirements.txt

# Configure Flyte connection
cp src/configs/pyflyte.config ~/.flyte/config.yaml

# Run workflow locally
pyflyte run src/workflows/ml_pipeline_improved.py credit_scoring_pipeline

# Register workflow to remote Flyte cluster
pyflyte register src/workflows/ml_pipeline_improved.py --project your-project
```

### Docker Development
```bash
# Build custom ML image
./scripts/docker-build.sh

# Run workflow in container
docker run -v $(pwd)/src/data:/data your-flyte-image
```

## 📚 Documentation

### Architecture Guides
- **[Flyte Architecture Guide](docs/architecture/FLYTE_ARCHITECTURE_GUIDE.md)** - Complete Flyte two-level architecture
- **[Layered Architecture Diagram](docs/architecture/LAYERED_ARCHITECTURE_DIAGRAM.md)** - Infrastructure stack visualization

### Implementation Guides
- **[Multi-Tenant Guide](docs/guides/FLYTE_MULTI_TENANT_GUIDE.md)** - Team-based multi-tenancy setup
- **[Workspace Integration](docs/guides/WORKSPACE_FLYTE_INTEGRATION.md)** - Enterprise workspace integration
- **[Automatic Project Creation](docs/guides/AUTOMATIC_PROJECT_CREATION_FLOW.md)** - Workspace-to-project mapping
- **[RBAC Comparison](docs/guides/RBAC_LOCAL_VS_ENTERPRISE.md)** - Local vs enterprise RBAC

### Deployment Guides
- **[Deployment Architecture](docs/deployment/DEPLOYMENT_ARCHITECTURE.md)** - FastAPI service deployment

## 🔧 Configuration

### Flyte Configuration
- **Project Config**: `src/configs/project.yaml`
- **CLI Config**: `src/configs/pyflyte.config`
- **Python Config**: `src/configs/config.py`

### Docker Configuration
- **Basic Image**: `containers/Dockerfile`
- **ML Optimized**: `containers/Dockerfile.custom`
- **Multi-stage**: `containers/Dockerfile.multistage`

## 🧪 Workflows

### Available Workflows
1. **Credit Scoring Pipeline** (`ml_pipeline_improved.py`)
   - Data loading and cleaning
   - Feature engineering
   - Model training (Random Forest)
   - Model evaluation

2. **Batch Prediction Pipeline** (`batch_prediction_pipeline.py`)
   - Large-scale batch inference
   - Result aggregation

3. **Scheduled ML Pipeline** (`scheduled_ml_pipeline.py`)
   - Automated daily/weekly runs
   - Model retraining

## 🏢 Enterprise Features

### Multi-Tenant Architecture
- **Team-based isolation** with dedicated namespaces
- **Dynamic RBAC** based on workspace roles
- **Automatic project provisioning** from workspace creation
- **Workspace-native integration** with existing company infrastructure

### Security & Compliance
- **Role-based access control** (Owner/Contributor/Viewer)
- **Data boundary enforcement** with S3 bucket isolation
- **Network policy isolation** between workspaces
- **Audit logging** for all workflow executions

## 🤝 Contributing

1. Create feature branch from `main`
2. Add your workflow to `src/workflows/`
3. Update documentation in `docs/`
4. Test locally and with Docker
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory
- **Examples**: See `examples/` for working samples
- **Issues**: Open GitHub issues for bugs and feature requests
