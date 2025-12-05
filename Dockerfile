# Stage 1: Base - common foundation for both variants
FROM python:3.12-slim AS base

# Upgrade pip, setuptools and wheel
RUN pip install --upgrade pip setuptools wheel

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src ./src

# Stage 2: Minimal - PDF to PDF/A conversion only
FROM base AS minimal

# Install system dependencies for OCRmyPDF (without LibreOffice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-ita \
    ghostscript \
    qpdf \
    pngquant \
    unpaper \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Run the API service
CMD ["uvicorn", "pdfa.api:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: Full - complete functionality with LibreOffice support (default)
FROM base AS full

# Install system dependencies for OCRmyPDF and LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-ita \
    ghostscript \
    qpdf \
    pngquant \
    unpaper \
    libreoffice-common \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Run the API service
CMD ["uvicorn", "pdfa.api:app", "--host", "0.0.0.0", "--port", "8000"]
