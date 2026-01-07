"""Request context for MDC-style logging.

This module provides context variables that are automatically included
in all log messages within a request scope. Similar to MDC (Mapped
Diagnostic Context) in Java logging frameworks.

Usage:
    # In middleware (automatically done by RequestContextMiddleware):
    set_request_context(user_email="user@example.com", client_ip="192.168.1.1")

    # In any code within the request:
    logger.info("Processing file")
    # Output: 2024-01-07 10:30:45 [INFO] user@example.com 192.168.1.1 ...
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

    from pdfa.user_models import User

# Context variables for request-scoped data
_user_email: ContextVar[str] = ContextVar("user_email", default="-")
_client_ip: ContextVar[str] = ContextVar("client_ip", default="-")


def set_request_context(
    user_email: str | None = None,
    client_ip: str | None = None,
) -> None:
    """Set context variables for the current request.

    Args:
        user_email: User's email address (or None for anonymous)
        client_ip: Client IP address

    """
    if user_email is not None:
        _user_email.set(user_email)
    if client_ip is not None:
        _client_ip.set(client_ip)


def clear_request_context() -> None:
    """Clear context variables (reset to defaults)."""
    _user_email.set("-")
    _client_ip.set("-")


def get_user_email() -> str:
    """Get the current request's user email."""
    return _user_email.get()


def get_client_ip() -> str:
    """Get the current request's client IP."""
    return _client_ip.get()


class RequestContextFilter(logging.Filter):
    """Logging filter that adds request context to log records.

    This filter reads from contextvars and adds user_email and client_ip
    attributes to each log record, making them available in log formatters.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context variables to the log record.

        Args:
            record: The log record to modify

        Returns:
            Always True (never filters out records)

        """
        record.user_email = _user_email.get()
        record.client_ip = _client_ip.get()
        return True


def extract_context_from_request(
    request: Request,
    user: User | None = None,
) -> tuple[str, str]:
    """Extract user email and client IP from a request.

    Args:
        request: FastAPI request object
        user: Optional authenticated user

    Returns:
        Tuple of (user_email, client_ip)

    """
    # Get user email
    user_email = user.email if user else "-"

    # Get client IP (priority: X-Forwarded-For, then direct IP)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"

    return user_email, client_ip
