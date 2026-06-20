FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Setup directories for mount points
RUN mkdir -p /app/dataset /app/outputs

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV GEMINI_API_KEY=""
ENV DATASET_ROOT="/app/dataset"

# Entrypoint to run claims review
ENTRYPOINT ["python", "main.py"]
