#!/usr/bin/env bash
# Validate MCP server: HTTP health check (POST /message) + list namespaces via MCP.
# IMPORTANT: Do NOT use GET /sse for health-check — supergateway only supports
#            ONE SSE connection at a time; a second one crashes the process.
# Usage: ./scripts/validate-mcp-server.sh <MCP_SERVER_BASE_URL>
set -e

TIMEOUT=5

while [[ $# -gt 0 ]]; do
  case $1 in
    -*)
      echo "Usage: $0 <MCP_SERVER_BASE_URL>" >&2
      exit 1
      ;;
    *) BASE_URL="$1"; shift ;;
  esac
done

[[ -n "${BASE_URL}" ]] || { echo "Usage: $0 <MCP_SERVER_BASE_URL>" >&2; exit 1; }
BASE_URL="${BASE_URL%/}"

# Health check: GET /healthz (supergateway --healthEndpoint /healthz returns "ok").
# IMPORTANT: Do NOT use GET /sse — supergateway only supports ONE SSE connection;
#            a second one crashes the process.
HEALTH_URL="${BASE_URL}/healthz"
echo "Checking MCP server at ${HEALTH_URL} (timeout ${TIMEOUT}s)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" --insecure "$HEALTH_URL" 2>/dev/null || true)

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "FAIL: MCP server health check returned HTTP ${HTTP_CODE:-(no response)} (expected 200 from /healthz)"
  exit 1
fi
echo "OK: MCP server responded with HTTP 200"

# List namespaces via MCP protocol (connects to /sse once)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 &>/dev/null && [[ -f "${SCRIPT_DIR}/mcp_list_namespaces.py" ]]; then
  if NAMESPACES=$(python3 "${SCRIPT_DIR}/mcp_list_namespaces.py" "$BASE_URL" 2>&1); then
    echo "Namespaces (via MCP):"
    echo "$NAMESPACES" | sed 's/^/  /'
  else
    echo "Warning: could not list namespaces via MCP"
    echo "$NAMESPACES" | sed 's/^/  /' >&2
  fi
fi
exit 0
