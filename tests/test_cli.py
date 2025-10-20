"""Tests for the pdfa CLI that wraps OCRmyPDF."""

from typing import Any
import importlib.util
import sys
import types

import pytest

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

from ocrmypdf import exceptions as ocrmypdf_exceptions

from pdfa import __version__
from pdfa import cli


def test_version() -> None:
    """Ensure the package exposes a version string."""
    assert __version__ == "0.1.0"


def test_convert_to_pdfa_invokes_ocrmypdf(monkeypatch, tmp_path) -> None:
    """convert_to_pdfa should call OCRmyPDF with expected arguments."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["input"] = input_file
        calls["output"] = output_file
        calls["kwargs"] = kwargs

    monkeypatch.setattr(cli.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "result" / "output.pdf"

    cli.convert_to_pdfa(
        input_pdf,
        output_pdf,
        language="eng",
        pdfa_level="3",
    )

    assert calls["input"] == str(input_pdf)
    assert calls["output"] == str(output_pdf)
    assert calls["kwargs"]["language"] == "eng"
    assert calls["kwargs"]["output_type"] == "pdfa-3"
    assert calls["kwargs"]["force_ocr"] is True
    assert output_pdf.parent.exists()


def test_convert_to_pdfa_missing_input(tmp_path) -> None:
    """Missing input files should raise FileNotFoundError."""
    input_pdf = tmp_path / "missing.pdf"
    output_pdf = tmp_path / "out.pdf"

    with pytest.raises(FileNotFoundError):
        cli.convert_to_pdfa(
            input_pdf,
            output_pdf,
            language="eng",
            pdfa_level="2",
        )


def test_main_success(monkeypatch, tmp_path, capsys) -> None:
    """CLI should exit cleanly on successful conversion."""
    calls: dict[str, Any] = {}

    def fake_ocr(input_file: str, output_file: str, **kwargs: Any) -> None:
        calls["input"] = input_file
        calls["output"] = output_file
        calls["kwargs"] = kwargs

    monkeypatch.setattr(cli.ocrmypdf, "ocr", fake_ocr)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    exit_code = cli.main(
        [
            str(input_pdf),
            str(output_pdf),
            "--language",
            "deu",
            "--pdfa-level",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Successfully created PDF/A file" in captured.out
    assert calls["kwargs"]["language"] == "deu"
    assert calls["kwargs"]["output_type"] == "pdfa-1"
    assert calls["kwargs"]["force_ocr"] is True


def test_main_handles_ocrmypdf_error(monkeypatch, tmp_path, capsys) -> None:
    """CLI should surface OCRmyPDF errors and exit with the reported code."""

    class FakeError(ocrmypdf_exceptions.ExitCodeException):  # type: ignore[misc]
        """Stub exception with a fixed exit code for testing."""

        def __init__(self) -> None:
            self.exit_code = 5

        def __str__(self) -> str:
            return "conversion failed"

    def raise_error(*_: Any, **__: Any) -> None:
        raise FakeError()

    monkeypatch.setattr(cli, "convert_to_pdfa", raise_error)

    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test")
    output_pdf = tmp_path / "output.pdf"

    exit_code = cli.main([str(input_pdf), str(output_pdf)])

    captured = capsys.readouterr()
    assert exit_code == 5
    assert "conversion failed" in captured.err
