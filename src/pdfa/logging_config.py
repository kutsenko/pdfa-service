"""Logging configuration for pdfa service.

Includes MDC-style request context logging with user email and client IP.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from pdfa.request_context import RequestContextFilter


def configure_logging(
    level: int = logging.INFO,
    log_file: Path | str | None = None,
) -> None:
    """Configure logging for the pdfa service.

    Args:
        level: Logging level (default: logging.INFO).
        log_file: Optional path to write logs to file (default: None, logs to stderr).

    Log format includes:
        - Timestamp
        - Log level
        - User email (from request context, "-" if not in request)
        - Client IP (from request context, "-" if not in request)
        - Logger name
        - Message

    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Create context filter for MDC-style logging
    context_filter = RequestContextFilter()

    # Console handler (always to stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.addFilter(context_filter)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(user_email)s %(client_ip)s "
        "%(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(level)
        file_handler.addFilter(context_filter)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(user_email)s %(client_ip)s %(name)s: "
            "%(message)s (%(filename)s:%(lineno)d)",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure Uvicorn loggers to use our format
    # Uvicorn creates its own handlers, so we need to reconfigure them
    _configure_uvicorn_logging(context_filter, console_handler, level)


def _configure_uvicorn_logging(
    context_filter: RequestContextFilter,
    console_handler: logging.Handler,
    level: int,
) -> None:
    """Configure Uvicorn's loggers to use our MDC-style format.

    Uvicorn creates separate loggers for access and error logs.
    We reconfigure them to use our handlers with context information.
    """
    # Uvicorn access log format (includes request details)
    access_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(user_email)s %(client_ip)s "
        "uvicorn.access: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure uvicorn.access logger
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_handler = logging.StreamHandler(sys.stderr)
    access_handler.setLevel(level)
    access_handler.addFilter(context_filter)
    access_handler.setFormatter(access_formatter)
    access_logger.addHandler(access_handler)
    access_logger.propagate = False  # Don't propagate to root to avoid duplicate logs

    # Configure uvicorn.error logger
    error_logger = logging.getLogger("uvicorn.error")
    error_logger.handlers.clear()
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(level)
    error_handler.addFilter(context_filter)
    error_handler.setFormatter(console_handler.formatter)
    error_logger.addHandler(error_handler)
    error_logger.propagate = False  # Don't propagate to root to avoid duplicate logs

    # Configure uvicorn main logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_handler = logging.StreamHandler(sys.stderr)
    uvicorn_handler.setLevel(level)
    uvicorn_handler.addFilter(context_filter)
    uvicorn_handler.setFormatter(console_handler.formatter)
    uvicorn_logger.addHandler(uvicorn_handler)
    uvicorn_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: The name of the logger (typically __name__).

    Returns:
        A logger instance configured with the module name.

    """
    return logging.getLogger(name)
