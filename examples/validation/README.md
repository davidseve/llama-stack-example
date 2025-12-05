# LlamaStack Validation Scripts

This directory contains comprehensive validation scripts to test your LlamaStack deployment and ensure all components are working correctly.

## Files

- `validate_llamastack_enhanced.py` - Enhanced validation script with comprehensive testing
- `run_validation.sh` - Shell script wrapper for easy execution
- `validate_llamastack.py` - Original validation script (preserved)

## Features

The enhanced validation script tests:

- ✅ **Connection** - Basic connectivity to LlamaStack
- ✅ **Models** - Model availability and metadata
- ✅ **Inference** - Text completions and chat completions
- ✅ **Embeddings** - Embedding generation
- ✅ **Agent Sessions** - Agent creation and management  
- ✅ **Tool Groups** - WebSearch, RAG, and MCP tools
- ✅ **MCP Integration** - Model Context Protocol functionality
- ✅ **Safety API** - Content safety checking
- ✅ **Evaluation API** - Model evaluation capabilities
- ✅ **Vector Database** - Vector storage functionality
- ✅ **Configuration Validation** - Expected provider validation

## Quick Start

### Using the Shell Wrapper (Recommended)

```bash
# Basic validation
./run_validation.sh --url http://localhost:8321

# With authentication
./run_validation.sh --url http://llamastack-service:8321 --token your-api-token

# Save results to JSON
./run_validation.sh --url http://localhost:8321 --json-output results.json

# Install dependencies automatically
./run_validation.sh --url http://localhost:8321 --install-deps
```

### Using the Python Script Directly

```bash
# Install dependencies first
pip install llama-stack-client

# Run validation
python3 validate_llamastack_enhanced.py --url http://localhost:8321
```

## Configuration

### Environment Variables

You can set these environment variables to avoid repeating parameters:

```bash
export LLAMASTACK_URL="http://localhost:8321"
export LLAMASTACK_TOKEN="your-api-token"
export VLLM_URL="http://vllm-service:8000/v1"
export MCP_URL="http://mcp-service:8080"
```

### Expected Configuration

The validation script expects the following providers based on your deployment:

- **Inference**: VLLM and Sentence Transformers
- **Tool Runtime**: WebSearch (Tavily/Brave), RAG, MCP
- **Safety**: TrustyAI FMS
- **Evaluation**: TrustyAI LMEval  
- **Vector DB**: Milvus
- **Agents**: Meta Reference implementation

## Command Line Options

```
--url URL                 LlamaStack URL (required)
--token TOKEN             API token (optional)
--timeout SECONDS         Request timeout (default: 30)
--json-output FILE        Save results to JSON file
--help                   Show help message
```

## Example Output

```
==========================================
Enhanced LlamaStack Comprehensive Validation
==========================================
[INFO] Target URL: http://localhost:8321
[INFO] Timestamp: 2024-01-15 10:30:00

============================================================
🔗 Testing Connection
============================================================
[SUCCESS] ✓ Connected to LlamaStack at http://localhost:8321
[INFO] Found 2 models

============================================================
🤖 Testing Model Availability
============================================================
[SUCCESS] ✓ Model: llama3.1-8b (llm)
[SUCCESS] ✓ Model: granite-embedding-125m (embedding)

============================================================
📊 Test Summary
============================================================
Total Tests: 12
[SUCCESS] Passed: 10
[ERROR] Failed: 2

Success Rate: 83.3%
[SUCCESS] 🎉 LlamaStack instance is functioning well!
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check if LlamaStack service is running
   - Verify the URL is correct
   - Check network connectivity

2. **Authentication Error**
   - Ensure API token is correct
   - Check if authentication is required

3. **Model Not Found**
   - Verify models are properly loaded
   - Check model configuration in deployment

4. **MCP Tools Not Available**
   - Ensure MCP service is running
   - Check MCP service connectivity
   - Verify MCP configuration in run.yaml

5. **Tool Groups Missing**
   - Check tool runtime providers are configured
   - Verify API keys for external services (Tavily, Brave)

### Debug Mode

For more detailed error information, you can modify the script to add debug logging or catch specific exceptions.

## Integration with CI/CD

You can use this script in CI/CD pipelines:

```bash
# Exit code 0 = success, 1 = failure
./run_validation.sh --url $LLAMASTACK_URL --json-output validation-results.json

# Check success rate in results
if [ $? -eq 0 ]; then
    echo "Validation passed"
else
    echo "Validation failed"
    exit 1
fi
```

## JSON Output Format

When using `--json-output`, results are saved in this format:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "url": "http://localhost:8321",
  "success_rate": 83.3,
  "tests": [
    {
      "name": "Connection",
      "success": true,
      "details": "Connected successfully, 2 models found",
      "timestamp": "2024-01-15T10:30:01.123456"
    }
  ]
}
```

## Contributing

To add new validation tests:

1. Add a new test method to the `EnhancedLlamaStackValidator` class
2. Call the test method in `run_all_tests()`
3. Follow the existing pattern for error handling and result tracking
