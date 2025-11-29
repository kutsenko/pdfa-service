# Batch Conversion Script

The `batch-convert.sh` script provides a robust, production-ready solution for converting multiple PDF and Office documents to PDF/A format using the pdfa-service REST API.

## Features

- **Recursive directory scanning**: Automatically finds all supported document formats
- **Parallel processing**: Convert multiple files concurrently for better performance
- **Error handling**: Robust error recovery with detailed logging
- **Progress tracking**: Real-time feedback on conversion status
- **Flexible configuration**: Customizable API endpoint, languages, and PDF/A levels
- **Dry-run mode**: Preview conversions without modifying files
- **Comprehensive logging**: Detailed logs saved to file for auditing and debugging

## Supported Formats

### PDF
- PDF (`.pdf`)

### MS Office Formats
- Word documents (`.docx`)
- PowerPoint presentations (`.pptx`)
- Excel spreadsheets (`.xlsx`)

### OpenDocument Formats (ODF)
- OpenDocument Text (`.odt`)
- OpenDocument Presentation (`.odp`)
- OpenDocument Spreadsheet (`.ods`)

## Requirements

- Bash 4.0+
- `curl` command-line tool
- `file` utility (for PDF validation)
- Running pdfa-service API

### Verify Requirements

```bash
# Check Bash version
bash --version

# Verify curl is installed
curl --version

# Verify file utility
file --version
```

## Installation

The script is included in the repository. Make it executable:

```bash
chmod +x scripts/batch-convert.sh
```

## Quick Start

Convert all documents in a directory (recursively):

```bash
./scripts/batch-convert.sh /path/to/documents
```

The script will:
1. Scan the directory recursively for supported formats
2. Convert each file to PDF/A format
3. Save the result with `-pdfa.pdf` suffix next to the original file
4. Display progress and a summary at the end

## Usage

```
./batch-convert.sh DIRECTORY [OPTIONS]

Options:
  --api-url URL              API endpoint (default: http://localhost:8000)
  --language LANG            Tesseract language codes (default: deu+eng)
  --pdfa-level LEVEL         PDF/A compliance level: 1, 2, or 3 (default: 2)
  --workers N                Number of parallel workers (default: 4)
  --dry-run                  Preview files without converting
  --output-suffix SUFFIX     Output file suffix (default: -pdfa.pdf)
  --log-file FILE            Write logs to file (default: batch-convert.log)
  --no-log                   Disable file logging
  --debug                    Enable debug output
  --help                     Show help message
```

## Examples

### Basic Usage

Convert all documents in the current directory:

```bash
./scripts/batch-convert.sh .
```

Convert all documents in a specific directory:

```bash
./scripts/batch-convert.sh /home/user/Documents
```

### Custom Configuration

Convert with custom language and PDF/A level:

```bash
./scripts/batch-convert.sh /path/to/documents \
  --language "eng+fra" \
  --pdfa-level "3"
```

Convert using a remote API server:

```bash
./scripts/batch-convert.sh /path/to/documents \
  --api-url "http://pdfa-api.example.com:8000"
```

### Parallel Processing

Use 8 workers for faster processing on multi-core systems:

```bash
./scripts/batch-convert.sh /path/to/documents --workers 8
```

For sequential processing (single worker):

```bash
./scripts/batch-convert.sh /path/to/documents --workers 1
```

### Dry-Run Mode

Preview what would be converted without making changes:

```bash
./scripts/batch-convert.sh /path/to/documents --dry-run
```

Output example:

```
[2024-01-15 14:30:45] [INFO] === PDF/A Batch Conversion Started ===
[2024-01-15 14:30:45] [INFO] Input directory: /home/user/documents
[2024-01-15 14:30:45] [INFO] Mode: DRY-RUN (no files will be converted)
[2024-01-15 14:30:46] [SUCCESS] Found 42 file(s) to process
[2024-01-15 14:30:46] [INFO] [1/42] [DRY-RUN] Would convert: /home/user/documents/report.pdf -> report-pdfa.pdf
[2024-01-15 14:30:46] [INFO] [2/42] [DRY-RUN] Would convert: /home/user/documents/letter.docx -> letter-pdfa.pdf
...
```

### Custom Output Suffix

Use a different naming convention:

```bash
./scripts/batch-convert.sh /path/to/documents \
  --output-suffix "_archived.pdf"
```

Files will be saved as `document_archived.pdf` instead of `document-pdfa.pdf`.

### Logging

Save logs to a custom file:

```bash
./scripts/batch-convert.sh /path/to/documents \
  --log-file "/var/log/pdfa-conversions.log"
```

Disable file logging (console only):

```bash
./scripts/batch-convert.sh /path/to/documents --no-log
```

### Debug Mode

Enable verbose debug output:

```bash
./scripts/batch-convert.sh /path/to/documents --debug
```

## Output

The script creates a summary after processing:

```
╔════════════════════════════════════════╗
║          CONVERSION SUMMARY            ║
╠════════════════════════════════════════╣
║ Total files found:      42
║ Successfully converted: 40
║ Failed:                  1
║ Skipped:                 1
║ Duration:               2m 34s
╚════════════════════════════════════════╝

Detailed logs saved to: batch-convert.log
```

### Exit Codes

- **0**: All files processed successfully (no failures)
- **1**: One or more files failed to convert

## Real-World Scenarios

### Scenario 1: Archive Large Document Collection

Convert 500+ documents in a corporate archive with OCR:

```bash
./scripts/batch-convert.sh /mnt/archive/documents \
  --language "deu+eng" \
  --pdfa-level "2" \
  --workers 6 \
  --log-file "/var/log/archive-conversion.log"
```

### Scenario 2: Convert Office and OpenDocument Documents

Convert all MS Office and OpenDocument files to PDF/A with English OCR:

```bash
./scripts/batch-convert.sh /home/user/Documents \
  --language "eng" \
  --pdfa-level "2"
```

Supported formats include:
- MS Office: DOCX, PPTX, XLSX
- OpenDocument: ODT, ODS, ODP
- PDF files

Other file types are skipped.

### Scenario 3: Process Multiple Directories

Create a wrapper script to process multiple directories:

```bash
#!/bin/bash
# process-all.sh

DIRS=(
  "/path/to/dir1"
  "/path/to/dir2"
  "/path/to/dir3"
)

for dir in "${DIRS[@]}"; do
  ./scripts/batch-convert.sh "$dir" \
    --log-file "batch-convert-$(basename "$dir").log"
done
```

### Scenario 4: Integration with Cron

Schedule automatic conversions of new documents:

```bash
# Process new documents daily at 2 AM
0 2 * * * cd /home/pdfa && ./scripts/batch-convert.sh /home/pdfa/inbox \
  --log-file /var/log/pdfa/daily-conversion.log
```

### Scenario 5: Docker-based Conversion

Use the script inside a Docker container:

```bash
docker run --rm -v /data:/data \
  pdfa-service:latest \
  /app/scripts/batch-convert.sh /data/input \
  --log-file /data/conversion.log
```

## Performance Tips

1. **Parallel Workers**: The default is 4 workers. Adjust based on:
   - System CPU cores: `--workers $(nproc)`
   - Available RAM (each worker uses ~100-200MB)
   - Network bandwidth to API server

2. **API Performance**: For remote API servers, consider:
   - Running the API with multiple uvicorn workers
   - Using a reverse proxy (nginx) with load balancing
   - Increasing `--workers` to match server capacity

3. **Large Files**: For documents >100MB:
   - Use fewer workers to avoid memory pressure
   - Consider increasing API server timeouts
   - Monitor server resource usage

4. **Network**: For remote conversions:
   - Use compression if the API supports it
   - Consider running API locally when possible
   - Monitor network bandwidth usage

## Troubleshooting

### "Cannot connect to API"

Ensure the pdfa-service is running:

```bash
# Check if API is running locally
curl http://localhost:8000/docs

# If using remote server, verify connectivity
curl http://api-server:8000/docs
```

Start the API if needed:

```bash
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000
```

### "Conversion failed" Errors

1. Check the detailed logs:

```bash
tail -f batch-convert.log
```

2. Test API directly:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@problem-file.pdf" \
  -F "language=deu+eng"
```

3. Check system dependencies are installed:

```bash
# Ubuntu
sudo apt install tesseract-ocr ghostscript qpdf
```

### High Memory Usage

Reduce parallel workers:

```bash
./scripts/batch-convert.sh /path/to/documents --workers 1
```

### Slow Conversions

Monitor API performance and increase workers if resources allow:

```bash
# Check API server resource usage
top -p $(pgrep -f "uvicorn.*api")

# Try more workers if CPU is not maxed out
./scripts/batch-convert.sh /path/to/documents --workers 8
```

## Advanced Usage

### Integration with File Monitoring

Automatically convert new files as they arrive:

```bash
#!/bin/bash
# watch-and-convert.sh

watch_dir="/home/user/incoming"
archive_dir="/home/user/converted"

while true; do
  if ls "$watch_dir"/*.{pdf,docx,pptx,xlsx} 2>/dev/null | grep -q .; then
    ./scripts/batch-convert.sh "$watch_dir" \
      --log-file "/var/log/watch-convert.log"

    # Move converted directory
    mkdir -p "$archive_dir"
    find "$watch_dir" -name "*-pdfa.pdf" -exec mv {} "$archive_dir" \;
  fi

  sleep 60
done
```

### Filter by File Type

Process only PDFs:

```bash
find /path/to/documents -name "*.pdf" | while read file; do
  output="${file%.*}-pdfa.pdf"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    -F "language=deu+eng" \
    --output "$output"
done
```

## License

This script is part of the pdfa-service project and follows the same license.

## Support

For issues or feature requests related to this script, please refer to the main [README.md](../README.md) and project documentation.
