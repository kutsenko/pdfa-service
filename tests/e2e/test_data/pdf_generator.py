"""Helper module to generate test PDF files of various sizes."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def create_minimal_pdf(output_path: Path) -> None:
    """Create a minimal valid PDF file.

    Args:
        output_path: Path where to save the PDF

    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    c.drawString(100, 750, "Minimal Test PDF")
    c.showPage()
    c.save()


def create_small_pdf(output_path: Path, num_pages: int = 3) -> None:
    """Create a small PDF with a few pages.

    Args:
        output_path: Path where to save the PDF
        num_pages: Number of pages to create (default: 3)

    """
    c = canvas.Canvas(str(output_path), pagesize=A4)

    for page_num in range(1, num_pages + 1):
        c.drawString(100, 800, f"Page {page_num} of {num_pages}")
        c.drawString(100, 750, "This is a test PDF for E2E testing.")
        c.drawString(100, 700, "It contains minimal content.")
        c.showPage()

    c.save()


def create_medium_pdf(output_path: Path, num_pages: int = 10) -> None:
    """Create a medium-sized PDF with multiple pages and content.

    Args:
        output_path: Path where to save the PDF
        num_pages: Number of pages to create (default: 10)

    """
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    for page_num in range(1, num_pages + 1):
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, f"Test Document - Page {page_num}")

        # Subtitle
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, f"Page {page_num} of {num_pages}")

        # Content
        c.setFont("Helvetica", 10)
        y_position = height - 180

        for line_num in range(30):
            text = (
                f"This is line {line_num + 1} on page {page_num}. "
                f"It contains some text to make the PDF more realistic."
            )
            c.drawString(100, y_position, text)
            y_position -= 15

            if y_position < 100:
                break

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(width - 150, 50, f"Generated for testing")

        c.showPage()

    c.save()


def create_large_pdf(output_path: Path, num_pages: int = 50) -> None:
    """Create a large PDF with many pages (for stress testing).

    Args:
        output_path: Path where to save the PDF
        num_pages: Number of pages to create (default: 50)

    """
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    for page_num in range(1, num_pages + 1):
        # Title
        c.setFont("Helvetica-Bold", 18)
        c.drawString(
            100, height - 80, f"Large Test Document - Page {page_num}/{num_pages}"
        )

        # Add some graphics
        c.rect(50, height - 150, width - 100, 50, stroke=1, fill=0)

        # Content sections
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 200, "Section 1: Introduction")

        c.setFont("Helvetica", 10)
        y_position = height - 230

        # Multiple paragraphs
        for para_num in range(5):
            c.drawString(100, y_position, f"Paragraph {para_num + 1}:")
            y_position -= 15

            for line_num in range(6):
                text = (
                    f"This is sentence {line_num + 1} of paragraph {para_num + 1}. "
                    f"It contains enough text to simulate a real document. "
                    f"The content is generated automatically for testing purposes."
                )
                c.drawString(120, y_position, text)
                y_position -= 12

            y_position -= 10  # Space between paragraphs

            if y_position < 100:
                break

        # Page number
        c.setFont("Helvetica", 9)
        c.drawString(width / 2 - 20, 30, f"Page {page_num}")

        c.showPage()

        # Progress indicator every 10 pages
        if page_num % 10 == 0:
            print(f"Generated {page_num}/{num_pages} pages...")

    c.save()
    print(f"Large PDF created: {num_pages} pages")


def create_very_large_pdf(output_path: Path, num_pages: int = 100) -> None:
    """Create a very large PDF for stress testing.

    Args:
        output_path: Path where to save the PDF
        num_pages: Number of pages to create (default: 100)

    """
    create_large_pdf(output_path, num_pages)


if __name__ == "__main__":
    # Generate test PDFs when run directly
    test_dir = Path(__file__).parent
    test_dir.mkdir(parents=True, exist_ok=True)

    print("Generating test PDFs...")

    create_minimal_pdf(test_dir / "minimal.pdf")
    print("✓ Created minimal.pdf")

    create_small_pdf(test_dir / "small.pdf", num_pages=3)
    print("✓ Created small.pdf (3 pages)")

    create_medium_pdf(test_dir / "medium.pdf", num_pages=10)
    print("✓ Created medium.pdf (10 pages)")

    create_large_pdf(test_dir / "large.pdf", num_pages=50)
    print("✓ Created large.pdf (50 pages)")

    create_very_large_pdf(test_dir / "very_large.pdf", num_pages=100)
    print("✓ Created very_large.pdf (100 pages)")

    print("\nAll test PDFs generated successfully!")
