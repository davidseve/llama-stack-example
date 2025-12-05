# Test All Examples

Script to run all RAG examples in sequence.

## Usage

```bash
# Run all examples
./run_all.sh

# Run only rag-evaluation-ragas (skip chatbot)
./run_all.sh --skip-mcp

# Run only rag-mcp-chatbot (skip evaluation)
./run_all.sh --skip-evaluation

# Show what would be executed without running anything
./run_all.sh --dry-run
```

## Included Examples

| Example | Description |
|---------|-------------|
| `rag-mcp-chatbot` | Chatbot with RAG + MCP tools |
| `rag-evaluation-ragas` | RAG evaluation with RAGAS metrics |

## Requirements

Before running, make sure to:

1. **Configure each example** with its `.env` file:
   ```bash
   # For rag-mcp-chatbot
   cp ../rag-mcp-chatbot/env.example ../rag-mcp-chatbot/.env
   
   # For rag-evaluation-ragas
   cp ../rag-evaluation-ragas/env.template ../rag-evaluation-ragas/.env
   ```

2. **Install dependencies** for each example:
   ```bash
   cd ../rag-mcp-chatbot && pip install -r requirements.txt
   cd ../rag-evaluation-ragas && pip install -r requirements.txt
   ```

3. **Have access to a Llama Stack server** configured with:
   - Inference model (e.g., `granite32-8b`)
   - Embedding model (e.g., `granite-embedding-125m`)
   - Milvus configured

## Options

| Option | Description |
|--------|-------------|
| `--skip-mcp` | Skip the rag-mcp-chatbot example |
| `--skip-evaluation` | Skip the rag-evaluation-ragas example |
| `--dry-run` | Show what would be executed without running |
| `--help`, `-h` | Show help |
