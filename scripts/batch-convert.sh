#!/usr/bin/env bash

#############################################################################
# batch-convert.sh
#
# Batch convert PDF and Office documents to PDF/A format using the pdfa-service
# REST API. Supports recursive directory scanning, parallel processing, and
# error handling with detailed logging.
#
# Usage:
#   ./batch-convert.sh /path/to/documents [OPTIONS]
#
# Options:
#   --api-url URL              API endpoint (default: http://localhost:8000)
#   --language LANG            Tesseract language codes (default: deu+eng)
#   --pdfa-level LEVEL         PDF/A compliance level: 1, 2, or 3 (default: 2)
#   --workers N                Number of parallel workers (default: 4)
#   --dry-run                  Preview files without converting
#   --output-suffix SUFFIX     Output file suffix (default: -pdfa.pdf)
#   --log-file FILE            Write logs to file (default: batch-convert.log)
#   --no-log                   Disable file logging
#   --help                     Show this help message
#
# Examples:
#   # Convert all documents in directory (recursive)
#   ./batch-convert.sh /path/to/documents
#
#   # Custom API server and language
#   ./batch-convert.sh /path/to/documents \
#     --api-url "http://api-server:8000" \
#     --language "eng+fra"
#
#   # Dry-run to preview what would be converted
#   ./batch-convert.sh /path/to/documents --dry-run
#
#   # Single worker for serial processing
#   ./batch-convert.sh /path/to/documents --workers 1
#
#############################################################################

set -o pipefail

# Default configuration
API_URL="http://localhost:8000"
LANGUAGE="deu+eng"
PDFA_LEVEL="2"
WORKERS=4
DRY_RUN=false
OUTPUT_SUFFIX="-pdfa.pdf"
LOG_FILE="batch-convert.log"
ENABLE_FILE_LOG=true
TEMP_DIR=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Statistics
TOTAL_FILES=0
CONVERTED=0
FAILED=0
SKIPPED=0
START_TIME=""

# Colors for output (disable if not a terminal)
if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  NC='\033[0m' # No Color
else
  RED=""
  GREEN=""
  YELLOW=""
  BLUE=""
  NC=""
fi

#############################################################################
# Helper Functions
#############################################################################

log() {
  local level="$1"
  shift
  local message="$@"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local log_message="[$timestamp] [$level] $message"

  # Console output
  case "$level" in
    INFO)
      echo -e "${BLUE}${log_message}${NC}"
      ;;
    SUCCESS)
      echo -e "${GREEN}${log_message}${NC}"
      ;;
    WARN)
      echo -e "${YELLOW}${log_message}${NC}"
      ;;
    ERROR)
      echo -e "${RED}${log_message}${NC}"
      ;;
    DEBUG)
      [[ "$DEBUG" == "1" ]] && echo -e "${BLUE}${log_message}${NC}"
      ;;
    *)
      echo "$log_message"
      ;;
  esac

  # File logging
  if [[ "$ENABLE_FILE_LOG" == "true" ]]; then
    echo "$log_message" >> "$LOG_FILE"
  fi
}

debug() {
  [[ "$DEBUG" == "1" ]] && log DEBUG "$@"
}

error() {
  log ERROR "$@" >&2
}

get_mime_type() {
  local file="$1"
  local ext="${file##*.}"
  ext="${ext,,}" # Convert to lowercase

  case "$ext" in
    pdf)
      echo "application/pdf"
      ;;
    docx)
      echo "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ;;
    pptx)
      echo "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      ;;
    xlsx)
      echo "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ;;
    *)
      echo ""
      ;;
  esac
}

is_supported_format() {
  local file="$1"
  local mime=$(get_mime_type "$file")
  [[ -n "$mime" ]]
}

convert_file() {
  local file="$1"
  local output_file="$2"

  if [[ "$DRY_RUN" == "true" ]]; then
    log INFO "[$((CONVERTED + FAILED + SKIPPED + 1))/$TOTAL_FILES] [DRY-RUN] Would convert: $file -> $output_file"
    return 0
  fi

  local mime=$(get_mime_type "$file")
  local filename=$(basename "$file")

  log INFO "Converting [$((CONVERTED + FAILED + SKIPPED + 1))/$TOTAL_FILES]: $filename -> $(basename "$output_file")"

  local http_code
  local error_output
  local temp_output

  temp_output=$(mktemp)
  trap "rm -f '$temp_output'" RETURN

  http_code=$(curl -s -w "%{http_code}" \
    -X POST "$API_URL/convert" \
    -F "file=@$file;type=$mime" \
    -F "language=$LANGUAGE" \
    -F "pdfa_level=$PDFA_LEVEL" \
    -o "$temp_output" 2>&1)

  if [[ "$http_code" == "200" ]]; then
    # Check if output file is a valid PDF
    if file "$temp_output" | grep -q "PDF"; then
      mv "$temp_output" "$output_file"
      log SUCCESS "Converted: $filename (size: $(numfmt --to=iec-i --suffix=B $(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file") 2>/dev/null || stat -c%s "$output_file"))"
      return 0
    else
      error_output=$(cat "$temp_output")
      error "Conversion returned invalid PDF: $filename (response: ${error_output:0:100})"
      rm -f "$temp_output"
      return 1
    fi
  else
    error_output=$(cat "$temp_output")
    error "Conversion failed for $filename (HTTP $http_code): ${error_output:0:150}"
    rm -f "$temp_output"
    return 1
  fi
}

process_file() {
  local file="$1"

  # Validate file exists and is readable
  if [[ ! -r "$file" ]]; then
    error "File not readable: $file"
    ((FAILED++))
    return 1
  fi

  # Check if format is supported
  if ! is_supported_format "$file"; then
    debug "Skipping unsupported format: $file"
    ((SKIPPED++))
    return 0
  fi

  local dir=$(dirname "$file")
  local filename=$(basename "$file")
  local base="${filename%.*}"
  local output_file="$dir/$base$OUTPUT_SUFFIX"

  # Skip if output already exists
  if [[ -f "$output_file" ]]; then
    log WARN "Output file already exists, skipping: $output_file"
    ((SKIPPED++))
    return 0
  fi

  if convert_file "$file" "$output_file"; then
    ((CONVERTED++))
    return 0
  else
    ((FAILED++))
    return 1
  fi
}

find_files() {
  local directory="$1"
  find "$directory" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" -o -name "*.xlsx" \)
}

show_help() {
  sed -n '/^#############################################################################/,/^#############################################################################/{
    /^# /!d
    s/^# //
    s/^#$//
    p
  }' "$0" | tail -n +2
}

validate_api() {
  log INFO "Validating API connection to $API_URL..."

  local http_code=$(curl -s -w "%{http_code}" -o /dev/null "$API_URL/docs" 2>/dev/null)

  if [[ "$http_code" != "200" ]]; then
    if [[ "$http_code" == "000" ]]; then
      error "Cannot connect to API at $API_URL. Is the service running?"
    else
      error "API returned HTTP $http_code"
    fi
    return 1
  fi

  log SUCCESS "API connection OK"
  return 0
}

print_summary() {
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
  local minutes=$((duration / 60))
  local seconds=$((duration % 60))

  echo ""
  echo "╔════════════════════════════════════════╗"
  echo "║          CONVERSION SUMMARY            ║"
  echo "╠════════════════════════════════════════╣"
  echo "║ Total files found:      $((TOTAL_FILES))"
  echo "║ Successfully converted: $(printf '%2d' $CONVERTED)"
  echo "║ Failed:                 $(printf '%2d' $FAILED)"
  echo "║ Skipped:                $(printf '%2d' $SKIPPED)"
  echo "║ Duration:               ${minutes}m ${seconds}s"
  echo "╚════════════════════════════════════════╝"
  echo ""

  if [[ "$ENABLE_FILE_LOG" == "true" ]]; then
    echo "Detailed logs saved to: $LOG_FILE"
  fi

  # Return appropriate exit code
  if [[ $FAILED -gt 0 ]]; then
    return 1
  fi
  return 0
}

cleanup() {
  if [[ -n "$TEMP_DIR" ]] && [[ -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}

#############################################################################
# Main Script
#############################################################################

main() {
  local input_dir=""

  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help)
        show_help
        exit 0
        ;;
      --api-url)
        API_URL="$2"
        shift 2
        ;;
      --language)
        LANGUAGE="$2"
        shift 2
        ;;
      --pdfa-level)
        PDFA_LEVEL="$2"
        shift 2
        ;;
      --workers)
        WORKERS="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --output-suffix)
        OUTPUT_SUFFIX="$2"
        shift 2
        ;;
      --log-file)
        LOG_FILE="$2"
        shift 2
        ;;
      --no-log)
        ENABLE_FILE_LOG=false
        shift
        ;;
      --debug)
        DEBUG=1
        shift
        ;;
      -*)
        error "Unknown option: $1"
        echo ""
        show_help
        exit 1
        ;;
      *)
        if [[ -z "$input_dir" ]]; then
          input_dir="$1"
        else
          error "Too many positional arguments"
          exit 1
        fi
        shift
        ;;
    esac
  done

  # Validate input directory
  if [[ -z "$input_dir" ]]; then
    error "Error: Input directory required"
    echo ""
    show_help
    exit 1
  fi

  if [[ ! -d "$input_dir" ]]; then
    error "Error: Directory not found: $input_dir"
    exit 1
  fi

  # Normalize path
  input_dir=$(cd "$input_dir" && pwd)

  # Setup cleanup trap
  trap cleanup EXIT

  # Log header
  log INFO "=== PDF/A Batch Conversion Started ==="
  log INFO "Input directory: $input_dir"
  log INFO "API endpoint: $API_URL"
  log INFO "Language: $LANGUAGE"
  log INFO "PDF/A level: $PDFA_LEVEL"
  log INFO "Parallel workers: $WORKERS"
  [[ "$DRY_RUN" == "true" ]] && log INFO "Mode: DRY-RUN (no files will be converted)"

  # Validate API connection
  if ! validate_api; then
    exit 1
  fi

  # Find files
  log INFO "Scanning directory for supported formats..."
  local files_array=()
  while IFS= read -r file; do
    files_array+=("$file")
  done < <(find_files "$input_dir")

  TOTAL_FILES=${#files_array[@]}

  if [[ $TOTAL_FILES -eq 0 ]]; then
    log WARN "No supported files found in: $input_dir"
    exit 0
  fi

  log SUCCESS "Found $TOTAL_FILES file(s) to process"

  # Start processing
  START_TIME=$(date +%s)
  echo ""

  if [[ $WORKERS -gt 1 ]]; then
    log INFO "Processing with $WORKERS parallel workers..."

    # Create named pipes for job queue
    local job_queue=$(mktemp -u)
    mkfifo "$job_queue"
    exec 3<>"$job_queue"
    rm "$job_queue"

    # Initialize worker pool
    for ((i = 1; i <= WORKERS; i++)); do
      echo "" >&3
    done

    # Process files in parallel
    for file in "${files_array[@]}"; do
      read -u 3
      {
        process_file "$file"
        echo >&3
      } &
    done

    wait
    exec 3>&-
  else
    # Serial processing
    log INFO "Processing files sequentially..."
    for file in "${files_array[@]}"; do
      process_file "$file"
    done
  fi

  echo ""
  print_summary
}

main "$@"
