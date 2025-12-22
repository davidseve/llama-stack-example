#!/bin/bash
# =============================================================================
# Run All RAG Examples
# =============================================================================
# This script executes both RAG examples in sequence:
#   1. rag-evaluation-ragas - RAG evaluation with RAGAS metrics
#   2. rag-mcp-chatbot - Chatbot with RAG + MCP tools
#
# Usage:
#   ./run_all.sh                    # Run all examples (RAGAS inline mode)
#   ./run_all.sh --skip-mcp         # Skip rag-mcp-chatbot
#   ./run_all.sh --skip-evaluation  # Skip rag-evaluation-ragas
#   ./run_all.sh --dry-run          # Show what would be executed
#   RAGAS_MODE=remote ./run_all.sh  # Use RAGAS remote mode (requires DSPA)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Load configuration from examples/.env
if [ -f "$EXAMPLES_DIR/.env" ]; then
    set -a
    source "$EXAMPLES_DIR/.env"
    set +a
else
    echo -e "${YELLOW}[INFO]${NC} No .env found. Copy env.template to .env:"
    echo "   cp $EXAMPLES_DIR/env.template $EXAMPLES_DIR/.env"
fi

# Options
SKIP_MCP=false
SKIP_EVALUATION=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-mcp)
            SKIP_MCP=true
            shift
            ;;
        --skip-evaluation)
            SKIP_EVALUATION=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-mcp          Skip rag-mcp-chatbot example"
            echo "  --skip-evaluation   Skip rag-evaluation-ragas example"
            echo "  --dry-run           Show what would be executed without running"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  RAGAS_MODE          Evaluation mode: 'inline' (default) or 'remote' (requires DSPA)"
            echo ""
            echo "Examples:"
            echo "  $0                        # Run all with inline RAGAS mode"
            echo "  RAGAS_MODE=remote $0      # Run all with remote RAGAS mode"
            echo "  $0 --skip-evaluation      # Run only chatbot, skip RAGAS"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
print_header() {
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_example() {
    local name=$1
    local dir=$2
    local script=$3
    
    print_header "Running: $name"
    print_info "Directory: $dir"
    print_info "Script: $script"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY-RUN] Would execute: cd $dir && ./$script"
        return 0
    fi
    
    if [ ! -d "$dir" ]; then
        print_error "Directory not found: $dir"
        return 1
    fi
    
    if [ ! -f "$dir/$script" ]; then
        print_error "Script not found: $dir/$script"
        return 1
    fi
    
    cd "$dir"
    chmod +x "$script"
    if ! ./"$script"; then
        print_error "$name failed!"
        return 1
    fi
    
    print_success "$name completed!"
}

# =============================================================================
# Main
# =============================================================================

print_header "🚀 RAG EXAMPLES TEST RUNNER"

echo -e "${BLUE}Examples directory:${NC} $EXAMPLES_DIR"
echo -e "${BLUE}Skip MCP:${NC} $SKIP_MCP"
echo -e "${BLUE}Skip Evaluation:${NC} $SKIP_EVALUATION"
echo -e "${BLUE}RAGAS Mode:${NC} ${RAGAS_MODE:-inline}"
echo -e "${BLUE}Dry run:${NC} $DRY_RUN"
echo ""

EXAMPLES_RUN=0
EXAMPLES_FAILED=0

# -----------------------------------------------------------------------------
# Example 1: rag-evaluation-ragas
# -----------------------------------------------------------------------------
if [ "$SKIP_EVALUATION" = false ]; then
    if run_example \
        "RAG Evaluation with RAGAS" \
        "$EXAMPLES_DIR/rag-evaluation-ragas" \
        "run_example.sh"; then
        EXAMPLES_RUN=$((EXAMPLES_RUN + 1))
    else
        EXAMPLES_FAILED=$((EXAMPLES_FAILED + 1))
        print_error "rag-evaluation-ragas failed!"
    fi
else
    print_info "Skipping rag-evaluation-ragas (--skip-evaluation)"
fi

# -----------------------------------------------------------------------------
# Example 2: rag-mcp-chatbot
# -----------------------------------------------------------------------------
if [ "$SKIP_MCP" = false ]; then
    if run_example \
        "RAG + MCP Chatbot" \
        "$EXAMPLES_DIR/rag-mcp-chatbot" \
        "run_example.sh"; then
        EXAMPLES_RUN=$((EXAMPLES_RUN + 1))
    else
        EXAMPLES_FAILED=$((EXAMPLES_FAILED + 1))
        print_error "rag-mcp-chatbot failed!"
    fi
else
    print_info "Skipping rag-mcp-chatbot (--skip-mcp)"
fi

# =============================================================================
# Summary
# =============================================================================

print_header "📊 SUMMARY"

echo -e "${GREEN}Examples run:${NC} $EXAMPLES_RUN"
echo -e "${RED}Examples failed:${NC} $EXAMPLES_FAILED"
echo ""

if [ $EXAMPLES_FAILED -eq 0 ]; then
    print_success "🎉 All examples completed successfully!"
    exit 0
else
    print_error "Some examples failed. Check the output above."
    exit 1
fi

