# syntax=docker/dockerfile:1

# --------------------- Build Stage ---------------------
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a temporary directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -------------------- Runtime Stage --------------------
FROM python:3.11-slim
WORKDIR /app

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Add non-root user
RUN useradd --create-home appuser

# Copy application code
COPY . .
RUN mkdir -p logs data results && chown -R appuser:appuser /app

USER appuser

# Environment configuration
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Expose health check port
EXPOSE 8080

CMD ["python", "main.py"]
