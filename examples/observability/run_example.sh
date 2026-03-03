#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$EXAMPLES_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [--deploy] [--test] [--all]"
    echo ""
    echo "  --deploy   Deploy observability stack via GitOps (operators, OTEL collector, Tempo, Grafana)"
    echo "  --test     Generate traffic and validate all observability components"
    echo "  --all      Run both deploy and test"
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

DO_DEPLOY=false
DO_TEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --deploy) DO_DEPLOY=true; shift ;;
        --test)   DO_TEST=true; shift ;;
        --all)    DO_DEPLOY=true; DO_TEST=true; shift ;;
        *)        usage ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LlamaStack Observability Example${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if $DO_DEPLOY; then
    echo -e "${YELLOW}>>> Phase 1: Deploy observability stack${NC}"
    bash "$SCRIPT_DIR/scripts/deploy_gitops.sh"
    echo ""
fi

if $DO_TEST; then
    echo -e "${YELLOW}>>> Phase 2: Generate traffic${NC}"
    bash "$SCRIPT_DIR/scripts/generate_traffic.sh"
    echo ""

    echo -e "${YELLOW}>>> Phase 3: Validate observability${NC}"
    bash "$SCRIPT_DIR/scripts/validate_all.sh"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Done!${NC}"
echo -e "${GREEN}========================================${NC}"
