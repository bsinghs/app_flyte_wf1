# Use prebuilt flytekit base image for quick setup
FROM ghcr.io/flyteorg/flytekit:py3.9-1.10.3

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional ML packages for your scheduled pipeline
RUN pip install --no-cache-dir \
    seaborn \
    plotly \
    xgboost

# Copy all application code
COPY . .

# Default command for Flyte execution
CMD ["pyflyte", "serve"]
