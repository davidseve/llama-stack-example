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

### 1. Configurar los valores

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

### 2. Instalar el chart

```bash
# Instalar con valores personalizados
helm install my-llamastack ./llama-stack-helm -f my-values.yaml

# O instalar con valores por defecto (requiere configurar secretos por separado)
helm install my-llamastack ./llama-stack-helm
```

### 3. Verificar la instalación

```bash
# Verificar el estado del release
helm status my-llamastack

# Ver los recursos creados
kubectl get llamastackdistribution -n rag
kubectl get configmap -n rag
kubectl get secret -n rag

# Ver logs del pod
kubectl logs -n rag -l app.kubernetes.io/name=llama-stack
```

## Configuración

### Estructura de valores principales

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|------------------|
| `llamastack.name` | Nombre del recurso LlamaStackDistribution | `lsd-llama-milvus` |
| `llamastack.namespace` | Namespace donde desplegar | `rag` |
| `llamastack.replicas` | Número de réplicas | `1` |
| `server.distribution.image` | Imagen de contenedor a usar | `quay.io/opendatahub/llama-stack:odh` |
| `server.storage.size` | Tamaño del almacenamiento | `5Gi` |

### Configuración de providers

La configuración de providers se define en `config.run.providers` y soporta:

- **inference**: Proveedores de inferencia (vLLM, etc.)
- **vector_io**: Bases de datos vectoriales (Milvus, etc.)
- **agents**: Proveedores de agentes
- **eval**: Proveedores de evaluación
- **datasetio**: Gestión de datasets
- **scoring**: Proveedores de puntuación
- **telemetry**: Observabilidad y telemetría
- **tool_runtime**: Herramientas externas

### Secretos

Los secretos se configuran en el formato:

```yaml
secret:
  name: llama-stack-inference-model-secret
  data:
    INFERENCE_MODEL: "<base64-encoded-value>"
    VLLM_URL: "<base64-encoded-value>"
    VLLM_TLS_VERIFY: "<base64-encoded-value>"
    VLLM_API_TOKEN: "<base64-encoded-value>"
```

Para codificar valores en base64:
```bash
echo -n "tu-valor-aquí" | base64
```

## Personalización avanzada

### Modificar la configuración de run.yaml

Puedes modificar completamente la configuración de LlamaStack editando los valores en `config.run`. Por ejemplo:

```yaml
config:
  run:
    providers:
      inference:
        - provider_id: custom-llm
          provider_type: remote::custom
          config:
            url: "https://my-custom-llm.example.com"
            api_key: "${env.CUSTOM_API_KEY}"
```

### Agregar variables de entorno adicionales

```yaml
server:
  containerSpec:
    env:
      customVariable: "custom-value"
      anotherSecret:
        secretName: my-other-secret
        key: MY_KEY
```

## Troubleshooting

### 1. El pod no inicia

Verificar los eventos del pod:
```bash
kubectl describe pod -n rag -l app.kubernetes.io/name=llama-stack
```

### 2. ConfigMap no se monta correctamente

Verificar que el ConfigMap existe:
```bash
kubectl get configmap -n rag <release-name>-config -o yaml
```

### 3. Secretos no configurados

Verificar que los secretos existen y tienen las claves correctas:
```bash
kubectl get secret -n rag llama-stack-inference-model-secret -o yaml
```

## Desinstalación

```bash
helm uninstall my-llamastack
```

## Contribución

Para contribuir a este chart:

1. Fork el repositorio
2. Realiza tus cambios
3. Ejecuta los tests: `helm lint .`
4. Crea un Pull Request

## Licencia

Este chart está bajo la misma licencia que el proyecto LlamaStack.
