#!/usr/bin/env python3
"""
Call MCP server (Streamable HTTP) to list namespaces.
Uses POST /mcp (Streamable HTTP transport) — no SSE connections needed.
Exit 0 if namespaces listed, 1 on error.
"""
import json
import os
import sys
import ssl
import time
import urllib.request
import urllib.error

DEBUG = os.environ.get("DEBUG", "").strip().lower() in ("1", "true", "yes")


def _dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: mcp_list_namespaces.py <MCP_SERVER_BASE_URL>", file=sys.stderr)
        sys.exit(1)

    base = sys.argv[1].rstrip("/")
    mcp_url = f"{base}/mcp"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    session_id = None

    def post_mcp(payload_dict):
        """POST JSON-RPC to /mcp, track Mcp-Session-Id."""
        nonlocal session_id
        body = json.dumps(payload_dict).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        req = urllib.request.Request(mcp_url, data=body, headers=headers, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            # Capture session ID from response
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                session_id = sid
                _dbg(f"Session ID: {session_id}")
            raw = resp.read().decode("utf-8")
            _dbg(f"Response ({resp.status}): {raw[:500]}")
            if not raw.strip():
                return {}
            # Streamable HTTP may return SSE-formatted data or plain JSON
            if raw.strip().startswith("event:") or raw.strip().startswith("data:"):
                # Parse SSE-style response
                for line in raw.split("\n"):
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            return json.loads(data)
                return {}
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            sid = e.headers.get("Mcp-Session-Id") if hasattr(e, "headers") else None
            if sid:
                session_id = sid
            _dbg(f"HTTP {e.code}: {err_body[:500]}")
            raise

    # --- 1) Initialize ---
    _dbg(f"POST {mcp_url}")
    try:
        init_resp = post_mcp({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "validate-mcp", "version": "1.0.0"},
            },
        })
        _dbg(f"Initialize OK: {json.dumps(init_resp)[:300]}")
    except Exception as e:
        print(f"Initialize failed: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2) Initialized notification ---
    try:
        post_mcp({"jsonrpc": "2.0", "method": "notifications/initialized"})
    except Exception:
        pass
    time.sleep(0.3)

    # --- 3) Discover tools ---
    tool_name = None
    try:
        tools_resp = post_mcp({"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}})
        tools = tools_resp.get("result", {}).get("tools", [])
        tool_names = [t.get("name") for t in tools]
        _dbg(f"Available tools ({len(tools)}): {tool_names}")

        # Find a tool whose name contains "namespace" and "list"
        for t_info in tools:
            name = t_info.get("name", "")
            if "namespace" in name.lower() and "list" in name.lower():
                tool_name = name
                break
        # Fallback: any tool with "namespace" in name
        if not tool_name:
            for t_info in tools:
                name = t_info.get("name", "")
                if "namespace" in name.lower():
                    tool_name = name
                    break
        # Fallback: known tool names
        if not tool_name:
            for candidate in ("namespaces_list", "list_namespaces", "kubectl_get", "resources_get"):
                if candidate in tool_names:
                    tool_name = candidate
                    break
    except Exception as e:
        _dbg(f"tools/list failed: {e}")

    if not tool_name:
        tool_name = "namespaces_list"
    _dbg(f"Using tool: {tool_name}")

    # --- 4) Call the tool ---
    if tool_name in ("kubectl_get", "resources_get"):
        call_args = {"resource": "namespaces"}
    else:
        call_args = {}

    try:
        call_resp = post_mcp({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool_name, "arguments": call_args},
        })
    except Exception as e:
        print(f"tools/call failed: {e}", file=sys.stderr)
        sys.exit(1)

    if call_resp and "result" in call_resp:
        content = call_resp["result"].get("content", [])
        for c in content:
            if c.get("type") == "text":
                print(c.get("text", ""))
        if content:
            sys.exit(0)

    if call_resp and "error" in call_resp:
        print(f"MCP error: {call_resp['error']}", file=sys.stderr)
        sys.exit(1)

    print("Could not list namespaces via MCP", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
