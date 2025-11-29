"""Tests for Office document conversion in the CLI."""

from __future__ import annotations

from typing import Any

from pdfa import cli
from pdfa.exceptions import OfficeConversionError


class TestCliOfficeConversion:
    """Tests for Office document handling in CLI."""

    def test_cli_converts_docx(self, monkeypatch, tmp_path, capsys) -> None:
        """CLI should convert DOCX files to PDF/A."""

        def mock_convert_office(input_file, output_file):
            output_file.write_bytes(b"%PDF-1.4 converted")

        def mock_convert_to_pdfa(input_pdf, output_pdf, **kwargs):
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(cli, "convert_office_to_pdf", mock_convert_office)
        monkeypatch.setattr(cli, "convert_to_pdfa", mock_convert_to_pdfa)

        input_file = tmp_path / "document.docx"
        input_file.write_bytes(b"PK\x03\x04dummy")
        output_pdf = tmp_path / "output.pdf"

        exit_code = cli.main([str(input_file), str(output_pdf), "--language", "eng"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Successfully created PDF/A file" in captured.out
        # Logging goes to stderr, not stdout
        assert "Office document detected" in captured.err

    def test_cli_converts_pptx(self, monkeypatch, tmp_path, capsys) -> None:
        """CLI should convert PPTX files to PDF/A."""

        def mock_convert_office(input_file, output_file):
            output_file.write_bytes(b"%PDF-1.4 converted")

        def mock_convert_to_pdfa(input_pdf, output_pdf, **kwargs):
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(cli, "convert_office_to_pdf", mock_convert_office)
        monkeypatch.setattr(cli, "convert_to_pdfa", mock_convert_to_pdfa)

        input_file = tmp_path / "presentation.pptx"
        input_file.write_bytes(b"PK\x03\x04dummy")
        output_pdf = tmp_path / "output.pdf"

        exit_code = cli.main([str(input_file), str(output_pdf)])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Successfully created PDF/A file" in captured.out

    def test_cli_detects_unsupported_format(self, tmp_path, capsys) -> None:
        """CLI should handle unsupported file formats gracefully."""
        input_file = tmp_path / "document.txt"
        input_file.write_text("text content")
        output_pdf = tmp_path / "output.pdf"

        exit_code = cli.main([str(input_file), str(output_pdf)])

        captured = capsys.readouterr()
        # argparse fails with exit code 2 for invalid arguments
        assert exit_code != 0
        assert len(captured.err) > 0

    def test_cli_handles_office_conversion_failure(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        """CLI should handle Office conversion errors gracefully."""

        def raise_error(*_: Any, **__: Any) -> None:
            raise OfficeConversionError("LibreOffice failed")

        monkeypatch.setattr(cli, "convert_office_to_pdf", raise_error)

        input_file = tmp_path / "document.docx"
        input_file.write_bytes(b"PK\x03\x04dummy")
        output_pdf = tmp_path / "output.pdf"

        exit_code = cli.main([str(input_file), str(output_pdf)])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Office conversion failed" in captured.err

    def test_cli_cleans_up_temp_pdf_on_success(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        """CLI should clean up temporary PDF after successful conversion."""

        def mock_convert_office(input_file, output_file):
            output_file.write_bytes(b"%PDF-1.4 converted")

        def mock_convert_to_pdfa(input_pdf, output_pdf, **kwargs):
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(cli, "convert_office_to_pdf", mock_convert_office)
        monkeypatch.setattr(cli, "convert_to_pdfa", mock_convert_to_pdfa)

        input_file = tmp_path / "document.docx"
        input_file.write_bytes(b"PK\x03\x04dummy")
        output_pdf = tmp_path / "output.pdf"

        exit_code = cli.main([str(input_file), str(output_pdf)])

        assert exit_code == 0
        # Temporary PDF should be deleted
        temp_pdf = tmp_path / "document_temp.pdf"
        assert not temp_pdf.exists()

    def test_cli_handles_pdf_input(self, monkeypatch, tmp_path, capsys) -> None:
        """CLI should handle PDF inputs without Office conversion."""

        def mock_convert_to_pdfa(input_pdf, output_pdf, **kwargs):
            output_pdf.write_bytes(b"%PDF-1.4 pdfa")

        monkeypatch.setattr(cli, "convert_to_pdfa", mock_convert_to_pdfa)

        input_file = tmp_path / "document.pdf"
        input_file.write_bytes(b"%PDF-1.4 test")
        output_pdf = tmp_path / "output.pdf"

        exit_code = cli.main([str(input_file), str(output_pdf)])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Successfully created PDF/A file" in captured.out
        # Should not mention Office conversion for PDF files
        assert "Office document detected" not in captured.out
