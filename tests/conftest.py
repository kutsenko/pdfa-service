"""Test-wide fixtures and stubs."""

from __future__ import annotations

import importlib.util
import sys
import types

if importlib.util.find_spec("ocrmypdf") is None:
    exceptions_module = types.ModuleType("ocrmypdf.exceptions")

    class ExitCodeException(Exception):
        """Fallback ExitCodeException used when OCRmyPDF is absent."""

        exit_code = 1

    class OCRmyPDFError(ExitCodeException):
        """Backward-compatible alias matching older OCRmyPDF documentation."""

        pass

    exceptions_module.ExitCodeException = ExitCodeException
    exceptions_module.OCRmyPDFError = OCRmyPDFError

    ocrmypdf_stub = types.ModuleType("ocrmypdf")
    ocrmypdf_stub.ocr = lambda *args, **kwargs: None  # type: ignore[assignment]
    ocrmypdf_stub.exceptions = exceptions_module

    sys.modules["ocrmypdf"] = ocrmypdf_stub
    sys.modules["ocrmypdf.exceptions"] = exceptions_module
