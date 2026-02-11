#!/usr/bin/env bash
# Run validate-mcp-server.sh and assert namespaces are listed. Exit 0 only if all pass.
# IMPORTANT: Do NOT call mcp_list_namespaces.py separately — validate already calls it,
#            and supergateway only supports ONE SSE connection at a time.
# Usage: ./scripts/test-mcp-remote-access.sh <MCP_SERVER_BASE_URL>
set -e

[[ -n "${1:-}" ]] || { echo "Usage: $0 <MCP_SERVER_BASE_URL>" >&2; exit 1; }
BASE_URL="${1%/}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAIL=0

OUTPUT=$("${SCRIPT_DIR}/validate-mcp-server.sh" "$BASE_URL" 2>&1) || { echo "validate-mcp-server.sh failed"; echo "$OUTPUT" >&2; exit 1; }
echo "$OUTPUT"
echo "$OUTPUT" | grep -q "OK: MCP server responded with HTTP" || { echo "FAIL: Expected HTTP response from MCP server" >&2; FAIL=1; }
echo "$OUTPUT" | grep -q "Namespaces (via MCP):" || { echo "FAIL: Expected Namespaces (via MCP)" >&2; FAIL=1; }
echo "$OUTPUT" | grep -A 200 "Namespaces (via MCP):" | tail -n +2 | grep -q '[a-zA-Z0-9]' || { echo "FAIL: Expected at least one namespace" >&2; FAIL=1; }

[[ $FAIL -eq 0 ]] || { echo "Output:" >&2; echo "$OUTPUT" >&2; exit 1; }
echo ""
echo "PASS: MCP remote access test (HTTP OK + namespaces listed via MCP)"
exit 0
