## Instalación (MaaS)

Estos son los pasos de instalación usando MaaS.

### Pasar el token mediante una variable de entorno al aplicar con oc

Para parametrizar `VLLM_API_TOKEN` en `llama-stack-example/gitops/appOfApps.yaml`, usa la variable de entorno `${VLLM_API_TOKEN}`, que puedes sustituir en el momento de aplicar.

Pasos sugeridos:

1. Exporta tu token a una variable de entorno.
   ```bash
   export VLLM_API_TOKEN="<tu_token>"
   ```

2. Aplica el manifiesto usando `envsubst` y `oc apply`:
   ```bash
   envsubst < gitops/appOfApps.yaml | oc apply -f -
   ```

Notas:
- `envsubst` reemplaza `${VLLM_API_TOKEN}` antes de enviarlo a `oc`.
- Asegúrate de que el proyecto/namespace correcto esté configurado en el manifiesto, o usa `-n <namespace>` con `oc apply` si es necesario.

---

## Ejemplos

### 1. Chatbot RAG + MCP

**[examples/rag-mcp-chatbot](examples/rag-mcp-chatbot/)**

Chatbot interactivo que combina RAG (Retrieval Augmented Generation) con herramientas MCP (Model Context Protocol) para interactuar con clusters OpenShift/Kubernetes. Permite hacer preguntas sobre documentación indexada y ejecutar operaciones en el cluster simultáneamente.

```bash
cd examples/rag-mcp-chatbot
./run_example.sh
```

### 2. Evaluación RAG con RAGAS

**[examples/rag-evaluation-ragas](examples/rag-evaluation-ragas/)**

Workflow completo para evaluar sistemas RAG usando métricas RAGAS (answer_relevancy, faithfulness, context_precision, context_recall) a través del Llama Stack SDK. Incluye scripts para subir documentos, generar datasets y ejecutar evaluaciones automatizadas.

```bash
cd examples/rag-evaluation-ragas
./run_example.sh
```
