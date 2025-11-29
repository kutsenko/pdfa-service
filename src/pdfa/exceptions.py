"""Custom exceptions for pdfa service."""

from __future__ import annotations


class OfficeConversionError(Exception):
    """Raised when Office document to PDF conversion fails."""

    pass


class UnsupportedFormatError(ValueError):
    """Raised when file format is not supported."""

    pass
