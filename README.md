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

2. (Optional) For guardrails with Granite Guardian, export the guardian token:
   ```bash
   export GRANITE_GUARDIAN_API_TOKEN="<your_guardian_token>"
   ```

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
- `envsubst` replaces `${LLAMA_4_SCOUT_API_TOKEN}`, `${GRANITE_GUARDIAN_API_TOKEN}`, and `${KUBEFLOW_PIPELINES_TOKEN}` before sending to `oc`.
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

### 3. Guardrails with Granite Guardian

**[guardrails-simple](./examples/guardrails-simple/README.md)**

Tests safety guardrails using **Granite Guardian 3.1 2B** as a direct safety model via Llama Stack's `inline::llama-guard` provider and the Responses API. No external orchestrator or detector services needed -- just the guardian model served as a vLLM endpoint.

Validates input/output safety checks for harmful content, jailbreak attempts, and passthrough behavior when guardrails are disabled.

```bash
cd examples/guardrails-simple
./run_example.sh
```

To enable guardrails on your deployment, set in your Helm values:

```yaml
guardrails:
  enabled: true
  guardianModelKey: "granite-guardian"  # must match a key in providers.vllm
```
