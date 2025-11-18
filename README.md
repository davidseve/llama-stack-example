## Installation (MaaS)

These are the installation steps using MaaS.

### Pass the token via an environment variable when applying with oc

To parameterize `VLLM_API_TOKEN` in `llama-stack-example/gitops/appOfApps.yaml`, use the environment variable `${VLLM_API_TOKEN}`, which you can substitute at apply time.

Suggested steps:

1. Export your token to an environment variable.
   ```bash
   export VLLM_API_TOKEN="<your_token>"
   ```

2. Apply the manifest using `envsubst` and `oc apply`:
   ```bash
   envsubst < gitops/appOfApps.yaml | oc apply -f -
   ```

Notes:
- `envsubst` replaces `${VLLM_API_TOKEN}` before sending it to `oc`.
- Ensure the correct project/namespace is configured in the manifest, or use `-n <namespace>` with `oc apply` if needed.


## Run the ReAct chatbot (RAG + MCP)

This section explains how to run `tests/agent-chatbot/llama_reactagent_chatbot-rag-mcp.py`. The script creates a ReAct agent using Llama Stack, enables RAG with a small example document set, and uses MCP tools (e.g., `mcp::openshift`).

### Prerequisites

- Python 3.8+ and `pip`
- An accessible Llama Stack server (`REMOTE_BASE_URL`)
- RAG enabled on the Llama Stack server
- OpenShift MCP toolgroup registered in Llama Stack (`mcp::openshift`)

### Quick start (recommended with virtualenv)

```bash
cd tests/agent-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure variables (minimal .env)

Create or edit a `.env` file in `llama-stack-example/tests/agent-chatbot` with at least these variables:

```bash
REMOTE_BASE_URL=http://localhost:8321
INFERENCE_MODEL_ID=llama-4-scout-17b-16e-w4a16
LLAMA_STACK_TIMEOUT=30
SKIP_SSL_VERIFY=false
```

### Run the script

```bash
python3 llama_reactagent_chatbot-rag-mcp.py
```

What the script does:
- Verifies registered MCP toolgroups and lists available tools
- Inserts example documents into a vector DB for RAG
- Creates a session and runs a test query, showing tool usage and agent response

To change the test query, edit the `query` variable in the `main()` function of `llama_reactagent_chatbot-rag-mcp.py`.

### Troubleshooting

- "No OpenShift MCP tools found": ensure the MCP server is running and registered in Llama Stack (toolgroup `mcp::openshift`).
- "RAG tool is not available": verify RAG is enabled on the server and the client exposes `tool_runtime.rag_tool`.
- TLS issues: set `SKIP_SSL_VERIFY=true` only in test environments with untrusted certificates.

