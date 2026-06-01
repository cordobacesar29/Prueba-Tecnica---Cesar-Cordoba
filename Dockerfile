# MineCatalog RAG - Production Dockerfile
# Build: docker build -t minecatalog-rag:latest .
# Run: docker run -d -e OPENAI_API_KEY=sk-xxx -p 8000:8000 minecatalog-rag:latest

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY rag_pipeline.py .
COPY prompt_engineering.py .

# Copy documentation
COPY docs/ ./docs/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "main.py"]
