"""REST API providing PDF to PDF/A conversion backed by OCRmyPDF."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa.converter import convert_to_pdfa

PdfaLevel = Literal["1", "2", "3"]

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
) -> Response:
    """Convert the uploaded PDF into a PDF/A document and return the result."""
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / "input.pdf"
        output_path = Path(tmp_dir) / "output.pdf"

        input_path.write_bytes(contents)

        try:
            convert_to_pdfa(
                input_path,
                output_path,
                language=language,
                pdfa_level=pdfa_level,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except ocrmypdf_exceptions.ExitCodeException as error:
            raise HTTPException(
                status_code=500, detail=f"OCRmyPDF failed: {error}"
            ) from error

        output_bytes = output_path.read_bytes()

    filename = file.filename or "converted.pdf"
    if not filename.endswith(".pdf"):
        filename = f"{Path(filename).stem}.pdf"

    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(content=output_bytes, headers=headers, media_type="application/pdf")
