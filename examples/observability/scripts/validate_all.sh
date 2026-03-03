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

NAMESPACE="${NAMESPACE:-llama-stack-example}"
PASS=0
FAIL=0
WARN=0

check() {
    local label="$1"
    local result="$2"
    local hint="${3:-}"

    if [[ "$result" == "PASS" ]]; then
        echo -e "  ${GREEN}[PASS]${NC} $label"
        PASS=$((PASS + 1))
    elif [[ "$result" == "WARN" ]]; then
        echo -e "  ${YELLOW}[WARN]${NC} $label"
        [[ -n "$hint" ]] && echo -e "         ${YELLOW}$hint${NC}"
        WARN=$((WARN + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} $label"
        [[ -n "$hint" ]] && echo -e "         ${RED}$hint${NC}"
        FAIL=$((FAIL + 1))
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Observability Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# --- 1. Operators ---
echo -e "${BLUE}[1/8] Operators${NC}"
for op in "grafana-operator" "tempo-operator" "opentelemetry-operator"; do
    PHASE=$(oc get csv -A 2>/dev/null | grep "$op" | head -1 | awk '{print $NF}' || echo "")
    if [[ "$PHASE" == "Succeeded" ]]; then
        check "$op CSV" "PASS"
    else
        check "$op CSV" "FAIL" "Not found or not Succeeded. Install via OperatorHub or check charts/operators."
    fi
done

# --- 2. User Workload Monitoring ---
echo ""
echo -e "${BLUE}[2/8] User Workload Monitoring${NC}"
UWM_PODS=$(oc get pods -n openshift-user-workload-monitoring --no-headers 2>/dev/null | grep -c "Running" || true)
UWM_PODS=${UWM_PODS:-0}
if [[ "$UWM_PODS" -gt 0 ]]; then
    check "UWM pods running ($UWM_PODS)" "PASS"
else
    check "UWM pods" "FAIL" "No running pods in openshift-user-workload-monitoring. Check cluster-monitoring-config ConfigMap."
fi

# --- 3. OTEL Collector ---
echo ""
echo -e "${BLUE}[3/8] OTEL Collector${NC}"
OTEL_POD=$(oc get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep "llama-stack-collector" | grep "Running" | head -1 || echo "")
if [[ -n "$OTEL_POD" ]]; then
    check "OTEL Collector pod running" "PASS"
else
    check "OTEL Collector pod" "FAIL" "Not found in $NAMESPACE. Check OpenTelemetry operator and charts/otel-collector."
fi

OTEL_SVC=$(oc get svc -n "$NAMESPACE" 2>/dev/null | grep "llama-stack-collector" | head -1 || echo "")
if [[ -n "$OTEL_SVC" ]]; then
    check "OTEL Collector service exists" "PASS"
else
    check "OTEL Collector service" "FAIL" "Service not found."
fi

# --- 4. Tempo ---
echo ""
echo -e "${BLUE}[4/8] Tempo${NC}"
TEMPO_POD=$(oc get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep "tempo" | grep "Running" | head -1 || echo "")
if [[ -n "$TEMPO_POD" ]]; then
    check "Tempo pod running" "PASS"
else
    check "Tempo pod" "FAIL" "Not found in $NAMESPACE. Check Tempo operator and charts/tempo."
fi

TEMPO_SVC_CHECK=$(oc get svc -n "$NAMESPACE" --no-headers 2>/dev/null | grep "^tempo-tempo " || echo "")
if [[ -n "$TEMPO_SVC_CHECK" ]]; then
    check "Tempo service available" "PASS"
else
    check "Tempo service" "FAIL" "tempo-tempo service not found."
fi

# --- 5. Grafana ---
echo ""
echo -e "${BLUE}[5/8] Grafana${NC}"
GRAFANA_POD=$(oc get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep "llama-stack-grafana" | grep "Running" | head -1 || echo "")
if [[ -n "$GRAFANA_POD" ]]; then
    check "Grafana pod running" "PASS"
else
    check "Grafana pod" "FAIL" "Not found in $NAMESPACE. Check Grafana operator and charts/grafana."
fi

GRAFANA_ROUTE=$(oc get route llama-stack-grafana-route -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
if [[ -n "$GRAFANA_ROUTE" ]]; then
    HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" "https://$GRAFANA_ROUTE" 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" =~ ^(200|302|403)$ ]]; then
        check "Grafana route accessible (HTTP $HTTP_CODE): https://$GRAFANA_ROUTE" "PASS"
    else
        check "Grafana route (HTTP $HTTP_CODE)" "FAIL" "https://$GRAFANA_ROUTE returned unexpected status."
    fi
else
    check "Grafana route" "FAIL" "Route not found."
fi

DS_COUNT=$(oc get grafanadatasource -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l || true)
DS_COUNT=$(echo "$DS_COUNT" | tr -d '[:space:]')
DS_COUNT=${DS_COUNT:-0}
check "Grafana datasources configured ($DS_COUNT)" "$([ "$DS_COUNT" -gt 0 ] && echo PASS || echo FAIL)"

DASH_COUNT=$(oc get grafanadashboard -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l || true)
DASH_COUNT=$(echo "$DASH_COUNT" | tr -d '[:space:]')
DASH_COUNT=${DASH_COUNT:-0}
check "Grafana dashboards configured ($DASH_COUNT)" "$([ "$DASH_COUNT" -gt 0 ] && echo PASS || echo FAIL)"

# --- 6. Metrics ---
echo ""
echo -e "${BLUE}[6/8] Metrics (Prometheus)${NC}"
TOKEN=$(oc whoami -t 2>/dev/null || echo "")
if [[ -n "$TOKEN" ]]; then
    SPANMETRICS_RESULT=$(oc exec -n openshift-user-workload-monitoring prometheus-user-workload-0 -c prometheus -- \
        curl -s 'http://localhost:9090/api/v1/query?query=traces_span_metrics_calls_total' 2>/dev/null || echo "")
    SPAN_COUNT=$(echo "$SPANMETRICS_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('result',[])))" 2>/dev/null || echo "0")
    SPAN_COUNT=${SPAN_COUNT:-0}
    if [[ "$SPAN_COUNT" -gt 0 ]]; then
        check "traces_span_metrics_calls_total found ($SPAN_COUNT series)" "PASS"
    else
        check "traces_span_metrics_calls_total" "WARN" "No span metrics yet. Generate traffic first (run_example.sh --test)."
    fi

    for EP in "/v1/chat/completions" "/v1/responses"; do
        EP_QUERY="traces_span_metrics_calls_total{span_name=\"$EP\"}"
        EP_RESULT=$(oc exec -n openshift-user-workload-monitoring prometheus-user-workload-0 -c prometheus -- \
            curl -s "http://localhost:9090/api/v1/query?query=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$EP_QUERY'))")" 2>/dev/null || echo "")
        EP_COUNT=$(echo "$EP_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(sum(float(x['value'][1]) for x in r))" 2>/dev/null || echo "0")
        EP_COUNT=${EP_COUNT:-0}
        if python3 -c "exit(0 if float('$EP_COUNT') > 0 else 1)" 2>/dev/null; then
            check "Endpoint $EP metrics (calls=$EP_COUNT)" "PASS"
        else
            check "Endpoint $EP metrics" "WARN" "No data for $EP. Generate traffic to this endpoint."
        fi
    done
else
    check "Prometheus query" "WARN" "No oc token available. Cannot query Prometheus."
fi

SM_COUNT=$(oc get servicemonitor -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l || true)
SM_COUNT=$(echo "$SM_COUNT" | tr -d '[:space:]')
SM_COUNT=${SM_COUNT:-0}
check "ServiceMonitor exists ($SM_COUNT)" "$([ "$SM_COUNT" -gt 0 ] && echo PASS || echo FAIL)"

LS_POD=$(oc get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep "llama-stack-example" | grep "Running" | head -1 | awk '{print $1}' || echo "")

# --- 7. Traces ---
echo ""
echo -e "${BLUE}[7/8] Traces (Tempo)${NC}"
TEMPO_SVC=$(oc get svc -n "$NAMESPACE" 2>/dev/null | grep "^tempo-tempo " | head -1 || echo "")
if [[ -n "$TEMPO_SVC" ]]; then
    TRACE_COUNT=$(oc exec -n "$NAMESPACE" "$LS_POD" -- \
        python3 -c "import urllib.request,json; d=json.loads(urllib.request.urlopen('http://tempo-tempo:3200/api/search?limit=20').read()); print(len(d.get('traces',[])))" 2>/dev/null || echo "0")
    TRACE_COUNT=${TRACE_COUNT:-0}
    if [[ "$TRACE_COUNT" -gt 0 ]]; then
        check "Traces found in Tempo ($TRACE_COUNT)" "PASS"
    else
        check "Traces in Tempo" "WARN" "No traces yet. Generate traffic first, then wait for OTEL batch export."
    fi

    for EP in "/v1/chat/completions" "/v1/responses"; do
        EP_TRACES=$(oc exec -n "$NAMESPACE" "$LS_POD" -- \
            python3 -c "
import urllib.request,json
d=json.loads(urllib.request.urlopen('http://tempo-tempo:3200/api/search?limit=50').read())
count=sum(1 for t in d.get('traces',[]) if t.get('rootTraceName','')=='$EP')
print(count)" 2>/dev/null || echo "0")
        EP_TRACES=${EP_TRACES:-0}
        if [[ "$EP_TRACES" -gt 0 ]]; then
            check "Traces for $EP ($EP_TRACES found)" "PASS"
        else
            check "Traces for $EP" "WARN" "No traces for $EP. Generate traffic to this endpoint."
        fi
    done
else
    check "Tempo service" "FAIL" "tempo-tempo service not found."
fi

# --- 8. Logs ---
echo ""
echo -e "${BLUE}[8/8] Logs${NC}"
if [[ -n "$LS_POD" ]]; then
    LOG_LINES=$(oc logs "$LS_POD" -n "$NAMESPACE" --tail=50 2>/dev/null | wc -l || echo "0")
    if [[ "$LOG_LINES" -gt 0 ]]; then
        check "LlamaStack pod logs available ($LOG_LINES lines)" "PASS"
    else
        check "LlamaStack pod logs" "WARN" "Pod found but no log output."
    fi

    OTEL_ENVS=$(oc get pod "$LS_POD" -n "$NAMESPACE" -o yaml 2>/dev/null | grep -c "OTEL_" || true)
    OTEL_ENVS=${OTEL_ENVS:-0}
    if [[ "$OTEL_ENVS" -gt 0 ]]; then
        check "LlamaStack OTEL env vars configured ($OTEL_ENVS vars)" "PASS"
    else
        check "LlamaStack OTEL env vars" "FAIL" "No OTEL_ env vars found. Check providers.telemetry.enabled in values."
    fi
else
    check "LlamaStack pod" "FAIL" "Not found running in $NAMESPACE."
fi

# --- Summary ---
echo ""
echo -e "${BLUE}========================================${NC}"
TOTAL=$((PASS + FAIL + WARN))
echo -e "  Total: $TOTAL checks"
echo -e "  ${GREEN}PASS: $PASS${NC}  ${RED}FAIL: $FAIL${NC}  ${YELLOW}WARN: $WARN${NC}"
echo -e "${BLUE}========================================${NC}"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
