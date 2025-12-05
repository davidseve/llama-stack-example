# LlamaStack Helm Chart

This Helm chart deploys a LlamaStackDistribution instance in Kubernetes using ConfigMaps for configuration.

## Features

- **ConfigMap-based configuration**: The `run.yaml` configuration is stored in a ConfigMap, making management and updates easier
- **Parameterized secrets**: Sensitive variables are managed through Kubernetes Secrets
- **Fully customizable**: All values are configurable through `values.yaml`
- **OpenShift compatibility**: Designed to work in both OpenShift and standard Kubernetes environments

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- LlamaStackDistribution CRD installed in the cluster
- Target namespace created (default: `rag`)

## Installation

### Configure the values

Before installation, you need to configure the secrets. Create a `my-values.yaml` file with your specific values:

```yaml
secret:
  data:
    # Base64-encoded values
    INFERENCE_MODEL: "bWV0YS1sbGFtYS9MbGFtYS0zLjItM0ItSW5zdHJ1Y3Q="  # meta-llama/Llama-3.2-3B-Instruct
    VLLM_URL: "aHR0cHM6Ly9teS12bGxtLXNlcnZlci5leGFtcGxlLmNvbQ=="      # https://my-vllm-server.example.com
    VLLM_TLS_VERIFY: "ZmFsc2U="                                          # false
    VLLM_API_TOKEN: "bXktYXBpLXRva2VuLWhlcmU="                          # my-api-token-here

# Optional: customize other values
llamastack:
  name: my-llamastack
  namespace: my-namespace
  replicas: 2

server:
  containerSpec:
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: "4"
        memory: 16Gi
```

## 🚀 Deployment with helm template + oc apply

### Basic deployment

```bash
# Deploy with default values
helm template llama-stack-example .  --values values-example.yaml | oc apply -f -
```
