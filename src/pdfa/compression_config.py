"""Configuration for PDF compression settings.

This module provides configuration options for OCRmyPDF compression parameters,
allowing fine-tuning of the trade-off between file size and quality.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class CompressionConfig:
    """Configuration for PDF compression parameters.

    Attributes:
        image_dpi: Target DPI for images (default: 150).
            - Lower values = smaller files but lower quality
            - Typical values: 72 (screen), 150 (documents), 300 (high quality)
            - Range: 72-600 DPI

        jpg_quality: JPEG compression quality (default: 85).
            - Scale: 1-100 (higher = better quality, larger files)
            - 85-95: Good balance for documents
            - 70-84: Acceptable for most documents
            - Below 70: Visible quality loss

        optimize: Optimization level (default: 1).
            - 0: No optimization
            - 1: Low optimization (lossless, fast)
            - 2: Medium optimization (requires pngquant)
            - 3: High optimization (slower, requires pngquant)

        remove_vectors: Remove vector graphics where possible (default: True).
            - True: Convert vectors to raster (smaller files, may lose quality)
            - False: Keep vector graphics (larger files, better quality)

        jbig2_lossy: Use lossy JBIG2 compression for B&W images (default: False).
            - False: Lossless compression (recommended for documents)
            - True: Lossy compression (smaller files, may affect text quality)

        jbig2_page_group_size: Pages to group for JBIG2 compression (default: 10).
            - Groups pages to find repeating patterns (better compression)
            - Higher values = better compression but slower processing
            - Range: 0 (disabled) to 100+

    """

    image_dpi: int = 150
    jpg_quality: int = 85
    optimize: Literal[0, 1, 2, 3] = 1
    remove_vectors: bool = True
    jbig2_lossy: bool = False
    jbig2_page_group_size: int = 10

    @classmethod
    def from_env(cls) -> CompressionConfig:
        """Load compression configuration from environment variables.

        Reads the following environment variables:
            - PDFA_IMAGE_DPI: Target DPI for images (default: 150)
            - PDFA_JPG_QUALITY: JPEG quality 1-100 (default: 85)
            - PDFA_OPTIMIZE: Optimization level 0-3 (default: 1)
            - PDFA_REMOVE_VECTORS: Remove vectors true/false (default: true)
            - PDFA_JBIG2_LOSSY: Use lossy JBIG2 true/false (default: false)
            - PDFA_JBIG2_PAGE_GROUP_SIZE: JBIG2 page group size (default: 10)

        Returns:
            CompressionConfig instance with values from environment or defaults.

        """
        return cls(
            image_dpi=int(os.getenv("PDFA_IMAGE_DPI", "150")),
            jpg_quality=int(os.getenv("PDFA_JPG_QUALITY", "85")),
            optimize=int(os.getenv("PDFA_OPTIMIZE", "1")),  # type: ignore
            remove_vectors=os.getenv("PDFA_REMOVE_VECTORS", "true").lower()
            in ("true", "1", "yes"),
            jbig2_lossy=os.getenv("PDFA_JBIG2_LOSSY", "false").lower()
            in ("true", "1", "yes"),
            jbig2_page_group_size=int(os.getenv("PDFA_JBIG2_PAGE_GROUP_SIZE", "10")),
        )

    def validate(self) -> None:
        """Validate compression configuration parameters.

        Raises:
            ValueError: If any parameter is out of valid range.

        """
        if not 72 <= self.image_dpi <= 600:
            raise ValueError(
                f"image_dpi must be between 72 and 600, got {self.image_dpi}"
            )

        if not 1 <= self.jpg_quality <= 100:
            raise ValueError(
                f"jpg_quality must be between 1 and 100, got {self.jpg_quality}"
            )

        if self.optimize not in (0, 1, 2, 3):
            raise ValueError(f"optimize must be 0, 1, 2, or 3, got {self.optimize}")

        if self.jbig2_page_group_size < 0:
            raise ValueError(
                f"jbig2_page_group_size must be >= 0, got {self.jbig2_page_group_size}"
            )


# Preset configurations for common use cases
PRESETS = {
    "balanced": CompressionConfig(
        image_dpi=150,
        jpg_quality=85,
        optimize=1,
        remove_vectors=True,
        jbig2_lossy=False,
        jbig2_page_group_size=10,
    ),
    "quality": CompressionConfig(
        image_dpi=300,
        jpg_quality=95,
        optimize=1,
        remove_vectors=False,
        jbig2_lossy=False,
        jbig2_page_group_size=10,
    ),
    "aggressive": CompressionConfig(
        image_dpi=100,
        jpg_quality=75,
        optimize=3,
        remove_vectors=True,
        jbig2_lossy=False,
        jbig2_page_group_size=20,
    ),
    "minimal": CompressionConfig(
        image_dpi=72,
        jpg_quality=70,
        optimize=3,
        remove_vectors=True,
        jbig2_lossy=False,
        jbig2_page_group_size=50,
    ),
    "preserve": CompressionConfig(
        image_dpi=300,
        jpg_quality=95,
        optimize=1,  # Lossless optimization, avoids warnings
        remove_vectors=False,
        jbig2_lossy=False,
        jbig2_page_group_size=1,  # Minimum valid value
    ),
}
