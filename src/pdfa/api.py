"""REST API providing PDF to PDF/A conversion backed by OCRmyPDF."""

from __future__ import annotations

import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa.converter import convert_to_pdfa
from pdfa.exceptions import OfficeConversionError, UnsupportedFormatError
from pdfa.format_converter import convert_office_to_pdf, is_office_document
from pdfa.logging_config import get_logger

PdfaLevel = Literal["1", "2", "3"]

logger = get_logger(__name__)

app = FastAPI(
    title="PDF/A Conversion Service",
    description="Convert PDFs to PDF/A using OCRmyPDF.",
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse)
async def web_ui() -> str:
    """Serve the web-based conversion interface."""
    ui_path = Path(__file__).parent / "web_ui.html"
    try:
        return ui_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Web UI file not found at %s", ui_path)
        return """
        <html>
        <head>
            <title>PDF/A Converter</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; }
                h1 { color: #333; }
                .error { color: #d32f2f; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📄 PDF/A Converter API</h1>
                <p>Web interface is not available. Use the API directly:</p>
                <p><strong>Endpoint:</strong> <code>POST /convert</code></p>
                <p><strong>API Documentation:</strong> <a href="/docs">/docs</a></p>
                <p>For detailed usage instructions, see the <a href="https://github.com/kutsenko/pdfa-service">GitHub repository</a>.</p>
            </div>
        </body>
        </html>
        """


@app.post(
    "/convert",
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"description": "Invalid input file"},
        500: {"description": "Conversion failed"},
    },
)
async def convert_endpoint(
    file: UploadFile = File(...),
    language: str = Form("deu+eng"),
    pdfa_level: PdfaLevel = Form("2"),
    ocr_enabled: bool = Form(True),
) -> Response:
    """Convert the uploaded PDF, Office, or ODF document into PDF/A.

    Supports PDF, DOCX, PPTX, XLSX (MS Office), and ODT, ODS, ODP (OpenDocument)
    files. Office and ODF documents are automatically converted to PDF before
    PDF/A conversion.

    Args:
        file: PDF, Office, or ODF file to convert.
        language: Tesseract language codes for OCR (default: 'deu+eng').
        pdfa_level: PDF/A compliance level (default: '2').
        ocr_enabled: Whether to perform OCR (default: True).

    """
    logger.info(
        f"Conversion request received: filename={file.filename}, "
        f"language={language}, pdfa_level={pdfa_level}, ocr_enabled={ocr_enabled}"
    )

    # Supported MIME types
    supported_types = {
        "application/pdf",
        "application/octet-stream",
        # Office document MIME types (MS Office)
        (
            "application/vnd.openxmlformats-officedocument." "wordprocessingml.document"
        ),  # docx
        (
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),  # pptx
        (
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        ),  # xlsx
        # Open Document Format (ODF) MIME types
        "application/vnd.oasis.opendocument.text",  # odt
        "application/vnd.oasis.opendocument.spreadsheet",  # ods
        "application/vnd.oasis.opendocument.presentation",  # odp
    }

    if file.content_type not in supported_types:
        logger.warning(
            f"Invalid file type rejected: {file.content_type} "
            f"(filename: {file.filename})"
        )
        raise HTTPException(
            status_code=400,
            detail="Supported formats: PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP",
        )

    contents = await file.read()
    if not contents:
        logger.warning(f"Empty file rejected: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.debug(f"Processing file: {file.filename} (size: {len(contents)} bytes)")

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Determine if file is Office document
        is_office = is_office_document(file.filename or "")

        # Use random filename for security (don't expose user filenames in temp storage)
        # Extract original file extension
        original_ext = Path(file.filename or "").suffix.lower() if file.filename else ""
        if not original_ext:
            original_ext = ".docx" if is_office else ".pdf"

        # Generate random temporary filename while preserving extension
        random_filename = f"{uuid.uuid4().hex}{original_ext}"
        input_path = tmp_path / random_filename

        logger.debug(f"Storing uploaded file with random name: {random_filename}")
        input_path.write_bytes(contents)

        try:
            # Convert Office documents to PDF first if needed
            pdf_path = input_path
            if is_office:
                logger.info(
                    f"Office document detected, converting to PDF: {file.filename}"
                )
                pdf_path = tmp_path / "converted.pdf"
                convert_office_to_pdf(input_path, pdf_path)

            # Convert to PDF/A
            output_path = tmp_path / "output.pdf"
            convert_to_pdfa(
                pdf_path,
                output_path,
                language=language,
                pdfa_level=pdfa_level,
                ocr_enabled=ocr_enabled,
            )

        except FileNotFoundError as error:
            logger.error(f"File not found during conversion: {error}")
            raise HTTPException(status_code=400, detail=str(error)) from error
        except UnsupportedFormatError as error:
            logger.error(f"Unsupported file format: {error}")
            raise HTTPException(status_code=400, detail=str(error)) from error
        except OfficeConversionError as error:
            logger.error(f"Office conversion failed: {error}")
            raise HTTPException(status_code=500, detail=str(error)) from error
        except ocrmypdf_exceptions.ExitCodeException as error:
            logger.error(f"OCRmyPDF conversion failed: {error}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"OCRmyPDF failed: {error}"
            ) from error
        except Exception as error:
            logger.exception(f"Unexpected error during conversion: {error}")
            raise HTTPException(
                status_code=500, detail=f"Conversion failed: {error}"
            ) from error

        output_bytes = output_path.read_bytes()

    filename = file.filename or "converted.pdf"
    if not filename.endswith(".pdf"):
        filename = f"{Path(filename).stem}.pdf"

    logger.info(
        f"Conversion successful: {file.filename} -> {filename} "
        f"(output size: {len(output_bytes)} bytes)"
    )

    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(content=output_bytes, headers=headers, media_type="application/pdf")
