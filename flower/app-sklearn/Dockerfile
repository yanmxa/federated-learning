# Use a smaller base image
FROM python:3.11-slim

# Set environment variables to reduce image size and improve pip behavior
ENV PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100

# Set the working directory
WORKDIR /app

# # Install system dependencies for building Python packages
# RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev build-base

# Copy only necessary project files
COPY pyproject.toml /app/

# Install Python dependencies from pyproject.toml using pip
RUN pip install -e .

# # Remove build dependencies to reduce image size
# RUN apk del gcc musl-dev libffi-dev openssl-dev build-base

# Copy the rest of the application files
COPY . /app

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/app

RUN chmod +x /app/entrypoint.sh

# Set the default entrypoint to Python
# 1. docker run --rm -e PYTHONPATH=/app quay.io/myan/flower-app app_sklearn/server_app.py --num-rounds 20
# 2. docker run --rm -e PYTHONPATH=/app quay.io/myan/flower-app app_sklearn/client_app.py --data-config "data-partition-1" --server-address 172.17.0.2:8080
ENTRYPOINT ["/app/entrypoint.sh"]



