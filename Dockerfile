# Multi-stage Dockerfile for Electronic Components Inventory Bot
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR and language packs
    tesseract-ocr \
    tesseract-ocr-eng \
    # OpenCV dependencies
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create temp directory
RUN mkdir -p /tmp/inventory_bot && chmod 777 /tmp/inventory_bot

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app /tmp/inventory_bot

# Switch to non-root user
USER botuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TEMP_DIR=/tmp/inventory_bot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the bot
CMD ["python", "-u", "main.py"]
