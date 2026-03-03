#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ -f "$EXAMPLES_DIR/.env" ]]; then
    source "$EXAMPLES_DIR/.env"
fi

LLAMA_STACK_URL="${LLAMA_STACK_URL:-${REMOTE_BASE_URL:-}}"
MODEL_ID="${INFERENCE_MODEL_ID:-}"
NUM_REQUESTS="${NUM_REQUESTS:-10}"
SKIP_SSL="${SKIP_SSL_VERIFY:-false}"

CURL_OPTS=()
if [[ "$SKIP_SSL" == "true" ]]; then
    CURL_OPTS+=(-k)
fi

if [[ -z "$LLAMA_STACK_URL" ]]; then
    echo -e "${RED}ERROR: LLAMA_STACK_URL or REMOTE_BASE_URL not set. Check examples/.env${NC}"
    exit 1
fi

if [[ -z "$MODEL_ID" ]]; then
    echo -e "${RED}ERROR: INFERENCE_MODEL_ID not set. Check examples/.env${NC}"
    exit 1
fi

echo -e "${BLUE}Generating traffic: $NUM_REQUESTS requests to $LLAMA_STACK_URL${NC}"
echo -e "${BLUE}Model: $MODEL_ID${NC}"
echo ""

PROMPTS=(
    "What is Kubernetes?"
    "Explain containerization in one paragraph."
    "How does a load balancer work?"
    "What is the difference between TCP and UDP?"
    "Describe the CAP theorem briefly."
    "What is a microservices architecture?"
    "Explain REST API design principles."
    "What is observability in distributed systems?"
    "How does distributed tracing work?"
    "What are the benefits of OpenTelemetry?"
)

SUCCESS=0
FAIL=0

for i in $(seq 1 "$NUM_REQUESTS"); do
    PROMPT_IDX=$(( (i - 1) % ${#PROMPTS[@]} ))
    PROMPT="${PROMPTS[$PROMPT_IDX]}"

    echo -n "  [$i/$NUM_REQUESTS] \"${PROMPT:0:40}...\" "

    RESPONSE=$(curl -s -w "\n%{http_code}" "${CURL_OPTS[@]}" \
        "$LLAMA_STACK_URL/v1/chat/completions" \
        -H 'Content-Type: application/json' \
        -d "{
            \"model\": \"$MODEL_ID\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}],
            \"stream\": false
        }" 2>/dev/null || echo -e "\n000")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "200" ]]; then
        TOTAL_TOKENS=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('usage',{}).get('total_tokens','?'))" 2>/dev/null || echo "?")
        echo -e "${GREEN}OK${NC} (tokens: $TOTAL_TOKENS)"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}FAIL (HTTP $HTTP_CODE)${NC}"
        FAIL=$((FAIL + 1))
    fi

    sleep 1
done

echo ""
echo -e "${BLUE}Results: ${GREEN}$SUCCESS OK${NC}, ${RED}$FAIL FAILED${NC}"

WAIT_SECS=60
echo -e "${YELLOW}Waiting ${WAIT_SECS}s for telemetry propagation (metrics export interval)...${NC}"
sleep "$WAIT_SECS"
echo -e "${GREEN}Telemetry propagation window complete.${NC}"
