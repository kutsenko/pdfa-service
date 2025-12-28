"""In-memory job management for conversion tasks."""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

from fastapi import WebSocket

from pdfa.event_logger import log_job_cleanup_event, log_job_timeout_event
from pdfa.exceptions import JobNotFoundException
from pdfa.models import AuditLogDocument, JobDocument
from pdfa.progress_tracker import ProgressInfo
from pdfa.repositories import AuditLogRepository, JobRepository

logger = logging.getLogger(__name__)


JobStatus = Literal["queued", "processing", "completed", "failed", "cancelled"]


@dataclass
class Job:
    """A conversion job.

    Supports both single-file and multi-file modes for multi-page documents.

    Attributes:
        job_id: Unique identifier for the job
        status: Current job status
        filename: Original filename (single-file) or combined name (multi-file)
        input_path: Path to input file (single-file mode)
        input_paths: List of input file paths (multi-file mode)
        output_path: Path to output file (when completed)
        config: Conversion configuration
        user_id: User who created the job (None if auth disabled)
        created_at: Job creation timestamp
        started_at: Processing start timestamp
        completed_at: Completion timestamp
        error: Error message (if failed)
        progress: Current progress information
        cancel_event: Event to signal cancellation
        temp_dir: Temporary directory for job files
        websockets: Set of WebSocket connections for this job

    """

    job_id: str
    status: JobStatus
    filename: str
    input_path: Path
    config: dict[str, Any]
    input_paths: list[Path] | None = None  # Multi-file mode
    user_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output_path: Path | None = None
    error: str | None = None
    progress: ProgressInfo | None = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    temp_dir: TemporaryDirectory | None = None
    websockets: set[WebSocket] = field(default_factory=set)


@dataclass
class JobConfig:
    """Configuration for job management.

    Attributes:
        max_concurrent_jobs: Maximum number of concurrent conversion jobs
        job_timeout_seconds: Maximum time for a job to run
        completed_job_ttl_seconds: Time to keep completed jobs before cleanup
        ws_ping_interval: WebSocket ping interval in seconds
        ws_max_connections: Maximum number of WebSocket connections
        temp_dir: Base directory for temporary files

    """

    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 7200  # 2 hours
    completed_job_ttl_seconds: int = 3600  # 1 hour
    ws_ping_interval: int = 30
    ws_max_connections: int = 100
    temp_dir: Path = Path("/tmp/pdfa-jobs")

    @classmethod
    def from_env(cls) -> JobConfig:
        """Load configuration from environment variables.

        Returns:
            JobConfig instance with values from environment or defaults

        """
        return cls(
            max_concurrent_jobs=int(os.getenv("PDFA_MAX_CONCURRENT_JOBS", "5")),
            job_timeout_seconds=int(os.getenv("PDFA_JOB_TIMEOUT_SECONDS", "7200")),
            completed_job_ttl_seconds=int(
                os.getenv("PDFA_COMPLETED_JOB_TTL_SECONDS", "3600")
            ),
            ws_ping_interval=int(os.getenv("PDFA_WS_PING_INTERVAL", "30")),
            ws_max_connections=int(os.getenv("PDFA_WS_MAX_CONNECTIONS", "100")),
            temp_dir=Path(os.getenv("PDFA_TEMP_DIR", "/tmp/pdfa-jobs")),
        )


class JobManager:
    """Manager for conversion jobs.

    This class manages the lifecycle of conversion jobs, including creation,
    tracking, cancellation, and cleanup. It also manages WebSocket connections
    and background tasks.

    """

    def __init__(self, config: JobConfig | None = None):
        """Initialize the job manager.

        Args:
            config: Job configuration (uses defaults if None)

        """
        self.config = config or JobConfig.from_env()
        self.jobs: dict[str, Job] = {}
        self.processing_semaphore = asyncio.Semaphore(self.config.max_concurrent_jobs)
        self.lock = asyncio.Lock()

        # MongoDB repositories for job persistence
        self.job_repo = JobRepository()
        self.audit_repo = AuditLogRepository()

        # Ensure temp directory exists
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)

        # Background task handles
        self.cleanup_task: asyncio.Task | None = None
        self.timeout_task: asyncio.Task | None = None
        self.keepalive_task: asyncio.Task | None = None

    def create_job(
        self,
        filename: str,
        file_data: bytes,
        config: dict[str, Any],
        user_id: str | None = None,
        filenames: list[str] | None = None,
        files_data: list[bytes] | None = None,
    ) -> Job:
        """Create a new conversion job.

        Supports both single-file and multi-file modes.

        Args:
            filename: Original filename (single-file mode)
            file_data: File content as bytes (single-file mode)
            config: Conversion configuration
            user_id: User identifier (None if auth disabled)
            filenames: List of filenames (multi-file mode)
            files_data: List of file contents (multi-file mode)

        Returns:
            The created job

        """
        job_id = str(uuid.uuid4())

        # Create temporary directory for this job
        temp_dir = TemporaryDirectory(
            prefix=f"pdfa_job_{job_id}_", dir=self.config.temp_dir
        )

        # Multi-file mode
        if filenames and files_data:
            # Save all input files
            input_paths = []
            total_size = 0
            for fname, fdata in zip(filenames, files_data):
                input_path = Path(temp_dir.name) / fname
                input_path.write_bytes(fdata)
                input_paths.append(input_path)
                total_size += len(fdata)

            # Use first filename as primary, store all paths
            job = Job(
                job_id=job_id,
                status="queued",
                filename=f"{len(filenames)}_pages.pdf",  # Combined name
                input_path=input_paths[0],  # First file as primary
                input_paths=input_paths,  # All files
                config=config,
                user_id=user_id,
                temp_dir=temp_dir,
            )

            # Persist with combined filename
            file_size = total_size
            persist_filename = f"{len(filenames)}_pages.pdf"
        else:
            # Single-file mode (backward compatibility)
            # Save input file
            input_path = Path(temp_dir.name) / filename
            input_path.write_bytes(file_data)

            # Create job
            job = Job(
                job_id=job_id,
                status="queued",
                filename=filename,
                input_path=input_path,
                config=config,
                user_id=user_id,
                temp_dir=temp_dir,
            )

            file_size = len(file_data)
            persist_filename = filename

        # Store job in-memory
        self.jobs[job_id] = job

        # Persist to MongoDB (async, non-blocking)
        # Only persist if there's a running event loop (skip in synchronous tests)
        try:
            asyncio.create_task(
                self._persist_job_creation(
                    job_id, persist_filename, config, user_id, file_size
                )
            )
        except RuntimeError:
            # No event loop running (e.g., in synchronous tests)
            pass

        log_msg = f"Created job {job_id} for file {filename}"
        if user_id:
            log_msg += f" (user: {user_id})"
        logger.info(log_msg)
        return job

    async def _persist_job_creation(
        self,
        job_id: str,
        filename: str,
        config: dict[str, Any],
        user_id: str | None,
        file_size: int,
    ) -> None:
        """Persist job creation to MongoDB.

        This is called asynchronously to avoid blocking job creation.

        Args:
            job_id: Job identifier
            filename: Original filename
            config: Conversion configuration
            user_id: User identifier (None if auth disabled)
            file_size: Input file size in bytes

        """
        try:
            # Create job document for MongoDB
            job_doc = JobDocument(
                job_id=job_id,
                user_id=user_id,
                status="queued",
                filename=filename,
                config=config,
                created_at=datetime.now(),
                file_size_input=file_size,
            )
            await self.job_repo.create_job(job_doc)

            # Log job creation event
            await self.audit_repo.log_event(
                AuditLogDocument(
                    event_type="job_created",
                    user_id=user_id,
                    timestamp=datetime.now(),
                    ip_address="internal",  # No request context here
                    details={
                        "job_id": job_id,
                        "filename": filename,
                        "file_size": file_size,
                    },
                )
            )
        except Exception as e:
            logger.error(f"Failed to persist job creation to MongoDB: {e}")

    def get_job(self, job_id: str) -> Job:
        """Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            The job

        Raises:
            JobNotFoundException: If job not found

        """
        if job_id not in self.jobs:
            raise JobNotFoundException(f"Job not found: {job_id}")
        return self.jobs[job_id]

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: str | None = None,
        output_path: Path | None = None,
    ) -> None:
        """Update job status.

        Args:
            job_id: Job identifier
            status: New status
            error: Error message (if failed)
            output_path: Output file path (if completed)

        """
        async with self.lock:
            job = self.get_job(job_id)
            job.status = status

            if status == "processing" and job.started_at is None:
                job.started_at = datetime.now()
            elif status in ("completed", "failed", "cancelled"):
                job.completed_at = datetime.now()

            if error:
                job.error = error
            if output_path:
                job.output_path = output_path

            logger.info(f"Job {job_id} status updated to {status}")

        # Persist to MongoDB (outside lock to avoid blocking)
        await self._persist_job_update(job_id, status, error, output_path)

    async def _persist_job_update(
        self,
        job_id: str,
        status: JobStatus,
        error: str | None,
        output_path: Path | None,
    ) -> None:
        """Persist job status update to MongoDB.

        Args:
            job_id: Job identifier
            status: New status
            error: Error message (if failed)
            output_path: Output file path (if completed)

        """
        try:
            # Get job from in-memory storage for additional data
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not in memory, skipping MongoDB update")
                return

            # Build update fields
            update_fields: dict[str, Any] = {}

            if status == "processing" and job.started_at:
                update_fields["started_at"] = job.started_at

            if status in ("completed", "failed", "cancelled") and job.completed_at:
                update_fields["completed_at"] = job.completed_at

                # Calculate duration
                if job.started_at:
                    duration = (job.completed_at - job.started_at).total_seconds()
                    update_fields["duration_seconds"] = duration

                # Add output file size if completed successfully
                if status == "completed" and output_path and output_path.exists():
                    update_fields["file_size_output"] = output_path.stat().st_size

                    # Calculate compression ratio if we have both sizes
                    if (
                        "file_size_output" in update_fields
                        and job.input_path
                        and job.input_path.exists()
                    ):
                        input_size = job.input_path.stat().st_size
                        if input_size > 0:
                            compression_ratio = (
                                update_fields["file_size_output"] / input_size
                            )
                            update_fields["compression_ratio"] = compression_ratio

            if error:
                update_fields["error"] = error

            # Update job in MongoDB
            await self.job_repo.update_job_status(job_id, status, **update_fields)

            # Log audit event for terminal states
            if status in ("completed", "failed", "cancelled"):
                event_type = f"job_{status}"
                await self.audit_repo.log_event(
                    AuditLogDocument(
                        event_type=event_type,  # type: ignore
                        user_id=job.user_id,
                        timestamp=datetime.now(),
                        ip_address="internal",
                        details={
                            "job_id": job_id,
                            "filename": job.filename,
                            "status": status,
                            "duration_seconds": update_fields.get("duration_seconds"),
                            "error": error,
                        },
                    )
                )

        except Exception as e:
            logger.error(f"Failed to persist job update to MongoDB: {e}")

    async def update_job_progress(self, job_id: str, progress: ProgressInfo) -> None:
        """Update job progress.

        Args:
            job_id: Job identifier
            progress: Progress information

        """
        async with self.lock:
            job = self.get_job(job_id)
            job.progress = progress

    async def cancel_job(self, job_id: str) -> None:
        """Cancel a job.

        Args:
            job_id: Job identifier

        """
        job = self.get_job(job_id)

        if job.status in ("completed", "failed", "cancelled"):
            logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
            return

        logger.info(f"Cancelling job {job_id}")
        job.cancel_event.set()
        await self.update_job_status(job_id, "cancelled")

    async def delete_job(self, job_id: str) -> None:
        """Delete a job and clean up its resources.

        Args:
            job_id: Job identifier

        """
        async with self.lock:
            if job_id not in self.jobs:
                return

            job = self.jobs[job_id]

            # Close all WebSocket connections
            for ws in list(job.websockets):
                try:
                    await ws.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket for job {job_id}: {e}")

            # Clean up temporary directory
            if job.temp_dir:
                try:
                    job.temp_dir.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up temp dir for job {job_id}: {e}")

            # Remove from registry
            del self.jobs[job_id]
            logger.info(f"Deleted job {job_id}")

    def register_websocket(self, job_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection for a job.

        Args:
            job_id: Job identifier
            websocket: WebSocket connection

        """
        job = self.get_job(job_id)
        job.websockets.add(websocket)
        logger.debug(
            f"Registered WebSocket for job {job_id} " f"(total: {len(job.websockets)})"
        )

    def unregister_websocket(self, job_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection from a job.

        Args:
            job_id: Job identifier
            websocket: WebSocket connection

        """
        try:
            job = self.get_job(job_id)
            job.websockets.discard(websocket)
            logger.debug(
                f"Unregistered WebSocket for job {job_id} "
                f"(remaining: {len(job.websockets)})"
            )
        except JobNotFoundException:
            pass  # Job may have been deleted

    async def broadcast_to_job(self, job_id: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all WebSockets for a job.

        Args:
            job_id: Job identifier
            message: Message to send

        """
        try:
            job = self.get_job(job_id)
            message_type = message.get("type", "unknown")

            logger.info(
                f"Broadcasting message type '{message_type}' to job {job_id} "
                f"({len(job.websockets)} connections)"
            )

            # Track successful sends
            success_count = 0
            failed_connections = []

            for ws in list(job.websockets):
                try:
                    await ws.send_json(message)
                    success_count += 1
                except Exception as e:
                    logger.error(
                        f"Error sending to WebSocket for job {job_id}: {e}",
                        exc_info=True,
                    )
                    failed_connections.append(ws)

            # Remove failed connections
            for ws in failed_connections:
                job.websockets.discard(ws)

            logger.info(
                f"Broadcast complete for job {job_id}: {success_count} successful, "
                f"{len(failed_connections)} failed"
            )

            # For critical completion/error messages, add a small delay to ensure
            # the message is fully transmitted before any cleanup happens
            if message_type in ("completed", "error", "cancelled"):
                await asyncio.sleep(0.1)
                logger.debug(f"Completion message delay complete for job {job_id}")

        except JobNotFoundException:
            logger.warning(f"Attempted broadcast to non-existent job {job_id}")
            pass  # Job may have been deleted

    def get_active_jobs(self) -> list[Job]:
        """Get all active (processing) jobs.

        Returns:
            List of active jobs

        """
        return [job for job in self.jobs.values() if job.status == "processing"]

    def get_queued_jobs(self) -> list[Job]:
        """Get all queued jobs.

        Returns:
            List of queued jobs

        """
        return [job for job in self.jobs.values() if job.status == "queued"]

    async def cleanup_old_jobs(self) -> None:
        """Clean up old completed/failed jobs."""
        now = datetime.now()
        ttl_seconds = self.config.completed_job_ttl_seconds

        to_delete = []
        for job_id, job in self.jobs.items():
            if job.status in ("completed", "failed", "cancelled"):
                if job.completed_at:
                    age = (now - job.completed_at).total_seconds()
                    if age > ttl_seconds:
                        to_delete.append((job_id, job, age))

        for job_id, job, age in to_delete:
            logger.info(f"Cleaning up old job {job_id} (age > {ttl_seconds}s)")

            # Collect file information before deletion
            files_deleted = {}
            total_size = 0

            try:
                if job.input_path and job.input_path.exists():
                    files_deleted["input_file"] = str(job.input_path)
                    total_size += job.input_path.stat().st_size

                if job.output_path and job.output_path.exists():
                    files_deleted["output_file"] = str(job.output_path)
                    total_size += job.output_path.stat().st_size

                if job.temp_dir and job.temp_dir.name:
                    temp_path = Path(job.temp_dir.name)
                    if temp_path.exists():
                        files_deleted["temp_directory"] = str(temp_path)
                        # Calculate temp dir size
                        for path in temp_path.rglob("*"):
                            if path.is_file():
                                total_size += path.stat().st_size
            except Exception as e:
                logger.warning(f"Error collecting file info for cleanup event: {e}")

            # Log cleanup event
            try:
                await log_job_cleanup_event(
                    job_id=job_id,
                    trigger="age_exceeded",
                    ttl_seconds=ttl_seconds,
                    age_seconds=age,
                    files_deleted=files_deleted if files_deleted else None,
                    total_size_bytes=total_size if total_size > 0 else None,
                )
            except Exception as e:
                logger.error(
                    f"Failed to log cleanup event for job {job_id}: {e}",
                    exc_info=True,
                )

            # Delete the job
            await self.delete_job(job_id)

    async def check_timeouts(self) -> None:
        """Check for timed-out jobs and cancel them."""
        now = datetime.now()
        timeout_seconds = self.config.job_timeout_seconds

        for job in self.get_active_jobs():
            if job.started_at:
                runtime = (now - job.started_at).total_seconds()
                if runtime > timeout_seconds:
                    logger.warning(f"Job {job.job_id} timed out after {runtime:.1f}s")

                    # Log timeout event
                    try:
                        await log_job_timeout_event(
                            job_id=job.job_id,
                            timeout_seconds=timeout_seconds,
                            runtime_seconds=runtime,
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to log timeout event for job {job.job_id}: {e}",
                            exc_info=True,
                        )

                    await self.cancel_job(job.job_id)
                    await self.update_job_status(
                        job.job_id,
                        "failed",
                        error=f"Job timeout after {timeout_seconds}s",
                    )

    async def cleanup_loop(self) -> None:
        """Background task to periodically clean up old jobs."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def timeout_monitor(self) -> None:
        """Background task to monitor job timeouts."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.check_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}", exc_info=True)

    async def websocket_keepalive(self) -> None:
        """Background task to send keep-alive pings to WebSocket connections.

        This helps maintain connections during long-running conversions by
        sending periodic ping messages to all active jobs.
        """
        while True:
            try:
                await asyncio.sleep(self.config.ws_ping_interval)

                # Send keep-alive to all processing jobs
                for job in self.get_active_jobs():
                    if len(job.websockets) > 0:
                        ping_message = {"type": "ping", "timestamp": time.time()}
                        try:
                            await self.broadcast_to_job(job.job_id, ping_message)
                            logger.debug(
                                f"Sent keep-alive ping to job {job.job_id} "
                                f"({len(job.websockets)} connections)"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error sending keep-alive to job {job.job_id}: {e}"
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket keep-alive: {e}", exc_info=True)

    def start_background_tasks(self) -> None:
        """Start background cleanup and monitoring tasks."""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self.cleanup_loop())
            logger.info("Started cleanup background task")

        if self.timeout_task is None or self.timeout_task.done():
            self.timeout_task = asyncio.create_task(self.timeout_monitor())
            logger.info("Started timeout monitor background task")

        if self.keepalive_task is None or self.keepalive_task.done():
            self.keepalive_task = asyncio.create_task(self.websocket_keepalive())
            logger.info("Started WebSocket keep-alive background task")

    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        if self.timeout_task:
            self.timeout_task.cancel()
            try:
                await self.timeout_task
            except asyncio.CancelledError:
                pass

        if self.keepalive_task:
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped background tasks")


# Global singleton instance
_job_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance.

    Returns:
        The global JobManager instance

    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
