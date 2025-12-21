"""REST API providing PDF to PDF/A conversion backed by OCRmyPDF."""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse, HTMLResponse, Response
from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa.compression_config import PRESETS, CompressionConfig
from pdfa.converter import convert_to_pdfa
from pdfa.exceptions import (
    JobCancelledException,
    JobNotFoundException,
    OfficeConversionError,
    UnsupportedFormatError,
)
from pdfa.format_converter import (
    convert_office_to_pdf,
    is_image_file,
    is_office_document,
)
from pdfa.image_converter import convert_image_to_pdf
from pdfa.job_manager import get_job_manager
from pdfa.logging_config import configure_logging, get_logger
from pdfa.progress_tracker import ProgressInfo
from pdfa.websocket_protocol import (
    CancelJobMessage,
    CancelledMessage,
    CompletedMessage,
    ErrorMessage,
    JobAcceptedMessage,
    PongMessage,
    ProgressMessage,
    SubmitJobMessage,
    parse_client_message,
)

PdfaLevel = Literal["pdf", "1", "2", "3"]
CompressionProfile = Literal["balanced", "quality", "aggressive", "minimal"]

logger = get_logger(__name__)

# Load compression configuration from environment variables at startup
compression_config = CompressionConfig.from_env()
logger.info(
    f"Loaded compression config: DPI={compression_config.image_dpi}, "
    f"JPG quality={compression_config.jpg_quality}, "
    f"Optimize={compression_config.optimize}"
)

# Progress broadcast timeout configuration
# For long-running conversions with many WebSocket clients, broadcasting progress
# updates can take longer than the default 2 seconds. Increase this if you have
# many concurrent clients or slow network conditions.
PROGRESS_BROADCAST_TIMEOUT = int(os.getenv("PROGRESS_BROADCAST_TIMEOUT", "10"))
logger.info(f"Progress broadcast timeout: {PROGRESS_BROADCAST_TIMEOUT} seconds")

app = FastAPI(
    title="PDF/A Conversion Service",
    description="Convert PDFs to PDF/A using OCRmyPDF.",
    version="0.1.0",
)

# Initialize job manager
job_manager = get_job_manager()


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    # Configure logging for all modules
    configure_logging()
    logger.info("Logging configured")
    logger.info("Starting background tasks...")
    job_manager.start_background_tasks()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on application shutdown."""
    logger.info("Stopping background tasks...")
    await job_manager.stop_background_tasks()


@app.get("/", response_class=HTMLResponse)
async def web_ui() -> str:
    """Serve the web-based conversion interface with browser language detection."""
    ui_path = Path(__file__).parent / "web_ui.html"
    try:
        html_content = ui_path.read_text(encoding="utf-8")
        # For root path, inject auto-detection flag
        html_content = html_content.replace(
            '<html lang="en" data-lang="en">', '<html lang="en" data-lang="auto">'
        )
        return html_content
    except FileNotFoundError:
        logger.warning("Web UI file not found at %s", ui_path)
        return await web_ui_lang("en")


@app.get("/{lang}", response_class=HTMLResponse)
async def web_ui_lang(lang: str) -> str:
    """Serve the web-based conversion interface in specified language.

    Args:
        lang: Language code (en, de, es, fr)

    """
    # Validate language code
    supported_langs = {"en", "de", "es", "fr"}
    if lang not in supported_langs:
        # For unsupported paths, let FastAPI handle it (will show 404 or other routes)
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    ui_path = Path(__file__).parent / "web_ui.html"
    try:
        html_content = ui_path.read_text(encoding="utf-8")
        # Inject the language code into the HTML
        html_content = html_content.replace(
            '<html lang="en" data-lang="en">',
            f'<html lang="{lang}" data-lang="{lang}">',
        )
        return html_content
    except FileNotFoundError:
        logger.warning("Web UI file not found at %s", ui_path)
        # Fallback HTML UI (line length exceptions acceptable for HTML/CSS)
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
    compression_profile: CompressionProfile = Form("balanced"),
    ocr_enabled: bool = Form(True),
    skip_ocr_on_tagged_pdfs: bool = Form(True),
) -> Response:
    """Convert the uploaded PDF, Office, ODF, or image file into PDF/A or plain PDF.

    Supports PDF, DOCX, PPTX, XLSX (MS Office), ODT, ODS, ODP (OpenDocument),
    and image files (JPG, PNG, TIFF, BMP, GIF). Office, ODF, and image files
    are automatically converted to PDF before PDF/A conversion.

    Args:
        file: PDF, Office, ODF, or image file to convert.
        language: Tesseract language codes for OCR (default: 'deu+eng').
        pdfa_level: PDF/A compliance level ('1', '2', '3') or 'pdf' for plain PDF
                   (default: '2'). When 'pdf' is selected with Office documents,
                   OCRmyPDF is skipped to preserve accessibility.
        compression_profile: Compression profile to use (default: 'balanced').
        ocr_enabled: Whether to perform OCR (default: True).
        skip_ocr_on_tagged_pdfs: Skip OCR for tagged PDFs (default: True).

    """
    logger.info(
        f"Conversion request received: filename={file.filename}, "
        f"language={language}, pdfa_level={pdfa_level}, "
        f"compression_profile={compression_profile}, ocr_enabled={ocr_enabled}, "
        f"skip_ocr_on_tagged_pdfs={skip_ocr_on_tagged_pdfs}"
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
        # Image MIME types
        "image/jpeg",  # jpg, jpeg
        "image/png",  # png
        "image/tiff",  # tiff, tif
        "image/bmp",  # bmp
        "image/gif",  # gif
    }

    if file.content_type not in supported_types:
        logger.warning(
            f"Invalid file type rejected: {file.content_type} "
            f"(filename: {file.filename})"
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Supported formats: PDF, DOCX, PPTX, XLSX, "
                "ODT, ODS, ODP, JPG, PNG, TIFF, BMP, GIF"
            ),
        )

    contents = await file.read()
    if not contents:
        logger.warning(f"Empty file rejected: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.debug(f"Processing file: {file.filename} (size: {len(contents)} bytes)")

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Determine file type
        is_office = is_office_document(file.filename or "")
        is_image = is_image_file(file.filename or "")

        # Use random filename for security (don't expose user filenames in temp storage)
        # Extract original file extension
        original_ext = Path(file.filename or "").suffix.lower() if file.filename else ""
        if not original_ext:
            if is_office:
                original_ext = ".docx"
            elif is_image:
                original_ext = ".jpg"
            else:
                original_ext = ".pdf"

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
                # Run blocking operation in thread pool to avoid blocking event loop
                await asyncio.to_thread(convert_office_to_pdf, input_path, pdf_path)
            elif is_image:
                logger.info(f"Image file detected, converting to PDF: {file.filename}")
                pdf_path = tmp_path / "converted.pdf"
                # Run blocking operation in thread pool to avoid blocking event loop
                await asyncio.to_thread(convert_image_to_pdf, input_path, pdf_path)

            # Convert to PDF/A or plain PDF
            output_path = tmp_path / "output.pdf"
            # Select compression configuration from profile
            selected_compression = PRESETS.get(compression_profile, compression_config)
            # Run blocking OCRmyPDF operation in thread pool to allow parallel requests
            await asyncio.to_thread(
                convert_to_pdfa,
                pdf_path,
                output_path,
                language=language,
                pdfa_level=pdfa_level,
                ocr_enabled=ocr_enabled,
                skip_ocr_on_tagged_pdfs=skip_ocr_on_tagged_pdfs,
                compression_config=selected_compression,
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

    # Use RFC 5987 encoding for filenames with Unicode characters
    # This ensures compatibility with all characters including umlauts, accents, etc.
    filename_encoded = quote(filename)

    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}",
    }

    return Response(content=output_bytes, headers=headers, media_type="application/pdf")


# ============================================================================
# WebSocket-based Progress Tracking Endpoints
# ============================================================================


async def process_conversion_job(job_id: str) -> None:
    """Process a conversion job asynchronously.

    Args:
        job_id: The job ID to process

    """
    try:
        # Get job - if this fails, job doesn't exist and we can't update status
        try:
            job = job_manager.get_job(job_id)
        except JobNotFoundException as e:
            logger.error(f"Job {job_id} not found in process_conversion_job: {e}")
            # Can't update status or broadcast since job doesn't exist
            return

        # Update status to processing - catch any errors here too
        try:
            await job_manager.update_job_status(job_id, "processing")
        except Exception as e:
            logger.error(
                f"Failed to update job {job_id} status to processing: {e}",
                exc_info=True,
            )
            # Try to set to failed state
            try:
                await job_manager.update_job_status(
                    job_id, "failed", error=f"Failed to start job: {e}"
                )
            except Exception:
                pass  # Nothing more we can do
            return

        # Send initial progress message to inform client that processing has started
        initial_progress = ProgressMessage(
            job_id=job_id,
            step="Starting conversion",
            current=0,
            total=100,
            percentage=0,
            message="Preparing document for conversion...",
        )
        try:
            await job_manager.broadcast_to_job(job_id, initial_progress.to_dict())
        except Exception as broadcast_error:
            logger.warning(
                f"Failed to broadcast initial progress for job {job_id}: {broadcast_error}"
            )
            # Continue anyway - this is not critical

        # Get the current event loop BEFORE entering the thread
        # This is critical because asyncio.get_event_loop() doesn't work reliably
        # from within a thread created by asyncio.to_thread()
        event_loop = asyncio.get_running_loop()

        # Progress callback that broadcasts to WebSocket
        def progress_callback(progress: ProgressInfo) -> None:
            # Log that we received a progress update
            logger.info(
                f"Progress callback called for job {job_id}: "
                f"{progress.step} - {progress.percentage}% "
                f"({progress.current}/{progress.total})"
            )

            # Send progress update to all connected clients
            message = ProgressMessage(
                job_id=job_id,
                step=progress.step,
                current=progress.current,
                total=progress.total,
                percentage=progress.percentage,
                message=progress.message,
            )
            # Schedule broadcast from thread-safe context using the captured event loop
            try:
                future = asyncio.run_coroutine_threadsafe(
                    job_manager.broadcast_to_job(job_id, message.to_dict()), event_loop
                )
                # Wait for the broadcast to complete (with timeout)
                # Increased from 2s to 10s default to handle multiple concurrent clients
                future.result(timeout=PROGRESS_BROADCAST_TIMEOUT)
                logger.info(
                    f"Successfully broadcast progress for job {job_id}: {progress.percentage}%"
                )
            except TimeoutError:
                # Broadcasting took too long - log warning but don't fail conversion
                # This can happen with many concurrent WebSocket clients or slow networks
                logger.warning(
                    f"Progress broadcast timeout ({PROGRESS_BROADCAST_TIMEOUT}s) "
                    f"for job {job_id} at {progress.percentage}%. "
                    f"Some clients may have missed this update."
                )
            except Exception as e:
                # Log any other errors but don't fail the conversion
                logger.error(
                    f"Failed to broadcast progress for job {job_id}: {e}",
                    exc_info=True,
                )

        # Determine file type and convert
        config = job.config
        pdf_path = job.input_path

        # Convert office/image to PDF if needed
        if is_office_document(job.filename):
            logger.info(f"Converting Office document for job {job_id}")
            pdf_path = job.input_path.parent / f"{job.input_path.stem}.pdf"
            await asyncio.to_thread(
                convert_office_to_pdf,
                job.input_path,
                pdf_path,
                progress_callback=progress_callback,
            )
        elif is_image_file(job.filename):
            logger.info(f"Converting image to PDF for job {job_id}")
            pdf_path = job.input_path.parent / f"{job.input_path.stem}.pdf"
            await asyncio.to_thread(convert_image_to_pdf, job.input_path, pdf_path)

        # Convert to PDF/A
        output_path = job.input_path.parent / f"{job.input_path.stem}_pdfa.pdf"

        # Get compression config
        profile = config.get("compression_profile", "balanced")
        selected_compression = PRESETS.get(profile, PRESETS["balanced"])

        await asyncio.to_thread(
            convert_to_pdfa,
            pdf_path,
            output_path,
            language=config.get("language", "deu+eng"),
            pdfa_level=config.get("pdfa_level", "2"),
            ocr_enabled=config.get("ocr_enabled", True),
            skip_ocr_on_tagged_pdfs=config.get("skip_ocr_on_tagged_pdfs", True),
            compression_config=selected_compression,
            progress_callback=progress_callback,
            cancel_event=job.cancel_event,
        )

        # Job completed successfully
        await job_manager.update_job_status(
            job_id, "completed", output_path=output_path
        )

        # Get file size
        file_size = output_path.stat().st_size

        # Send completion message
        message = CompletedMessage(
            job_id=job_id,
            download_url=f"/download/{job_id}",
            filename=f"{job.filename.rsplit('.', 1)[0]}_pdfa.pdf",
            size_bytes=file_size,
        )
        await job_manager.broadcast_to_job(job_id, message.to_dict())

    except JobCancelledException:
        logger.info(f"Job {job_id} was cancelled")
        await job_manager.update_job_status(job_id, "cancelled")
        message = CancelledMessage(job_id=job_id)
        await job_manager.broadcast_to_job(job_id, message.to_dict())

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)

        # Try to update status and broadcast error - wrap in try/except to ensure
        # we always try to notify the client even if status update fails
        try:
            await job_manager.update_job_status(job_id, "failed", error=str(e))
        except Exception as update_error:
            logger.error(
                f"Failed to update status for job {job_id}: {update_error}",
                exc_info=True,
            )

        # Send error message to client - always try this even if status update failed
        try:
            error_code = "CONVERSION_FAILED"
            if isinstance(e, OfficeConversionError):
                error_code = "OFFICE_CONVERSION_FAILED"
            elif isinstance(e, ocrmypdf_exceptions.PriorOcrFoundError):
                error_code = "OCR_ALREADY_EXISTS"

            message = ErrorMessage(
                job_id=job_id,
                error_code=error_code,
                message=str(e),
            )
            await job_manager.broadcast_to_job(job_id, message.to_dict())
        except Exception as broadcast_error:
            logger.error(
                f"Failed to broadcast error message for job {job_id}: {broadcast_error}",
                exc_info=True,
            )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time conversion progress.

    Protocol:
        Client sends: SubmitJobMessage, CancelJobMessage, PingMessage
        Server sends: JobAcceptedMessage, ProgressMessage, CompletedMessage,
                     ErrorMessage, CancelledMessage, PongMessage

    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    current_job_id: str | None = None

    try:
        async for message_data in websocket.iter_json():
            try:
                # Parse incoming message
                message = parse_client_message(message_data)

                if isinstance(message, SubmitJobMessage):
                    # Create new job
                    file_data = message.get_file_bytes()
                    job = job_manager.create_job(
                        filename=message.filename,
                        file_data=file_data,
                        config=message.config or {},
                    )
                    current_job_id = job.job_id

                    # Register WebSocket for this job
                    job_manager.register_websocket(job.job_id, websocket)

                    # Send job accepted message
                    response = JobAcceptedMessage(
                        job_id=job.job_id,
                        status="queued",
                    )
                    await websocket.send_json(response.to_dict())

                    # Start processing job in background
                    asyncio.create_task(process_conversion_job(job.job_id))

                elif isinstance(message, CancelJobMessage):
                    # Cancel job
                    try:
                        await job_manager.cancel_job(message.job_id)
                        logger.info(f"Job {message.job_id} cancel requested")
                    except JobNotFoundException:
                        error_msg = ErrorMessage(
                            job_id=message.job_id,
                            error_code="JOB_NOT_FOUND",
                            message=f"Job {message.job_id} not found",
                        )
                        await websocket.send_json(error_msg.to_dict())

                else:  # PingMessage
                    response = PongMessage()
                    await websocket.send_json(response.to_dict())

            except ValueError as e:
                # Invalid message format
                logger.error(f"Invalid WebSocket message: {e}")
                error_msg = ErrorMessage(
                    error_code="INVALID_MESSAGE",
                    message=str(e),
                )
                await websocket.send_json(error_msg.to_dict())

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Unregister WebSocket
        if current_job_id:
            job_manager.unregister_websocket(current_job_id, websocket)
        logger.info("WebSocket connection closed")


@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the current status of a conversion job.

    This endpoint is useful for clients that have lost their WebSocket connection
    and want to poll for job status as a fallback mechanism.

    Args:
        job_id: The job ID

    Returns:
        Job status information including:
        - job_id: The job identifier
        - status: Current status (queued, running, completed, failed, cancelled)
        - progress: Current progress percentage (0-100)
        - message: Latest progress message
        - created_at: Job creation timestamp
        - download_url: Download URL (only if status is completed)
        - filename: Original filename
        - error: Error message (only if status is failed)

    Raises:
        HTTPException: If job not found (404)

    Example:
        GET /api/v1/jobs/abc123/status
        Response:
        {
            "job_id": "abc123",
            "status": "running",
            "progress": 45.5,
            "message": "Processing page 5 of 10",
            "created_at": "2024-12-12T10:30:00Z",
            "filename": "document.pdf"
        }

    """
    try:
        job = job_manager.get_job(job_id)
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build response with current job status
    response = {
        "job_id": job_id,
        "status": job.status,
        "progress": getattr(job, "progress_percentage", 0.0),
        "message": getattr(job, "progress_message", ""),
        "created_at": (
            job.created_at.isoformat() if hasattr(job, "created_at") else None
        ),
        "filename": job.filename,
    }

    # Add download URL if job is completed
    if job.status == "completed":
        response["download_url"] = f"/download/{job_id}"
        response["filename_output"] = f"{job.filename.rsplit('.', 1)[0]}_pdfa.pdf"

    # Add error message if job failed
    if job.status == "failed" and hasattr(job, "error_message"):
        response["error"] = job.error_message

    logger.debug(f"Status query for job {job_id}: {job.status}")

    return response


@app.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download the converted PDF for a completed job.

    Args:
        job_id: The job ID

    Returns:
        The converted PDF file

    Raises:
        HTTPException: If job not found or not completed

    """
    try:
        job = job_manager.get_job(job_id)
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job.status})",
        )

    # Check if output path exists
    if not job.output_path:
        logger.error(f"Job {job_id} has no output_path despite being completed")
        raise HTTPException(
            status_code=500,
            detail="Job completed but output file path is missing",
        )

    # Check file existence - handle race condition where file might be deleted
    # between status check and FileResponse
    if not job.output_path.exists():
        logger.error(
            f"Output file for job {job_id} not found at {job.output_path} "
            "(may have been cleaned up)"
        )
        raise HTTPException(
            status_code=404,
            detail="Output file not found (may have been cleaned up after TTL expired)",
        )

    filename = f"{job.filename.rsplit('.', 1)[0]}_pdfa.pdf"

    logger.info(f"Downloading result for job {job_id}: {filename}")

    # Use FileResponse which handles the file reading
    # Note: There's still a small race condition window between exists() check
    # and FileResponse reading the file, but FileResponse will handle
    # FileNotFoundError gracefully
    return FileResponse(
        path=job.output_path,
        media_type="application/pdf",
        filename=filename,
    )
