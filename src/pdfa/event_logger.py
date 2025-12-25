"""Event logging helpers for job execution tracking.

This module provides high-level helper functions for logging job events to MongoDB.
Each function creates a JobEvent and persists it via JobRepository, providing a clean
interface for the conversion pipeline to record decision points and milestones.

All functions are async and designed to be called during job processing without blocking
the main conversion flow.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from pdfa.models import JobEvent
from pdfa.repositories import JobRepository

logger = logging.getLogger(__name__)


async def log_format_conversion_event(
    job_id: str,
    source_format: str,
    target_format: str,
    conversion_required: bool,
    converter: str | None = None,
    conversion_time_seconds: float | None = None,
) -> None:
    """Log format conversion event (Office/Image→PDF).

    Args:
        job_id: Job identifier
        source_format: Source file format (e.g., "docx", "jpg", "pdf")
        target_format: Target format (typically "pdf")
        conversion_required: Whether format conversion was needed
        converter: Converter used (e.g., "office_to_pdf", "image_to_pdf")
        conversion_time_seconds: Time taken for conversion

    Example:
        await log_format_conversion_event(
            job_id="uuid-123",
            source_format="docx",
            target_format="pdf",
            conversion_required=True,
            converter="office_to_pdf",
            conversion_time_seconds=3.2
        )

    """
    # Build message
    if conversion_required:
        message = f"Format conversion: {source_format.upper()}→{target_format.upper()}"
        if converter:
            message += f" using {converter}"
    else:
        message = f"No format conversion required (source is {source_format.upper()})"

    # Build details
    details: dict[str, Any] = {
        "source_format": source_format,
        "target_format": target_format,
        "conversion_required": conversion_required,
    }
    if converter:
        details["converter"] = converter
    if conversion_time_seconds is not None:
        details["conversion_time_seconds"] = conversion_time_seconds

    # Create and persist event
    event = JobEvent(
        event_type="format_conversion",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{source_format}.success"
                if conversion_required
                else f"{event.event_type}.none",
                "_i18n_params": {
                    "source_format": source_format,
                    "target_format": target_format,
                },
            },
        )

        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")


async def log_ocr_decision_event(
    job_id: str,
    decision: str,
    reason: str,
    **kwargs: Any,
) -> None:
    """Log OCR decision event.

    Args:
        job_id: Job identifier
        decision: "skip" or "perform"
        reason: Reason for decision (e.g., "tagged_pdf", "has_text", "no_text")
        **kwargs: Additional details (pages_with_text, total_pages_checked, text_ratio,
                 total_characters, has_struct_tree_root, etc.)

    Example:
        await log_ocr_decision_event(
            job_id="uuid-123",
            decision="skip",
            reason="tagged_pdf",
            has_struct_tree_root=True
        )

    """
    # Build message
    if decision == "skip":
        reason_text = {
            "tagged_pdf": "tagged PDF detected",
            "has_text": "existing text found",
        }.get(reason, reason)
        message = f"OCR skipped: {reason_text}"
    else:
        reason_text = {
            "no_text": "no text detected",
        }.get(reason, reason)
        message = f"OCR will be performed: {reason_text}"

    # Build details
    details: dict[str, Any] = {
        "decision": decision,
        "reason": reason,
        **kwargs,
    }

    # Create and persist event
    event = JobEvent(
        event_type="ocr_decision",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{decision}.{reason}",
                "_i18n_params": {"decision": decision, "reason": reason},
            },
        )

        # Best-effort async broadcast (non-blocking)
        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,  # Prevent blocking on slow connections
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")
        # Continue - MongoDB persistence is more important


async def log_compression_selected_event(
    job_id: str,
    profile: str,
    reason: str,
    original_profile: str | None = None,
    settings: dict[str, Any] | None = None,
) -> None:
    """Log compression profile selection event.

    Args:
        job_id: Job identifier
        profile: Selected compression profile (e.g., "quality", "balanced", "preserve")
        reason: Reason for selection (e.g., "user_selected",
                "auto_switched_for_tagged_pdf")
        original_profile: Original profile if auto-switched
        settings: Compression settings applied

    Example:
        await log_compression_selected_event(
            job_id="uuid-123",
            profile="preserve",
            reason="auto_switched_for_tagged_pdf",
            original_profile="balanced",
            settings={"image_dpi": 300, "remove_vectors": False}
        )

    """
    # Build message
    if reason == "auto_switched_for_tagged_pdf":
        message = (
            f"Compression profile auto-switched: {original_profile}→{profile} "
            f"(tagged PDF preservation)"
        )
    else:
        message = f"Compression profile selected: {profile}"

    # Build details
    details: dict[str, Any] = {
        "profile": profile,
        "reason": reason,
    }
    if original_profile:
        details["original_profile"] = original_profile
    if settings:
        details["settings"] = settings

    # Create and persist event
    event = JobEvent(
        event_type="compression_selected",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{profile}.{reason}",
                "_i18n_params": {"profile": profile, "reason": reason},
            },
        )

        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")


async def log_passthrough_mode_event(
    job_id: str,
    enabled: bool,
    reason: str,
    pdfa_level: str,
    ocr_enabled: bool,
    has_tags: bool,
    tags_preserved: bool,
) -> None:
    """Log pass-through mode activation event.

    Pass-through mode is activated when output is PDF (not PDF/A) and OCR is disabled,
    allowing the intermediate PDF to be returned directly without OCRmyPDF processing.

    Args:
        job_id: Job identifier
        enabled: Whether pass-through mode is enabled
        reason: Reason for pass-through (e.g., "pdf_output_no_ocr")
        pdfa_level: Target PDF/A level (or "pdf" for non-PDF/A)
        ocr_enabled: Whether OCR was enabled in config
        has_tags: Whether document has structure tags
        tags_preserved: Whether tags were preserved

    Example:
        await log_passthrough_mode_event(
            job_id="uuid-123",
            enabled=True,
            reason="pdf_output_no_ocr",
            pdfa_level="pdf",
            ocr_enabled=False,
            has_tags=True,
            tags_preserved=True
        )

    """
    # Build message
    if enabled:
        message = f"Pass-through mode activated: {reason}"
        if tags_preserved and has_tags:
            message += " (tags preserved)"
    else:
        message = "Pass-through mode not applicable"

    # Build details
    details: dict[str, Any] = {
        "enabled": enabled,
        "reason": reason,
        "pdfa_level": pdfa_level,
        "ocr_enabled": ocr_enabled,
        "has_tags": has_tags,
        "tags_preserved": tags_preserved,
    }

    # Create and persist event
    event = JobEvent(
        event_type="passthrough_mode",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{reason}.{pdfa_level}",
                "_i18n_params": {"reason": reason, "pdfa_level": pdfa_level},
            },
        )

        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")


async def log_fallback_applied_event(
    job_id: str,
    tier: int,
    reason: str,
    original_error: str | None = None,
    safe_mode_config: dict[str, Any] | None = None,
    pdfa_level_downgrade: dict[str, str] | None = None,
    tier2_error: str | None = None,
    ocr_disabled: bool | None = None,
) -> None:
    """Log fallback tier activation event.

    Fallback tiers are used when OCRmyPDF fails with standard settings:
    - Tier 2: Safe mode with reduced image DPI, optimize=0, PDF/A 3→2 downgrade
    - Tier 3: No OCR, safe mode only

    Args:
        job_id: Job identifier
        tier: Fallback tier (2 or 3)
        reason: Reason for fallback (e.g., "ghostscript_error", "tier2_failed")
        original_error: Original error message from tier 1
        safe_mode_config: Safe mode configuration applied
        pdfa_level_downgrade: PDF/A level downgrade details
        tier2_error: Error from tier 2 (for tier 3 fallback)
        ocr_disabled: Whether OCR was disabled (tier 3)

    Example:
        await log_fallback_applied_event(
            job_id="uuid-123",
            tier=2,
            reason="ghostscript_error",
            original_error="SubprocessOutputError: Ghostscript failed",
            safe_mode_config={"image_dpi": 100, "optimize": 0},
            pdfa_level_downgrade={"original": "3", "fallback": "2"}
        )

    """
    # Build message
    if tier == 2:
        message = f"Fallback tier {tier} applied: Safe mode + PDF/A downgrade"
    elif tier == 3:
        message = f"Fallback tier {tier} applied: No OCR (safe mode only)"
    else:
        message = f"Fallback tier {tier} applied"

    # Build details
    details: dict[str, Any] = {
        "tier": tier,
        "reason": reason,
    }
    if original_error:
        details["original_error"] = original_error
    if safe_mode_config:
        details["safe_mode_config"] = safe_mode_config
    if pdfa_level_downgrade:
        details["pdfa_level_downgrade"] = pdfa_level_downgrade
    if tier2_error:
        details["tier2_error"] = tier2_error
    if ocr_disabled is not None:
        details["ocr_disabled"] = ocr_disabled

    # Create and persist event
    event = JobEvent(
        event_type="fallback_applied",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.tier{tier}.{reason}",
                "_i18n_params": {"tier": tier, "reason": reason},
            },
        )

        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")


async def log_job_timeout_event(
    job_id: str,
    timeout_seconds: int,
    runtime_seconds: float,
) -> None:
    """Log job timeout event.

    Args:
        job_id: Job identifier
        timeout_seconds: Configured timeout limit
        runtime_seconds: Actual runtime before timeout

    Example:
        await log_job_timeout_event(
            job_id="uuid-123",
            timeout_seconds=7200,
            runtime_seconds=7305
        )

    """
    message = f"Job timeout after {timeout_seconds}s (runtime: {runtime_seconds:.0f}s)"

    details: dict[str, Any] = {
        "timeout_seconds": timeout_seconds,
        "runtime_seconds": runtime_seconds,
        "job_cancelled": True,
    }

    # Create and persist event
    event = JobEvent(
        event_type="job_timeout",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.exceeded.max_duration",
                "_i18n_params": {"timeout_sec": timeout_seconds},
            },
        )

        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")


async def log_job_cleanup_event(
    job_id: str,
    trigger: str,
    ttl_seconds: int | None = None,
    age_seconds: float | None = None,
    files_deleted: dict[str, str] | None = None,
    total_size_bytes: int | None = None,
) -> None:
    """Log job cleanup event.

    Args:
        job_id: Job identifier
        trigger: Cleanup trigger (e.g., "age_exceeded", "timeout")
        ttl_seconds: Configured TTL in seconds
        age_seconds: Actual age of job at cleanup
        files_deleted: Dict of deleted files (input_file, output_file, temp_directory)
        total_size_bytes: Total size of deleted files

    Example:
        await log_job_cleanup_event(
            job_id="uuid-123",
            trigger="age_exceeded",
            ttl_seconds=3600,
            age_seconds=3720,
            files_deleted={
                "input_file": "/tmp/input.pdf",
                "output_file": "/tmp/output.pdf"
            },
            total_size_bytes=2048576
        )

    """
    # Build message
    if trigger == "age_exceeded":
        message = f"Job cleaned up: TTL exceeded ({ttl_seconds}s limit)"
    elif trigger == "timeout":
        message = "Job cleaned up: Timeout"
    else:
        message = f"Job cleaned up: {trigger}"

    # Build details
    details: dict[str, Any] = {
        "trigger": trigger,
    }
    if ttl_seconds is not None:
        details["ttl_seconds"] = ttl_seconds
    if age_seconds is not None:
        details["age_seconds"] = age_seconds
    if files_deleted:
        details["files_deleted"] = files_deleted
    if total_size_bytes is not None:
        details["total_size_bytes"] = total_size_bytes

    # Create and persist event
    event = JobEvent(
        event_type="job_cleanup",
        message=message,
        details=details,
    )

    repo = JobRepository()
    await repo.add_job_event(job_id, event)

    # Broadcast event to WebSocket clients
    try:
        from pdfa.job_manager import get_job_manager
        from pdfa.websocket_protocol import JobEventMessage

        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{trigger}.success",
                "_i18n_params": {"trigger": trigger},
            },
        )

        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Event broadcast timeout for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event for job {job_id}: {e}")
