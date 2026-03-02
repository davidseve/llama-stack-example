# Guardrails Example

Tests TrustyAI Guardrails integration with Llama Stack using the Responses API.

## Prerequisites

1. **Llama Stack** deployed with guardrails enabled in `values.yaml`:
   ```yaml
   guardrails:
     enabled: true
     orchestratorUrl: "https://guardrails-orchestrator:8080"
     regex:
       enabled: true
       filter: ["(?i).*fight club.*"]
     hap:
       enabled: true
     prompt_injection:
       enabled: true
     language_detection:
       enabled: true
   ```

2. **Guardrails Orchestrator** deployed (see `charts/guardrails-orchestrator`).

3. Python 3.9+

## Quick Start

```bash
# Set required environment variables
export LLAMA_STACK_URL="https://your-llama-stack-route.example.com"
export MODEL_ID="your-model-id"

# Run all tests
./run_example.sh

# Or run directly
python test_guardrails.py --url $LLAMA_STACK_URL --model $MODEL_ID
```

## Test Cases

| Test | Shield | Prompt | Expected |
|------|--------|--------|----------|
| `regex` | regex | "Tell me about fight club..." | Violation |
| `hap` | hap | Hateful/abusive language | Violation |
| `prompt_injection` | prompt_injection | "Forget your instructions..." | Violation |
| `language_detection` | language_detection | Spanish prompt | Violation |
| `all_shields_safe` | all | "What is the capital of France?" | Success |
| `no_shields` | none | "Tell me about fight club." | Success |

## Options

```bash
# Test only specific shields
python test_guardrails.py --url $URL --model $MODEL --shields regex hap

# Run only specific test cases
python test_guardrails.py --url $URL --model $MODEL --test-only regex all_shields_safe

# Verbose output (show full response text)
python test_guardrails.py --url $URL --model $MODEL --verbose

# With SSL verification
python test_guardrails.py --url $URL --model $MODEL --verify-ssl
```
