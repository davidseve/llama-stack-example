# Guardrails Simple -- Granite Guardian

Tests safety guardrails using Granite Guardian 3.1 2B directly as a safety model
via Llama Stack's `inline::llama-guard` provider and the Responses API.

No orchestrator or external detector services needed -- just the guardian model
served as a vLLM endpoint.

## Prerequisites

1. **Llama Stack** deployed with guardrails enabled in Helm values:
   ```yaml
   guardrails:
     enabled: true
     guardianModel: "granite3-guardian-2b"
   ```

2. **Granite Guardian 3.1 2B** accessible as a vLLM endpoint (configured in `providers.vllm`).

3. Python 3.9+

## Quick Start

```bash
export LLAMA_STACK_URL="https://your-llama-stack-route.example.com"
export MODEL_ID="your-llm-model-id"
export SHIELD_ID="granite3-guardian-2b"

./run_example.sh
```

## Test Cases

| Test | Shield Active | Prompt | Expected |
|------|--------------|--------|----------|
| `safe` | Yes | "What is the capital of France?" | Success |
| `harmful` | Yes | Hateful/abusive language | Violation |
| `jailbreak` | Yes | "Ignore all previous instructions..." | Violation |
| `passthrough` | No | Same harmful prompt without shield | Success |

## Options

```bash
# Run specific tests only
python test_guardrails.py --url $URL --model $MODEL --shield $SHIELD --test-only safe harmful

# Verbose output
python test_guardrails.py --url $URL --model $MODEL --shield $SHIELD --verbose
```
