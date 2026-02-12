# Llama Stack Examples

Examples demonstrating Llama Stack capabilities on Red Hat OpenShift AI.

## Prerequisites

| Component | Version | Description |
|-----------|---------|-------------|
| **OpenShift Container Platform** | 4.19+ | Kubernetes distribution for enterprise |
| **OpenShift GitOps** | - | GitOps continuous delivery (for automated deployment) |
| **Python** | 3.11+ | Required for running the example scripts |

---

## Installation

Choose one of the following installation options based on your infrastructure:

### Option 1: Model as a Service (MaaS)

Use this option when you want to consume models from an external provider (e.g., IBM watsonx, OpenAI-compatible endpoints). The LLM runs externally, and Llama Stack connects to it via API.

**Advantages:**
- No GPU resources required on your cluster
- Quick setup
- Lower infrastructure costs

**Steps:**

1. Export your MaaS configuration as environment variables:
   ```bash
   export LLAMA_4_SCOUT_API_TOKEN="<your_token>"
   ```

2. (Optional) To use **Gemini** models via Models.corp, export your Models.corp application credential:
   ```bash
   export GEMINI_API_KEY="<your_models_corp_credential>"
   ```
   > This enables Gemini models (e.g., `gemini-3-pro-preview`) through the OpenAI-compatible endpoint provided by Models.corp. See [Gemini integration](#gemini-via-modelscorp) below.

3. (Optional) For RAGAS remote evaluation with Kubeflow Pipelines, export your user token:
   ```bash
   export KUBEFLOW_PIPELINES_TOKEN="$(oc whoami -t)"
   ```
   > ⚠️ **Note**: This token expires (~24h). You'll need to renew it periodically.

4. Deploy using GitOps (OpenShift GitOps):
   ```bash
   envsubst < gitops/appOfApps.yaml | oc apply -f -
   ```

**Notes:**
- `envsubst` replaces `${LLAMA_4_SCOUT_API_TOKEN}`, `${GEMINI_API_KEY}`, and `${KUBEFLOW_PIPELINES_TOKEN}` before sending to `oc`.
- Ensure the correct project/namespace is configured in the manifest, or use `-n <namespace>` with `oc apply` if needed.
- See [DSPA SSL Configuration](./docs/DSPA-SSL-CONFIGURATION.md) for details on RAGAS remote evaluation setup.

---

### Option 2: Self-Hosted Model (vLLM)

Use this option when you want to deploy and run the LLM model directly on your OpenShift cluster using vLLM as the inference server.

**Advantages:**
- Full control over the model and infrastructure
- Data stays within your cluster
- No external API dependencies

**Requirements:**
- GPU nodes available in your cluster (NVIDIA recommended)
- Sufficient VRAM for the model (e.g., 24GB+ for 7B models)
- NVIDIA GPU Operator installed and configured

**Steps:**

1. Update `gitops/llama-stack-values.yaml` to point to your local vLLM inference service:
   ```yaml
   secret:
     data:
       INFERENCE_MODEL: "your-model-name"
       VLLM_URL: "http://vllm-inference.llama-stack.svc.cluster.local:8000/v1"
   ```

2. Deploy using GitOps (OpenShift GitOps):
   ```bash
   oc apply -f gitops/appOfApps.yaml
   ```

3. Wait for the vLLM inference service to be ready:
   ```bash
   oc get inferenceservice -n llama-stack -w
   ```

**Notes:**
- Model download may take several minutes depending on model size and network speed.
- The `VLLM_URL` should point to your internal vLLM service endpoint.

---

### Gemini via Models.corp

Llama Stack can use Google Gemini models through Red Hat's internal Models.corp infrastructure. The endpoint is OpenAI-compatible, so it connects directly via the `remote::openai` provider -- no proxy needed.

**How it works:**

```
Llama Stack (remote::openai) → Models.corp APIcast → Google Gemini API
```

The Gemini endpoint at Models.corp exposes an OpenAI-compatible API at `/v1beta/openai/chat/completions`, which Llama Stack's `remote::openai` provider speaks natively.

**Configuration:**

The Gemini provider is pre-configured in `gitops/llama-stack-values.yaml`:

```yaml
providers:
  openai:
    enabled: true
    baseUrl: "https://gemini--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443/v1beta/openai"
    models:
      gemini-pro:
        modelId: "gemini-3-pro-preview"
        providerModelId: "gemini-3-pro-preview"
```

To add more models (e.g., `gemini-2.0-flash`), add entries under `models`:

```yaml
    models:
      gemini-pro:
        modelId: "gemini-3-pro-preview"
        providerModelId: "gemini-3-pro-preview"
      gemini-flash:
        modelId: "gemini-2.0-flash"
        providerModelId: "gemini-2.0-flash"
```

**Available Models.corp Gemini models:**

| Model ID | Characteristics | Typical Use Cases |
|----------|----------------|-------------------|
| `gemini-2.0-flash` | Low-latency responses | Chatbots, mobile integrations |
| `gemini-2.5-pro` | Extended processing (10+ seconds) | Complex reasoning tasks |
| `gemini-3-pro-preview` | Latest generation | General AI tasks |

**Usage from client code:**

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="https://<your-llama-stack-route>")

response = client.responses.create(
    model="gemini-3-pro-preview",
    input="Explain Kubernetes pods",
    stream=True,
)
```

> **Note**: For the API key, use your Models.corp application credential exported as `GEMINI_API_KEY` before deploying with `envsubst`.
> Contact **#help-it-ai-platforms** for Models.corp access.

---

## Examples

### 1. RAG + MCP Chatbot

**[rag-mcp-chatbot](./examples/rag-mcp-chatbot/README.md)**

Interactive chatbot that combines RAG (Retrieval Augmented Generation) with MCP (Model Context Protocol) tools to interact with OpenShift/Kubernetes clusters. Allows asking questions about indexed documentation and executing cluster operations simultaneously.

```bash
cd examples/rag-mcp-chatbot
./run_example.sh
```

### 2. RAG Evaluation with RAGAS

**[rag-evaluation-ragas](./examples/rag-evaluation-ragas/README.md)**

Complete workflow to evaluate RAG systems using RAGAS metrics (answer_relevancy, faithfulness, context_precision, context_recall) through the Llama Stack SDK. Includes scripts to upload documents, generate datasets, and run automated evaluations.

```bash
cd examples/rag-evaluation-ragas
./run_example.sh
```
