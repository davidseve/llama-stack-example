# MCP Chatbot - Kubernetes + ArgoCD Diagnostics

A chatbot that uses the Llama Stack **Responses API** with MCP tools to diagnose application issues in OpenShift. It connects to both the **Kubernetes MCP server** and the **ArgoCD MCP server** registered in Llama Stack.

Unlike `rag-mcp-chatbot`, this example does **not** use RAG/file_search. It relies entirely on live MCP tool calls to gather information.

## Architecture

```
User Query
    │
    ▼
chatbot.py (Responses API)
    │
    ▼
Llama Stack Server
    ├── LLM decides which tools to call
    ├── mcp::openshift → Kubernetes MCP (pods, logs, events)
    ├── mcp::argocd   → ArgoCD MCP (app status, sync, resources)
    └── LLM produces diagnosis from tool results
```

## Prerequisites

- Llama Stack server running with both MCP toolgroups registered:
  - `mcp::openshift` (Kubernetes MCP server)
  - `mcp::argocd` (ArgoCD MCP server)
- Python 3.11+
- `examples/.env` configured with `REMOTE_BASE_URL` and `INFERENCE_MODEL_ID`

## Quick Start

```bash
# From the examples/mcp-chatbot directory
pip install -r requirements.txt
./run_example.sh
```

## Custom Queries

```bash
export TEST_QUERY="Why is the discounts deployment failing in openshift-gitops?"
python chatbot.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REMOTE_BASE_URL` | `http://localhost:8321` | Llama Stack server URL |
| `INFERENCE_MODEL_ID` | `granite32-8b` | Model to use for inference |
| `SKIP_SSL_VERIFY` | `false` | Skip SSL certificate verification |
| `LLAMA_STACK_TIMEOUT` | `300` | HTTP timeout in seconds |
| `TEST_QUERY` | *(discounts app diagnosis)* | Query to send to the chatbot |
