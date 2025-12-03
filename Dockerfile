FROM python:3.12-slim

# Upgrade pip, setuptools and wheel
RUN pip install --upgrade pip setuptools wheel

# Install system dependencies for OCRmyPDF and LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-calc \
    libreoffice-impress \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    ghostscript \
    qpdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src ./src

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Run the API service
CMD ["uvicorn", "pdfa.api:app", "--host", "0.0.0.0", "--port", "8000"]
