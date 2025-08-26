# LlamaStack Helm Chart

Este Helm chart despliega una instancia de LlamaStackDistribution en Kubernetes utilizando ConfigMaps para la configuración.

## Características

- **Configuración via ConfigMap**: La configuración del `run.yaml` se almacena en un ConfigMap, facilitando la gestión y actualización
- **Secretos parametrizados**: Las variables sensibles se gestionan mediante Secrets de Kubernetes
- **Totalmente parametrizable**: Todos los valores son configurables mediante `values.yaml`
- **Compatibilidad con OpenShift**: Diseñado para funcionar en entornos OpenShift y Kubernetes estándar

## Prerrequisitos

- Kubernetes 1.19+
- Helm 3.2.0+
- CRD de LlamaStackDistribution instalado en el cluster
- Namespace de destino creado (por defecto: `rag`)

## Instalación

### Configurar los valores

Antes de la instalación, necesitas configurar los secretos. Crea un archivo `my-values.yaml` con tus valores específicos:

```yaml
secret:
  data:
    # Valores codificados en base64
    INFERENCE_MODEL: "bWV0YS1sbGFtYS9MbGFtYS0zLjItM0ItSW5zdHJ1Y3Q="  # meta-llama/Llama-3.2-3B-Instruct
    VLLM_URL: "aHR0cHM6Ly9teS12bGxtLXNlcnZlci5leGFtcGxlLmNvbQ=="      # https://my-vllm-server.example.com
    VLLM_TLS_VERIFY: "ZmFsc2U="                                          # false
    VLLM_API_TOKEN: "bXktYXBpLXRva2VuLWhlcmU="                          # my-api-token-here

# Opcional: personalizar otros valores
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
