#!/bin/bash

# Docker build and push script for custom Flyte workflows
# Usage: ./docker-build.sh [version]

set -e

# Configuration
REGISTRY="your-registry.com"  # Replace with your Docker registry
PROJECT_NAME="flyte-ml-workflows"
VERSION=${1:-"latest"}
IMAGE_NAME="${REGISTRY}/${PROJECT_NAME}:${VERSION}"

echo "🐳 Building Docker image: ${IMAGE_NAME}"

# Build the image
docker build -f Dockerfile.custom -t ${IMAGE_NAME} .

echo "✅ Build completed successfully!"

# Optional: Push to registry
read -p "Push to registry? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Pushing to registry..."
    docker push ${IMAGE_NAME}
    echo "✅ Push completed!"
else
    echo "ℹ️  Skipping push. To push later, run:"
    echo "   docker push ${IMAGE_NAME}"
fi

echo "🎯 Image ready: ${IMAGE_NAME}"
echo ""
echo "📋 Next steps:"
echo "1. Update your workflow files to use this image"
echo "2. Register workflows with: pyflyte register"
echo "3. Test execution with: pyflyte run"
