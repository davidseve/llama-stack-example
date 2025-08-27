#!/bin/bash

# LlamaStack Validation Runner
# This script helps run the enhanced LlamaStack validation with proper environment setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_usage() {
    echo "LlamaStack Validation Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --url URL                 LlamaStack URL (required)"
    echo "  --token TOKEN             API token (optional)"
    echo "  --timeout SECONDS         Request timeout (default: 30)"
    echo "  --json-output FILE        Save results to JSON file"
    echo "  --skip-ssl-verify        Skip SSL certificate verification"
    echo "  --verbose, -v            Enable verbose error reporting with full stack traces"
    echo "  --basic                  Run basic validation (recommended)"
    echo "  --install-deps           Install required dependencies"
    echo "  --help                   Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  LLAMASTACK_URL           Default LlamaStack URL"
    echo "  LLAMASTACK_TOKEN         Default API token"
    echo "  VLLM_URL                 VLLM inference URL"
    echo "  MCP_URL                  MCP service URL"
    echo ""
    echo "Examples:"
    echo "  $0 --url http://localhost:8321"
    echo "  $0 --url http://llamastack-service:8321 --token my-token"
    echo "  $0 --url https://llamastack.apps.example.com --skip-ssl-verify"
    echo "  $0 --url http://llamastack-service:8321 --json-output results.json"
    echo "  $0 --url http://llamastack-service:8321 --verbose"
}

# Default values
URL="${LLAMASTACK_URL:-}"
TOKEN="${LLAMASTACK_TOKEN:-}"
TIMEOUT=30
JSON_OUTPUT=""
SKIP_SSL_VERIFY=false
VERBOSE=false
BASIC_MODE=false
INSTALL_DEPS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            URL="$2"
            shift 2
            ;;
        --token)
            TOKEN="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --json-output)
            JSON_OUTPUT="$2"
            shift 2
            ;;
        --skip-ssl-verify)
            SKIP_SSL_VERIFY=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --basic)
            BASIC_MODE=true
            shift
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Check if URL is provided
if [ -z "$URL" ]; then
    print_error "LlamaStack URL is required. Use --url or set LLAMASTACK_URL environment variable."
    print_usage
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Choose validation script based on mode
if [ "$BASIC_MODE" = true ]; then
    VALIDATION_SCRIPT="$SCRIPT_DIR/validate_basic.py"
else
    VALIDATION_SCRIPT="$SCRIPT_DIR/validate_llamastack_enhanced.py"
fi

# Check if validation script exists
if [ ! -f "$VALIDATION_SCRIPT" ]; then
    print_error "Validation script not found: $VALIDATION_SCRIPT"
    exit 1
fi

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    print_info "Installing required dependencies..."
    
    # Check if pip is available
    if ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install pip first."
        exit 1
    fi
    
    # Install llama-stack-client
    pip install llama-stack-client
    
    print_success "Dependencies installed successfully"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "python3 not found. Please install Python 3."
    exit 1
fi

# Build command
CMD="python3 $VALIDATION_SCRIPT --url $URL"

# Add timeout only for enhanced script
if [ "$BASIC_MODE" != true ]; then
    CMD="$CMD --timeout $TIMEOUT"
fi

if [ -n "$TOKEN" ]; then
    CMD="$CMD --token $TOKEN"
fi

if [ -n "$JSON_OUTPUT" ]; then
    CMD="$CMD --json-output $JSON_OUTPUT"
fi

if [ "$SKIP_SSL_VERIFY" = true ]; then
    CMD="$CMD --skip-ssl-verify"
fi

if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Display environment info
print_info "=========================================="
print_info "LlamaStack Validation Runner"
print_info "=========================================="
print_info "Target URL: $URL"
if [ -n "$TOKEN" ]; then
    print_info "Using API Token: ${TOKEN:0:10}..."
else
    print_info "No API Token provided"
fi
print_info "Timeout: ${TIMEOUT}s"
if [ -n "$JSON_OUTPUT" ]; then
    print_info "JSON Output: $JSON_OUTPUT"
fi
if [ "$SKIP_SSL_VERIFY" = true ]; then
    print_info "SSL Verification: DISABLED (--skip-ssl-verify)"
fi
if [ "$VERBOSE" = true ]; then
    print_info "Verbose Mode: ENABLED (detailed error reporting)"
fi
if [ "$BASIC_MODE" = true ]; then
    print_info "Validation Mode: BASIC (recommended for initial testing)"
else
    print_info "Validation Mode: ENHANCED (comprehensive testing)"
fi

# Show environment variables for reference
echo ""
print_info "Environment Variables:"
if [ -n "$VLLM_URL" ]; then
    print_info "  VLLM_URL: $VLLM_URL"
fi
if [ -n "$MCP_URL" ]; then
    print_info "  MCP_URL: $MCP_URL"
fi

echo ""

# Run validation
print_info "Running validation..."
print_info "Command: $CMD"
echo ""

exec $CMD
