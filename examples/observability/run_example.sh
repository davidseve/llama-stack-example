#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [--traffic] [--validate] [--all]"
    echo ""
    echo "  --traffic    Generate traffic to LlamaStack (/v1/chat/completions + /v1/responses)"
    echo "  --validate   Validate all observability components (operators, collector, Tempo, Grafana, metrics, traces)"
    echo "  --all        Run both traffic generation and validation"
    echo ""
    echo "The observability stack (operators, OTEL collector, Tempo, Grafana) is deployed"
    echo "via GitOps using the appOfApps pattern. See gitops/appOfApps.yaml."
    echo ""
    echo "Prerequisites:"
    echo "  - oc CLI logged in with cluster-admin"
    echo "  - examples/.env configured with REMOTE_BASE_URL and INFERENCE_MODEL_ID"
    exit 1
}

if [[ $# -eq 0 ]]; then
    usage
fi

if [[ -f "$EXAMPLES_DIR/.env" ]]; then
    source "$EXAMPLES_DIR/.env"
fi

DO_TRAFFIC=false
DO_VALIDATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --traffic)   DO_TRAFFIC=true; shift ;;
        --validate)  DO_VALIDATE=true; shift ;;
        --all)       DO_TRAFFIC=true; DO_VALIDATE=true; shift ;;
        *)           usage ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LlamaStack Observability Example${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if $DO_TRAFFIC; then
    echo -e "${YELLOW}>>> Phase 1: Generate traffic${NC}"
    bash "$SCRIPT_DIR/scripts/generate_traffic.sh"
    echo ""
fi

if $DO_VALIDATE; then
    echo -e "${YELLOW}>>> Phase 2: Validate observability${NC}"
    bash "$SCRIPT_DIR/scripts/validate_all.sh"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Done!${NC}"
echo -e "${GREEN}========================================${NC}"
