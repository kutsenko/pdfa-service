#!/usr/bin/env bash

#############################################################################
# curl-examples.sh
#
# Common curl examples for interacting with the pdfa-service REST API.
# Copy and modify these commands for your use case.
#
# Prerequisites:
#   - pdfa-service API running (default: http://localhost:8000)
#   - curl installed
#   - Sample PDF/Office documents in current directory
#
#############################################################################

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}PDFa-Service curl Examples${NC}\n"

#############################################################################
# Example 1: Convert a PDF file
#############################################################################

echo -e "${YELLOW}Example 1: Convert a PDF file${NC}"
echo "Convert a PDF to PDF/A with German+English OCR"
echo ""
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"language=deu+eng\" \\"
echo "  -F \"pdfa_level=2\" \\"
echo "  --output output-pdfa.pdf"
echo ""
echo "# Save output to file with timestamp"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  --output \"output-\$(date +%Y%m%d_%H%M%S).pdf\""
echo ""

#############################################################################
# Example 2: Convert Office documents
#############################################################################

echo -e "${YELLOW}Example 2: Convert Office documents${NC}"
echo ""
echo "# Word document (DOCX)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@document.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document\" \\"
echo "  --output document-pdfa.pdf"
echo ""
echo "# PowerPoint presentation (PPTX)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@presentation.pptx;type=application/vnd.openxmlformats-officedocument.presentationml.presentation\" \\"
echo "  --output presentation-pdfa.pdf"
echo ""
echo "# Excel spreadsheet (XLSX)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@spreadsheet.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\" \\"
echo "  --output spreadsheet-pdfa.pdf"
echo ""

#############################################################################
# Example 3: Different PDF/A compliance levels
#############################################################################

echo -e "${YELLOW}Example 3: Different PDF/A compliance levels${NC}"
echo ""
echo "# PDF/A-1 (most restrictive, maximum compatibility)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"pdfa_level=1\" \\"
echo "  --output output-pdfa1.pdf"
echo ""
echo "# PDF/A-2 (default, good balance)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"pdfa_level=2\" \\"
echo "  --output output-pdfa2.pdf"
echo ""
echo "# PDF/A-3 (most flexible, allows embedding additional files)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"pdfa_level=3\" \\"
echo "  --output output-pdfa3.pdf"
echo ""

#############################################################################
# Example 4: Different languages and OCR
#############################################################################

echo -e "${YELLOW}Example 4: OCR with different languages${NC}"
echo ""
echo "# English only"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"language=eng\" \\"
echo "  --output output-pdfa.pdf"
echo ""
echo "# Multiple languages (German + English)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"language=deu+eng\" \\"
echo "  --output output-pdfa.pdf"
echo ""
echo "# French + Spanish + Portuguese"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"language=fra+spa+por\" \\"
echo "  --output output-pdfa.pdf"
echo ""
echo "# Disable OCR (faster, for already text-searchable PDFs)"
echo "curl -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"ocr_enabled=false\" \\"
echo "  --output output-pdfa.pdf"
echo ""

#############################################################################
# Example 5: Batch processing with loops
#############################################################################

echo -e "${YELLOW}Example 5: Batch processing all PDFs in directory${NC}"
echo ""
echo "# Convert all PDFs, save with -pdfa.pdf suffix"
echo "for file in *.pdf; do"
echo "  output=\"\${file%.*}-pdfa.pdf\""
echo "  echo \"Converting: \$file -> \$output\""
echo "  curl -s -X POST \"http://localhost:8000/convert\" \\"
echo "    -F \"file=@\${file};type=application/pdf\" \\"
echo "    -F \"language=deu+eng\" \\"
echo "    --output \"\$output\""
echo "done"
echo ""

#############################################################################
# Example 6: Batch processing mixed formats
#############################################################################

echo -e "${YELLOW}Example 6: Batch processing mixed formats (PDF, DOCX, PPTX, XLSX)${NC}"
echo ""
echo "# Convert all supported formats"
echo "for file in *.{pdf,docx,pptx,xlsx}; do"
echo "  [ ! -f \"\$file\" ] && continue"
echo "  output=\"\${file%.*}-pdfa.pdf\""
echo "  mime=\"application/pdf\""
echo "  "
echo "  case \"\${file##*.}\" in"
echo "    pdf) mime=\"application/pdf\" ;;"
echo "    docx) mime=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document\" ;;"
echo "    pptx) mime=\"application/vnd.openxmlformats-officedocument.presentationml.presentation\" ;;"
echo "    xlsx) mime=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\" ;;"
echo "  esac"
echo "  "
echo "  echo \"Converting: \$file -> \$output\""
echo "  curl -s -X POST \"http://localhost:8000/convert\" \\"
echo "    -F \"file=@\${file};type=\${mime}\" \\"
echo "    --output \"\$output\""
echo "done"
echo ""

#############################################################################
# Example 7: Recursive directory conversion
#############################################################################

echo -e "${YELLOW}Example 7: Recursively convert all PDFs in directory tree${NC}"
echo ""
echo "find /path/to/documents -name \"*.pdf\" -type f | while read file; do"
echo "  output=\"\${file%.*}-pdfa.pdf\""
echo "  echo \"Converting: \$file\""
echo "  curl -s -X POST \"http://localhost:8000/convert\" \\"
echo "    -F \"file=@\${file};type=application/pdf\" \\"
echo "    --output \"\$output\""
echo "done"
echo ""

#############################################################################
# Example 8: Parallel processing with xargs
#############################################################################

echo -e "${YELLOW}Example 8: Parallel processing with xargs (4 concurrent conversions)${NC}"
echo ""
echo "find /path/to/documents -name \"*.pdf\" -type f | \\"
echo "  xargs -P 4 -I {} bash -c '"
echo "    file=\"{}\""
echo "    output=\"\${file%.*}-pdfa.pdf\""
echo "    curl -s -X POST \"http://localhost:8000/convert\" \\"
echo "      -F \"file=@\${file};type=application/pdf\" \\"
echo "      --output \"\$output\""
echo "  '"
echo ""

#############################################################################
# Example 9: Error handling with status codes
#############################################################################

echo -e "${YELLOW}Example 9: Error handling and status codes${NC}"
echo ""
echo "# Check HTTP status code"
echo "http_code=\$(curl -s -w '%{http_code}' -o output.pdf \\"
echo "  -X POST \"http://localhost:8000/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\")"
echo ""
echo "if [ \"\$http_code\" == \"200\" ]; then"
echo "  echo \"Conversion successful\""
echo "else"
echo "  echo \"Conversion failed with HTTP \$http_code\""
echo "fi"
echo ""

#############################################################################
# Example 10: Using remote API server
#############################################################################

echo -e "${YELLOW}Example 10: Using remote API server${NC}"
echo ""
echo "# Replace localhost with your API server"
echo "API_SERVER=\"http://pdfa-api.example.com:8000\""
echo ""
echo "curl -X POST \"\${API_SERVER}/convert\" \\"
echo "  -F \"file=@input.pdf;type=application/pdf\" \\"
echo "  -F \"language=deu+eng\" \\"
echo "  --output output-pdfa.pdf"
echo ""

#############################################################################
# Example 11: Progress indication
#############################################################################

echo -e "${YELLOW}Example 11: Batch processing with progress indication${NC}"
echo ""
echo "total=\$(find /path/to/documents -name \"*.pdf\" | wc -l)"
echo "count=0"
echo ""
echo "find /path/to/documents -name \"*.pdf\" | while read file; do"
echo "  ((count++))"
echo "  output=\"\${file%.*}-pdfa.pdf\""
echo "  echo \"[\$count/\$total] Converting: \$(basename \"\$file\")\""
echo "  curl -s -X POST \"http://localhost:8000/convert\" \\"
echo "    -F \"file=@\${file};type=application/pdf\" \\"
echo "    --output \"\$output\""
echo "done"
echo ""

#############################################################################
# Example 12: Large batch processing with logging
#############################################################################

echo -e "${YELLOW}Example 12: Large batch processing with detailed logging${NC}"
echo ""
echo "LOG_FILE=\"conversion-\$(date +%Y%m%d_%H%M%S).log\""
echo ""
echo "find /path/to/documents -type f \\"
echo "  -name \"*.pdf\" -o -name \"*.docx\" -o -name \"*.pptx\" -o -name \"*.xlsx\" | while read file; do"
echo "  output=\"\${file%.*}-pdfa.pdf\""
echo "  echo \"[$(date '+%Y-%m-%d %H:%M:%S')] Processing: \$file\" | tee -a \"\$LOG_FILE\""
echo "  "
echo "  if curl -s -X POST \"http://localhost:8000/convert\" \\"
echo "    -F \"file=@\${file};type=application/pdf\" \\"
echo "    --output \"\$output\" 2>/dev/null; then"
echo "    echo \"[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Success: \$output\" | tee -a \"\$LOG_FILE\""
echo "  else"
echo "    echo \"[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Failed: \$file\" | tee -a \"\$LOG_FILE\""
echo "  fi"
echo "done"
echo ""

echo -e "${GREEN}For production use, see: scripts/batch-convert.sh${NC}"
echo ""
