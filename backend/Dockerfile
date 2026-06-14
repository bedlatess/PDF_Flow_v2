# Python backend - FastAPI
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing / OCR / Office conversion
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    tesseract-ocr-spa \
    poppler-utils \
    libreoffice \
    chromium \
    fonts-liberation \
    fonts-noto-color-emoji \
    libmagic1 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
# E (Elevation of Privilege): Non-root containers
RUN useradd -m -u 1000 pdfflow && \
    chown -R pdfflow:pdfflow /app && \
    mkdir -p /tmp/pdf-flow/uploads && \
    chown -R pdfflow:pdfflow /tmp/pdf-flow

USER pdfflow

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
