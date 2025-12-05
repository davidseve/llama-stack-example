# Llama Stack Chatbot with RAG + MCP Tools

A chatbot that combines:
- **RAG (Retrieval Augmented Generation)**: Search documentation via `file_search`
- **MCP (Model Context Protocol)**: Interact with OpenShift/Kubernetes cluster

## Quick Start

```bash
# 1. Configure your environment
cp env.example .env
# Edit .env with your Llama Stack URL

# 2. Run the complete workflow
./run_example.sh
```

Or step by step:

```bash
# Upload documents first
python milvus-upload.py --url https://your-llama-stack-url

# Then run the chatbot (use the VECTOR_STORE_ID from previous step)
VECTOR_STORE_ID=vs_xxx python chatbot.py
```

## Configuration

Create a `.env` file:

```bash
REMOTE_BASE_URL=https://llama-stack.example.com
INFERENCE_MODEL_ID=llama-4-scout-17b-16e-w4a16
EMBEDDING_MODEL=granite-embedding-125m
VECTOR_STORE_ID=vs_xxx  # Optional, will be created if not set
SKIP_SSL_VERIFY=true
```

## Project Structure

```
agent-chatbot/
├── chatbot.py           # Main chatbot using Responses API
├── milvus-upload.py     # Upload documents to vector store
├── run_example.sh       # Complete workflow script
├── documents/           # Documentation to index
│   ├── discounts-application-overview.txt
│   ├── discounts-application-troubleshooting.txt
│   └── discounts-application-configuration.txt
├── requirements.txt
└── .env                 # Configuration (create from .env.example)
```

## How It Works

### The Responses API Internal Loop

When you call `client.responses.create()`, **the server handles tool execution automatically**:

```
Your Code                          Llama Stack Server
    │                                     │
    │  responses.create(tools=[...])      │
    │ ─────────────────────────────────►  │
    │                                     │
    │                           ┌─────────┴─────────┐
    │                           │                   │
    │                           │  1. LLM Call #1   │
    │                           │  (decide tools)   │
    │                           │        │          │
    │                           │        ▼          │
    │                           │  2. Execute MCP   │
    │                           │     (34ms)        │
    │                           │        │          │
    │                           │        ▼          │
    │                           │  3. Execute RAG   │
    │                           │     (58ms)        │
    │                           │        │          │
    │                           │        ▼          │
    │                           │  4. LLM Call #2   │
    │                           │  (final response) │
    │                           │                   │
    │                           └─────────┬─────────┘
    │                                     │
    │  ◄───────────────────────────────── │
    │         Complete Response           │
```

**One API call = Multiple internal operations:**

| Step | Operation | Time |
|------|-----------|------|
| 1 | LLM decides which tools to use | ~400ms |
| 2 | Execute MCP tools (pods, logs, etc.) | ~35ms |
| 3 | Execute RAG search (file_search) | ~60ms |
| 4 | LLM generates final response | ~1500ms |

### Why No Manual Loop?

The Responses API is different from Chat Completions:

| API | Tool Execution | Loop |
|-----|----------------|------|
| **Chat Completions** | You (client) | Manual |
| **Responses API** | Server (automatic) | Internal |

This is by design - the Responses API handles the ReAct pattern internally.

### Evidence from Server Logs

```
13:47:07.081 [START] /v1/responses
   └→ openai_chat_completion (384ms)      ← LLM #1: decides tools
   └→ invoke_mcp_tool (34ms)              ← Executes MCP
   └→ knowledge_search (58ms)             ← Executes RAG
   └→ openai_chat_completion (1478ms)     ← LLM #2: final response
13:47:17.664 [END] /v1/responses
```

## Tools Available

### 1. MCP OpenShift Tools

Interact with your Kubernetes/OpenShift cluster:
- `pods_list_in_namespace`: List pods
- `pods_logs`: Get pod logs
- `deployments_list`: List deployments
- And 20+ more...

### 2. RAG file_search

Search your indexed documentation:
- Troubleshooting guides
- Configuration references
- Application overviews

## Example Query

```
Q: "List the pods in openshift-gitops and tell me about discounts troubleshooting"

The chatbot will:
1. Call MCP to list pods in the namespace
2. Search documentation for troubleshooting info
3. Combine both results in a comprehensive answer
```

## Adding Your Own Documents

1. Add `.txt` or `.md` files to the `documents/` folder
2. Run `python milvus-upload.py` to re-index
3. Update `VECTOR_STORE_ID` in `.env`

## Troubleshooting

### Error 500: "Unsupported tool call: file_search"

This is an intermittent server bug. Simply retry the request.

### MCP tools not found

Verify the `mcp::openshift` toolgroup is registered:
```python
client.toolgroups.list()
```

### RAG returns no results

Check that:
1. `VECTOR_STORE_ID` is set correctly
2. Documents were uploaded successfully
3. The query matches document content

## References

- [Llama Stack Documentation](https://llama-stack.readthedocs.io)
- [Responses vs Agents API](https://llama-stack.readthedocs.io/en/latest/building_applications/responses_vs_agents.html)
- [Red Hat OpenShift AI](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/)

