# Configuración para RAGAS Remote con DSPA

## Resumen

Este documento explica la configuración necesaria para que **llama-stack** pueda ejecutar evaluaciones RAGAS en modo **remote** usando **DSPA** (DataSciencePipelinesApplication) en Red Hat OpenShift AI.

**Referencia oficial**: [opendatahub-io/llama-stack-provider-ragas](https://github.com/opendatahub-io/llama-stack-provider-ragas/blob/main/demos/llama-stack-openshift/README.md)

## Arquitectura

```
┌─────────────────────────────┐      HTTP (port 8888)      ┌──────────────────────────────┐
│   llama-stack-example       │ ──────────────────────────▶│   data-science-project       │
│   namespace                 │                            │   namespace                  │
│                             │                            │                              │
│   ┌───────────────────┐    │                            │   ┌────────────────────┐    │
│   │  llama-stack pod  │    │                            │   │  ds-pipeline-dspa  │    │
│   │                   │    │                            │   │  (DSPA API Server) │    │
│   └───────────────────┘    │                            │   └────────────────────┘    │
└─────────────────────────────┘                            └──────────────────────────────┘
```

## El Problema: SSL Certificate Verification

Por defecto, DSPA expone su API a través de **HTTPS** en el puerto 8888, utilizando certificados firmados por el **OpenShift Service CA**. El provider `llama-stack-provider-ragas` hace llamadas `requests.get()` directas que no respetan `ssl_verify: false`, causando:

```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: 
self-signed certificate in certificate chain
```

## Solución: Deshabilitar podToPodTLS en DSPA

La solución más simple y recomendada es **deshabilitar TLS** entre los componentes de DSPA, forzando comunicación HTTP:

### Configuración en `charts/dspa/values.yaml`

```yaml
podToPodTLS: false  # Deshabilita TLS entre componentes DSPA
```

### Configuración en `gitops/llama-stack-values.yaml`

```yaml
kubeflow:
  # IMPORTANTE: Usar HTTP, no HTTPS
  pipelinesEndpoint: "http://ds-pipeline-dspa.data-science-project.svc.cluster.local:8888"
  sslVerify: false
```

> **Nota**: Con `podToPodTLS: false`, DSPA escucha en HTTP en el puerto 8888. Esto es seguro para comunicación intra-cluster.

## Solución SSL Alternativa (CA Bundle Job)

Si necesitas mantener HTTPS, puedes habilitar el CA Bundle Job:

```yaml
kubeflow:
  caBundleJob:
    enabled: true  # Crea combined-ca-bundle con Service CA
```

### Componentes del CA Bundle Job

1. **Service CA ConfigMap** - OpenShift inyecta el Service CA
2. **Combined CA Bundle** - Combina CAs públicas + Service CA
3. **Job PostSync** - Parchea el deployment

> **Nota**: El `odh-trusted-ca-bundle` es gestionado por CNO y se sobrescribe. Por eso usamos un ConfigMap separado.

## Archivos Involucrados

### Chart: `charts/llama-stack`

| Archivo | Propósito |
|---------|-----------|
| `templates/ca-bundle-job.yaml` | Job que combina CAs y parchea deployment |
| `templates/llamastack-distribution.yaml` | Define el LlamaStackDistribution CR |
| `conf/default-run.yaml` | Configuración del provider `trustyai_ragas_remote` |

### Chart: `charts/dspa`

| Archivo | Propósito |
|---------|-----------|
| `templates/dspa.yaml` | Define el DataSciencePipelinesApplication |
| `templates/networkpolicy.yaml` | Permite tráfico cross-namespace |
| `templates/route.yaml` | (Opcional) Expone DSPA externamente |

## Requisitos Previos

### 1. Token de Pipelines (OBLIGATORIO)

El service account de LlamaStack **no tiene privilegios** para crear pipeline runs. Debes proporcionar un token de usuario.

#### Opción A: Via GitOps (Recomendado)

Exporta el token antes de aplicar el appOfApps:

```bash
export LLAMA_4_SCOUT_API_TOKEN="<your_token>"
export KUBEFLOW_PIPELINES_TOKEN="$(oc whoami -t)"

envsubst < gitops/appOfApps.yaml | oc apply -f -
```

#### Opción B: Manualmente

```bash
# Añadir token al secret existente
oc patch secret llama-stack-example-secret -n llama-stack-example --type='json' \
  -p='[{"op": "add", "path": "/data/KUBEFLOW_PIPELINES_TOKEN", "value": "'$(echo -n "$(oc whoami -t)" | base64)'"}]'

# Reiniciar el pod para que tome el nuevo token
oc rollout restart deployment/llama-stack-example -n llama-stack-example
```

> ⚠️ **IMPORTANTE**: El token de usuario expira (~24h). Deberás renovarlo periódicamente.

### 2. URL Externa de Llama Stack (OBLIGATORIO)

La `llama_stack_url` **debe ser una ruta externa**, ya que los pods del pipeline necesitan acceder a Llama Stack desde fuera:

```yaml
kubeflow:
  # INCORRECTO - URL interna
  # llamaStackUrl: "http://llama-stack-example.llama-stack-example.svc.cluster.local:8321"
  
  # CORRECTO - Ruta externa
  llamaStackUrl: "https://llama-stack-example-llama-stack-example.apps.your-cluster.com"
```

## Configuración de Values

### `gitops/llama-stack-values.yaml`

```yaml
providers:
  kubeflow:
    enabled: true
    llamaStackUrl: "https://llama-stack-example-llama-stack-example.apps.your-cluster.com"  # Ruta externa
    pipelinesEndpoint: "http://ds-pipeline-dspa.data-science-project.svc.cluster.local:8888"  # HTTP, no HTTPS
    sslVerify: false
    namespace: "data-science-project"
    caBundleJob:
      enabled: false  # No necesario con podToPodTLS: false
```

### `charts/dspa/values.yaml`

```yaml
podToPodTLS: false  # IMPORTANTE: Deshabilita TLS para evitar problemas de certificados

networkPolicy:
  enabled: true   # Requerida para tráfico cross-namespace

apiServer:
  enableOauth: false  # Importante: permite acceso service-to-service
```

## NetworkPolicy

La NetworkPolicy es **necesaria** porque:

1. DSPA está en namespace `data-science-project`
2. llama-stack está en namespace `llama-stack-example`
3. OpenShift puede tener políticas de red por defecto que bloquean tráfico cross-namespace

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-llama-stack-to-dspa
  namespace: data-science-project
spec:
  podSelector:
    matchLabels:
      app: ds-pipeline-dspa
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: llama-stack-example
      ports:
        - port: 8888
        - port: 8887
```

## Route (Opcional)

La Route **NO es necesaria** para la configuración actual porque:

1. Usamos el servicio interno HTTPS
2. El CA bundle combinado incluye el Service CA
3. La comunicación es cluster-interna

Solo habilitar la Route si se necesita acceso externo a DSPA.

## Flujo de Despliegue (ArgoCD)

```
sync-wave 0-3: Operadores base (RHOAI)
     │
     ▼
sync-wave 4: MinIO (almacenamiento para pipelines)
     │
     ▼
sync-wave 5: llama-stack (crea LlamaStackDistribution)
     │
     ▼
sync-wave 10: DSPA (requiere CRD de RHOAI)
     │
     ▼
PostSync: CA Bundle Job
  1. Espera Service CA injection
  2. Combina system CAs + Service CA
  3. Crea combined-ca-bundle ConfigMap
  4. Parchea deployment
```

## Troubleshooting

### Error: SSL Certificate Verify Failed

Verifica que `podToPodTLS` esté deshabilitado y uses HTTP:

```bash
# Verificar podToPodTLS
oc get dspa dspa -n data-science-project -o jsonpath='{.spec.podToPodTLS}'
# Debe mostrar: false

# Verificar que usas HTTP en la configuración
oc get configmap llama-stack-example-config -n llama-stack-example \
  -o jsonpath='{.data.run\.yaml}' | grep pipelines_endpoint
# Debe mostrar: http:// (no https://)
```

### Error: Connection Timeout a DSPA

```bash
# Verificar NetworkPolicy existe
oc get networkpolicy allow-llama-stack-to-dspa -n data-science-project

# Probar conectividad desde llama-stack pod
POD=$(oc get pod -n llama-stack-example | grep llama-stack-example | grep Running | awk '{print $1}')
oc exec -n llama-stack-example $POD -c llama-stack -- \
  curl -s "http://ds-pipeline-dspa.data-science-project.svc.cluster.local:8888/apis/v2beta1/healthz"
```

### Error: Connection Reset by Peer

Esto indica que DSPA tiene OAuth habilitado:

```bash
# Verificar configuración de DSPA
oc get dspa dspa -n data-science-project -o yaml | grep enableOauth
# Debe ser: enableOauth: false
```

### Error: Token Expired / Unauthorized

El token de Kubeflow Pipelines expira (~24h):

```bash
# Renovar el token
oc patch secret llama-stack-example-secret -n llama-stack-example --type='json' \
  -p='[{"op": "replace", "path": "/data/KUBEFLOW_PIPELINES_TOKEN", "value": "'$(echo -n "$(oc whoami -t)" | base64)'"}]'

# Reiniciar para tomar el nuevo token
oc rollout restart deployment/llama-stack-example -n llama-stack-example
```

## Referencias

- [OpenShift Service CA Operator](https://docs.openshift.com/container-platform/latest/security/certificate_types_descriptions/service-ca-certificates.html)
- [OpenShift Network Policy](https://docs.openshift.com/container-platform/latest/networking/network_policy/about-network-policy.html)
- [RHOAI DataSciencePipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/)

