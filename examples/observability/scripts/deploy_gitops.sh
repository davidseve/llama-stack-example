#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="${NAMESPACE:-llama-stack-example}"

echo -e "${BLUE}[1/5] Applying appOfApps...${NC}"
oc apply -f "$REPO_ROOT/gitops/appOfApps.yaml"

echo -e "${BLUE}[2/5] Waiting for operator subscriptions (up to 5 min)...${NC}"
OPERATORS=("grafana-operator" "tempo-product" "opentelemetry-product")
for op in "${OPERATORS[@]}"; do
    echo -n "  Waiting for $op CSV... "
    TIMEOUT=300
    ELAPSED=0
    while [[ $ELAPSED -lt $TIMEOUT ]]; do
        PHASE=$(oc get csv -A 2>/dev/null | grep "$op" | head -1 | awk '{print $NF}' || echo "")
        if [[ "$PHASE" == "Succeeded" ]]; then
            echo -e "${GREEN}Succeeded${NC}"
            break
        fi
        sleep 10
        ELAPSED=$((ELAPSED + 10))
    done
    if [[ $ELAPSED -ge $TIMEOUT ]]; then
        echo -e "${RED}TIMEOUT (not found after ${TIMEOUT}s)${NC}"
    fi
done

echo -e "${BLUE}[3/5] Waiting for UWM pods (up to 3 min)...${NC}"
echo -n "  Waiting for prometheus-user-workload... "
TIMEOUT=180
ELAPSED=0
while [[ $ELAPSED -lt $TIMEOUT ]]; do
    COUNT=$(oc get pods -n openshift-user-workload-monitoring 2>/dev/null | grep -c "Running" || true)
    COUNT=${COUNT:-0}
    if [[ "$COUNT" -gt 0 ]]; then
        echo -e "${GREEN}Running ($COUNT pods)${NC}"
        break
    fi
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done
if [[ $ELAPSED -ge $TIMEOUT ]]; then
    echo -e "${YELLOW}TIMEOUT (UWM may need cluster-monitoring-config; check openshift-monitoring)${NC}"
fi

echo -e "${BLUE}[4/5] Waiting for observability pods in $NAMESPACE (up to 5 min)...${NC}"
COMPONENTS=("tempo" "llama-stack-collector" "llama-stack-grafana")
for comp in "${COMPONENTS[@]}"; do
    echo -n "  Waiting for $comp... "
    TIMEOUT=300
    ELAPSED=0
    while [[ $ELAPSED -lt $TIMEOUT ]]; do
        READY=$(oc get pods -n "$NAMESPACE" 2>/dev/null | grep "$comp" | grep "Running" | head -1 || echo "")
        if [[ -n "$READY" ]]; then
            echo -e "${GREEN}Running${NC}"
            break
        fi
        sleep 15
        ELAPSED=$((ELAPSED + 15))
    done
    if [[ $ELAPSED -ge $TIMEOUT ]]; then
        echo -e "${RED}TIMEOUT${NC}"
    fi
done

echo -e "${BLUE}[5/5] Routes${NC}"
GRAFANA_ROUTE=$(oc get route llama-stack-grafana-route -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "not found")
JAEGER_ROUTE=$(oc get route tempo-jaegerui -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "not found")

echo -e "  Grafana:   ${GREEN}https://${GRAFANA_ROUTE}${NC}"
echo -e "  Jaeger UI: ${GREEN}https://${JAEGER_ROUTE}${NC}"
echo ""
echo -e "${GREEN}Deployment complete.${NC}"
