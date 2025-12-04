# PDF Compression Configuration

**Documentation in other languages**: [Deutsch (German)](COMPRESSION.de.md)

The PDF/A service provides comprehensive configuration options for PDF compression, allowing you to optimize the balance between file size and image quality.

## Parameter Overview

All compression parameters can be configured via environment variables. The default values provide a balanced trade-off between quality and file size.

### PDFA_IMAGE_DPI

**Description:** Target resolution for images in DPI (Dots Per Inch)

**Default:** `150`

**Valid Range:** 72-600 DPI

**Effects:**
- **Lower values (72-100 DPI):**
  - Smaller file sizes (up to 80% reduction)
  - Suitable for text-only documents
  - Images may appear pixelated
  - Optimal for archival with minimal image content

- **Medium values (150-200 DPI):**
  - Balanced ratio (default)
  - Good readability of text and images
  - Moderate file size
  - Ideal for most office documents

- **Higher values (300-600 DPI):**
  - High-quality images
  - Larger files (2-4x larger than 150 DPI)
  - Necessary for photos and detailed graphics
  - Recommended for print-ready documents

**Example:**
```yaml
- PDFA_IMAGE_DPI=100  # Aggressive compression
- PDFA_IMAGE_DPI=150  # Balanced (default)
- PDFA_IMAGE_DPI=300  # High quality
```

### PDFA_JPG_QUALITY

**Description:** JPEG compression quality for color images

**Default:** `85`

**Valid Range:** 1-100 (higher = better quality)

**Effects:**
- **Low values (60-75):**
  - Significant file size reduction (50-70% smaller)
  - Visible JPEG artifacts possible
  - Only suitable for non-critical documents

- **Medium values (80-90):**
  - Good balance (default: 85)
  - Barely visible quality loss
  - Recommended for most use cases

- **High values (91-100):**
  - Minimal compression
  - Very high image quality
  - Significantly larger files
  - Use only for critical requirements

**Example:**
```yaml
- PDFA_JPG_QUALITY=70  # Strong compression
- PDFA_JPG_QUALITY=85  # Balanced (default)
- PDFA_JPG_QUALITY=95  # High quality
```

### PDFA_OPTIMIZE

**Description:** OCRmyPDF optimization level

**Default:** `1`

**Valid Values:** 0, 1, 2, 3

**Effects:**
- **Level 0 (No optimization):**
  - Fastest processing
  - Largest files
  - Only recommended for testing

- **Level 1 (Low optimization):**
  - Lossless compression
  - Fast processing (default)
  - Moderate file size reduction (20-30%)
  - Recommended for production use

- **Level 2 (Medium optimization):**
  - Requires `pngquant` (included in Docker image)
  - Better PNG compression
  - Longer processing time
  - 30-50% file size reduction

- **Level 3 (High optimization):**
  - Requires `pngquant`
  - Maximum compression
  - Significantly longer processing time
  - 40-60% file size reduction
  - Use only when optimization is critical

**Example:**
```yaml
- PDFA_OPTIMIZE=1  # Fast and lossless (default)
- PDFA_OPTIMIZE=2  # Better compression
- PDFA_OPTIMIZE=3  # Maximum compression (slow)
```

### PDFA_REMOVE_VECTORS

**Description:** Convert vector graphics to raster graphics

**Default:** `true`

**Valid Values:** `true`, `false`, `1`, `0`, `yes`, `no`

**Effects:**
- **true (enabled):**
  - Vector graphics are rasterized
  - Smaller files (up to 50% with many vectors)
  - Possible quality loss when scaling
  - Recommended for archival

- **false (disabled):**
  - Vector graphics remain preserved
  - Larger files
  - Better scalability
  - Recommended for documents with many diagrams/logos

**Example:**
```yaml
- PDFA_REMOVE_VECTORS=true   # Smaller files (default)
- PDFA_REMOVE_VECTORS=false  # Keep vector graphics
```

### PDFA_JBIG2_LOSSY

**Description:** Lossy JBIG2 compression for black-and-white images

**Default:** `false`

**Valid Values:** `true`, `false`, `1`, `0`, `yes`, `no`

**Effects:**
- **false (lossless):**
  - Recommended for text documents (default)
  - No quality loss
  - Excellent compression for B&W images
  - Text remains readable

- **true (lossy):**
  - Even smaller files (additional 10-30%)
  - Possible text alterations
  - **Not recommended** for important documents
  - Only for non-critical archives

**Warning:** Lossy JBIG2 compression can alter text and should be avoided for official documents!

**Example:**
```yaml
- PDFA_JBIG2_LOSSY=false  # Safe and recommended (default)
- PDFA_JBIG2_LOSSY=true   # Only for non-critical documents
```

### PDFA_JBIG2_PAGE_GROUP_SIZE

**Description:** Number of pages grouped for JBIG2 compression

**Default:** `10`

**Valid Range:** 0-100+ (0 disables grouping)

**Effects:**
- **0 (disabled):**
  - No cross-page compression
  - Faster processing
  - Larger files

- **10-20 (recommended):**
  - Good balance (default: 10)
  - Finds patterns across multiple pages
  - Moderate processing time

- **50-100 (aggressive):**
  - Maximum compression for large documents
  - Longer processing time
  - Especially effective for repetitive content

**Example:**
```yaml
- PDFA_JBIG2_PAGE_GROUP_SIZE=0   # No grouping
- PDFA_JBIG2_PAGE_GROUP_SIZE=10  # Default
- PDFA_JBIG2_PAGE_GROUP_SIZE=50  # Aggressive compression
```

## Predefined Profiles

The `compression_config.py` module defines the following preset profiles:

### balanced (Default)
Balanced settings for most use cases:
```yaml
- PDFA_IMAGE_DPI=150
- PDFA_JPG_QUALITY=85
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=10
```

**Ideal for:** Office documents, general archival

### quality (High Quality)
Maximum quality with moderate compression:
```yaml
- PDFA_IMAGE_DPI=300
- PDFA_JPG_QUALITY=95
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=false
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=10
```

**Ideal for:** Print-ready documents, photos, detailed graphics

### aggressive (Strong Compression)
Significant file size reduction with acceptable quality:
```yaml
- PDFA_IMAGE_DPI=100
- PDFA_JPG_QUALITY=75
- PDFA_OPTIMIZE=3
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=20
```

**Ideal for:** Long-term archival, large document volumes

### minimal (Maximum Compression)
Smallest file size for non-critical documents:
```yaml
- PDFA_IMAGE_DPI=72
- PDFA_JPG_QUALITY=70
- PDFA_OPTIMIZE=3
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=50
```

**Ideal for:** Readability is priority, maximum space savings

## Usage in docker-compose.yml

Default settings are already configured in `docker-compose.yml`. Adjust as needed:

```yaml
services:
  pdfa:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      # Example: Aggressive compression
      - PDFA_IMAGE_DPI=100
      - PDFA_JPG_QUALITY=75
      - PDFA_OPTIMIZE=3
      - PDFA_REMOVE_VECTORS=true
      - PDFA_JBIG2_LOSSY=false
      - PDFA_JBIG2_PAGE_GROUP_SIZE=20
    restart: unless-stopped
```

## Usage in CLI

The CLI reads the same environment variables:

```bash
# With default settings
pdfa-cli input.pdf output.pdf

# With custom settings
export PDFA_IMAGE_DPI=100
export PDFA_JPG_QUALITY=75
pdfa-cli input.pdf output.pdf

# One-time for a single command
PDFA_IMAGE_DPI=300 PDFA_JPG_QUALITY=95 pdfa-cli photo.pdf output.pdf
```

## Recommendations by Use Case

### Text Documents (Invoices, Contracts)
```yaml
- PDFA_IMAGE_DPI=150
- PDFA_JPG_QUALITY=80
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
```
**Result:** Small files, good readability, safe archival

### Documents with Photos
```yaml
- PDFA_IMAGE_DPI=200
- PDFA_JPG_QUALITY=90
- PDFA_OPTIMIZE=2
- PDFA_REMOVE_VECTORS=false
- PDFA_JBIG2_LOSSY=false
```
**Result:** Good image quality, moderate file size

### Scanned Documents
```yaml
- PDFA_IMAGE_DPI=150
- PDFA_JPG_QUALITY=80
- PDFA_OPTIMIZE=2
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=20
```
**Result:** Optimal compression for scans

### Technical Drawings/Diagrams
```yaml
- PDFA_IMAGE_DPI=300
- PDFA_JPG_QUALITY=90
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=false
- PDFA_JBIG2_LOSSY=false
```
**Result:** Sharp lines, lossless vectors

## Performance Notes

Processing speed is mainly influenced by these parameters:

1. **PDFA_OPTIMIZE:** Level 3 is significantly slower (3-5x) than Level 1
2. **PDFA_IMAGE_DPI:** Higher DPI = longer processing
3. **PDFA_JBIG2_PAGE_GROUP_SIZE:** Larger values = longer processing

**Recommendation for production:**
- Use `PDFA_OPTIMIZE=1` for fast processing
- Use levels 2-3 only during off-hours or in batch jobs
- Test settings with representative documents

## File Size Expectations

Examples for a typical 10-page document with text and images:

| Configuration | File Size | Quality | Speed |
|---------------|-----------|---------|-------|
| **quality** | ~2.5 MB | Excellent | Fast |
| **balanced** (default) | ~1.2 MB | Very good | Fast |
| **aggressive** | ~600 KB | Good | Medium |
| **minimal** | ~400 KB | Acceptable | Slow |

Results vary significantly depending on document content.

## Troubleshooting

### Quality too low
- Increase `PDFA_IMAGE_DPI` to 200 or 300
- Increase `PDFA_JPG_QUALITY` to 90 or higher
- Set `PDFA_REMOVE_VECTORS=false`

### Files too large
- Reduce `PDFA_IMAGE_DPI` to 100-120
- Reduce `PDFA_JPG_QUALITY` to 75-80
- Increase `PDFA_OPTIMIZE` to 2 or 3
- Increase `PDFA_JBIG2_PAGE_GROUP_SIZE` to 20-50

### Processing too slow
- Use `PDFA_OPTIMIZE=1`
- Reduce `PDFA_IMAGE_DPI`
- Reduce `PDFA_JBIG2_PAGE_GROUP_SIZE`

## Further Information

- [OCRmyPDF Documentation](https://ocrmypdf.readthedocs.io/)
- [JBIG2 Compression](https://en.wikipedia.org/wiki/JBIG2)
- [PDF/A Standards](https://www.pdfa.org/)
