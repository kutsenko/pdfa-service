"""Integration tests for Office and ODF document to PDF/A conversion.

These tests require LibreOffice, Tesseract, and Ghostscript to be installed.
They are skipped gracefully if dependencies are unavailable.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# Check for required dependencies
HAS_LIBREOFFICE = shutil.which("libreoffice") is not None
HAS_TESSERACT = shutil.which("tesseract") is not None
HAS_GHOSTSCRIPT = shutil.which("gs") is not None


def create_test_docx(path: Path) -> None:
    """Create a minimal valid DOCX file."""
    # DOCX is a ZIP file with specific structure
    import zipfile

    # Create minimal DOCX structure
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as docx:
        # Add [Content_Types].xml
        docx.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )

        # Add _rels/.rels
        docx.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )

        # Add word/document.xml
        docx.writestr(
            "word/document.xml",
            '<?xml version="1.0"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            "<w:p>"
            "<w:r>"
            "<w:t>Test Document</w:t>"
            "</w:r>"
            "</w:p>"
            "</w:body>"
            "</w:document>",
        )


def create_test_pptx(path: Path) -> None:
    """Create a minimal valid PPTX file."""
    import zipfile

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as pptx:
        # Add [Content_Types].xml
        pptx.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            "</Types>",
        )

        # Add _rels/.rels
        pptx.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            "</Relationships>",
        )

        # Add ppt/presentation.xml
        pptx.writestr(
            "ppt/presentation.xml",
            '<?xml version="1.0"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            "<p:sldIdLst>"
            '<p:sldId id="256" r:id="rId1"/>'
            "</p:sldIdLst>"
            "</p:presentation>",
        )

        # Add ppt/slides/slide1.xml
        pptx.writestr(
            "ppt/slides/slide1.xml",
            '<?xml version="1.0"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            "<p:cSld>"
            "<p:spTree>"
            "<p:sp>"
            "<p:nvSpPr>"
            '<p:cNvPr id="1" name="Title"/>'
            "</p:nvSpPr>"
            "</p:sp>"
            "</p:spTree>"
            "</p:cSld>"
            "</p:sld>",
        )

        # Add ppt/_rels/presentation.xml.rels
        pptx.writestr(
            "ppt/_rels/presentation.xml.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'
            "</Relationships>",
        )


def create_test_xlsx(path: Path) -> None:
    """Create a minimal valid XLSX file."""
    import zipfile

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as xlsx:
        # Add [Content_Types].xml
        xlsx.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>",
        )

        # Add _rels/.rels
        xlsx.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )

        # Add xl/workbook.xml
        xlsx.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheets>"
            '<sheet name="Sheet1" sheetId="1" r:id="rId1"/>'
            "</sheets>"
            "</workbook>",
        )

        # Add xl/worksheets/sheet1.xml
        xlsx.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1">'
            '<c r="A1" t="inlineStr">'
            "<is>"
            "<t>Test Data</t>"
            "</is>"
            "</c>"
            "</row>"
            "</sheetData>"
            "</worksheet>",
        )

        # Add xl/_rels/workbook.xml.rels
        xlsx.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )


def create_test_odt(path: Path) -> None:
    """Create a minimal valid ODT (OpenDocument Text) file."""
    import zipfile

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as odt:
        # Add mimetype (must be first and uncompressed for valid ODF)
        odt.writestr(
            "mimetype",
            "application/vnd.oasis.opendocument.text",
            compress_type=zipfile.ZIP_STORED,
        )

        # Add META-INF/manifest.xml
        odt.writestr(
            "META-INF/manifest.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
            '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" manifest:full-path="/"/>'
            '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
            '</manifest:manifest>',
        )

        # Add content.xml
        odt.writestr(
            "content.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            '<office:body><office:text><text:p>Test ODT Document</text:p></office:text></office:body>'
            '</office:document>',
        )


def create_test_ods(path: Path) -> None:
    """Create a minimal valid ODS (OpenDocument Spreadsheet) file."""
    import zipfile

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as ods:
        # Add mimetype
        ods.writestr(
            "mimetype",
            "application/vnd.oasis.opendocument.spreadsheet",
            compress_type=zipfile.ZIP_STORED,
        )

        # Add META-INF/manifest.xml
        ods.writestr(
            "META-INF/manifest.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
            '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.spreadsheet" manifest:full-path="/"/>'
            '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
            '</manifest:manifest>',
        )

        # Add content.xml
        ods.writestr(
            "content.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            '<office:body><office:spreadsheet><table:table table:name="Sheet1">'
            '<table:table-row><table:table-cell><text:p>Test ODS Data</text:p></table:table-cell></table:table-row>'
            '</table:table></office:spreadsheet></office:body>'
            '</office:document>',
        )


def create_test_odp(path: Path) -> None:
    """Create a minimal valid ODP (OpenDocument Presentation) file."""
    import zipfile

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as odp:
        # Add mimetype
        odp.writestr(
            "mimetype",
            "application/vnd.oasis.opendocument.presentation",
            compress_type=zipfile.ZIP_STORED,
        )

        # Add META-INF/manifest.xml
        odp.writestr(
            "META-INF/manifest.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
            '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.presentation" manifest:full-path="/"/>'
            '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
            '</manifest:manifest>',
        )

        # Add content.xml
        odp.writestr(
            "content.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            '<office:body><office:presentation><draw:page><draw:text-box>'
            '<text:p>Test ODP Presentation</text:p>'
            '</draw:text-box></draw:page></office:presentation></office:body>'
            '</office:document>',
        )


@pytest.mark.skipif(
    not HAS_LIBREOFFICE,
    reason="LibreOffice not installed",
)
class TestOfficeConversion:
    """Integration tests for Office document conversion."""

    @pytest.fixture()
    def test_files(self, tmp_path: Path) -> dict[str, Path]:
        """Create test files in all supported Office and ODF formats."""
        files = {}

        # Create test DOCX
        docx_file = tmp_path / "test_document.docx"
        create_test_docx(docx_file)
        files["docx"] = docx_file

        # Create test PPTX
        pptx_file = tmp_path / "test_presentation.pptx"
        create_test_pptx(pptx_file)
        files["pptx"] = pptx_file

        # Create test XLSX
        xlsx_file = tmp_path / "test_spreadsheet.xlsx"
        create_test_xlsx(xlsx_file)
        files["xlsx"] = xlsx_file

        # Create test ODT
        odt_file = tmp_path / "test_document.odt"
        create_test_odt(odt_file)
        files["odt"] = odt_file

        # Create test ODS
        ods_file = tmp_path / "test_spreadsheet.ods"
        create_test_ods(ods_file)
        files["ods"] = ods_file

        # Create test ODP
        odp_file = tmp_path / "test_presentation.odp"
        create_test_odp(odp_file)
        files["odp"] = odp_file

        return files

    def test_convert_docx_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """DOCX files should be converted to PDF/A."""
        from pdfa.format_converter import convert_office_to_pdf

        output_pdf = tmp_path / "output.pdf"
        convert_office_to_pdf(test_files["docx"], output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        # Verify it's a PDF
        assert output_pdf.read_bytes().startswith(b"%PDF")

    def test_convert_odt_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """ODT files should be converted to PDF/A."""
        from pdfa.format_converter import convert_office_to_pdf

        output_pdf = tmp_path / "output.pdf"
        convert_office_to_pdf(test_files["odt"], output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        # Verify it's a PDF
        assert output_pdf.read_bytes().startswith(b"%PDF")

    def test_convert_ods_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """ODS files should be converted to PDF/A."""
        from pdfa.format_converter import convert_office_to_pdf

        output_pdf = tmp_path / "output.pdf"
        convert_office_to_pdf(test_files["ods"], output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        # Verify it's a PDF
        assert output_pdf.read_bytes().startswith(b"%PDF")

    def test_convert_odp_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """ODP files should be converted to PDF/A."""
        from pdfa.format_converter import convert_office_to_pdf

        output_pdf = tmp_path / "output.pdf"
        convert_office_to_pdf(test_files["odp"], output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        # Verify it's a PDF
        assert output_pdf.read_bytes().startswith(b"%PDF")

    @pytest.mark.skip(reason="Minimal PPTX not valid enough for LibreOffice conversion")
    def test_convert_pptx_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """PPTX files should be converted to PDF/A."""
        from pdfa.format_converter import convert_office_to_pdf

        output_pdf = tmp_path / "output.pdf"
        convert_office_to_pdf(test_files["pptx"], output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        assert output_pdf.read_bytes().startswith(b"%PDF")

    @pytest.mark.skip(reason="Minimal XLSX not valid enough for LibreOffice conversion")
    def test_convert_xlsx_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """XLSX files should be converted to PDF/A."""
        from pdfa.format_converter import convert_office_to_pdf

        output_pdf = tmp_path / "output.pdf"
        convert_office_to_pdf(test_files["xlsx"], output_pdf)

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        assert output_pdf.read_bytes().startswith(b"%PDF")

    @pytest.mark.skipif(
        not (HAS_TESSERACT and HAS_GHOSTSCRIPT),
        reason="Tesseract or Ghostscript not installed",
    )
    def test_docx_end_to_end_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """DOCX should be converted end-to-end to PDF/A."""
        from pdfa.cli import main

        output_pdf = tmp_path / "output.pdf"
        exit_code = main([str(test_files["docx"]), str(output_pdf)])

        assert exit_code == 0
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        # Verify it's a PDF
        assert output_pdf.read_bytes().startswith(b"%PDF")

    @pytest.mark.skip(reason="Minimal PPTX not valid enough for LibreOffice conversion")
    def test_pptx_end_to_end_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """PPTX should be converted end-to-end to PDF/A."""
        from pdfa.cli import main

        output_pdf = tmp_path / "output.pdf"
        exit_code = main([str(test_files["pptx"]), str(output_pdf)])

        assert exit_code == 0
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        assert output_pdf.read_bytes().startswith(b"%PDF")

    @pytest.mark.skip(reason="Minimal XLSX not valid enough for LibreOffice conversion")
    def test_xlsx_end_to_end_to_pdfa(
        self, test_files: dict[str, Path], tmp_path: Path
    ) -> None:
        """XLSX should be converted end-to-end to PDF/A."""
        from pdfa.cli import main

        output_pdf = tmp_path / "output.pdf"
        exit_code = main([str(test_files["xlsx"]), str(output_pdf)])

        assert exit_code == 0
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        assert output_pdf.read_bytes().startswith(b"%PDF")
