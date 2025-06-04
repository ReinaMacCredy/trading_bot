# Multi-stage build for Professional Discord Trading Bot
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 tradingbot

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/tradingbot/.local

# Copy application code
COPY --chown=tradingbot:tradingbot . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/home/tradingbot/.local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create necessary directories
RUN mkdir -p logs data results && \
    chown -R tradingbot:tradingbot logs data results

# Switch to non-root user
USER tradingbot

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/tmp/bot_healthy') else 1)"

# Expose port for health monitoring (optional)
EXPOSE 8080

# Start the bot
CMD ["python", "main.py"] 