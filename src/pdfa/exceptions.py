"""Custom exceptions for pdfa service."""

from __future__ import annotations


class OfficeConversionError(Exception):
    """Raised when Office document to PDF conversion fails."""

    pass


class UnsupportedFormatError(ValueError):
    """Raised when file format is not supported."""

    pass


class JobCancelledException(Exception):
    """Raised when a conversion job is cancelled by user request."""

    pass


class JobTimeoutException(Exception):
    """Raised when a conversion job exceeds the timeout limit."""

    pass


class JobNotFoundException(Exception):
    """Raised when a requested job ID is not found."""

    pass
