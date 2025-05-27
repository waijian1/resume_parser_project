# Use an official MLflow image as the base
FROM ghcr.io/mlflow/mlflow:v3.0.0rc2 
# (You can check for the absolute latest tag on ghcr.io/mlflow/mlflow if desired)

# Install boto3 to enable S3 artifact store functionality
# Also good to ensure pip is up to date
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir boto3