FROM python:3.11-slim

WORKDIR /app

# Cài đặt dependencies cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt packages
COPY requirements-simple.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY main.py web_server.py ./
COPY config/ ./config/

# Tạo thư mục logs
RUN mkdir -p logs data results

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8080 8000

# Default command
CMD ["python", "main.py"] 