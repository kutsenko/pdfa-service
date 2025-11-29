"""REST API providing PDF to PDF/A conversion backed by OCRmyPDF."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
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
    """Convert the uploaded PDF or Office document into PDF/A.

    Supports PDF, DOCX, PPTX, and XLSX files. Office documents are
    automatically converted to PDF before PDF/A conversion.

    Args:
        file: PDF or Office file to convert.
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
        # Office document MIME types
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
    }

    if file.content_type not in supported_types:
        logger.warning(
            f"Invalid file type rejected: {file.content_type} "
            f"(filename: {file.filename})"
        )
        raise HTTPException(
            status_code=400,
            detail="Supported formats: PDF, DOCX, PPTX, XLSX",
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

        # Write uploaded file to temporary location
        if is_office:
            # Keep original filename for office documents (LibreOffice needs it)
            input_path = tmp_path / (file.filename or "document.docx")
        else:
            input_path = tmp_path / "input.pdf"

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
