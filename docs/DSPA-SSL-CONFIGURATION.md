# Configuración SSL para DSPA (DataSciencePipelinesApplication)

## Resumen

Este documento explica la configuración necesaria para que **llama-stack** pueda comunicarse con **DSPA** (DataSciencePipelinesApplication) en Red Hat OpenShift AI, específicamente para el proveedor `trustyai_ragas_remote`.

## Arquitectura

```
┌─────────────────────────────┐     HTTPS (port 8888)     ┌──────────────────────────────┐
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

DSPA expone su API a través de HTTPS en el puerto 8888, utilizando certificados firmados por el **OpenShift Service CA** (Autoridad Certificadora interna de servicios).

Cuando `llama-stack` intenta conectar con DSPA, obtiene:

```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: 
self-signed certificate in certificate chain
```

### ¿Por qué ocurre?

1. El operador de LlamaStack configura `SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt`
2. Ese bundle contiene solo CAs públicas (Let's Encrypt, DigiCert, etc.)
3. El OpenShift Service CA **NO está incluido** en ese bundle
4. Por lo tanto, el certificado de DSPA no puede ser validado

## La Solución: Combined CA Bundle

### Componentes

1. **Service CA ConfigMap** (`llama-stack-example-service-ca`)
   - Anotación: `service.beta.openshift.io/inject-cabundle: "true"`
   - OpenShift inyecta automáticamente el Service CA

2. **Combined CA Bundle ConfigMap** (`combined-ca-bundle`)
   - Combina: `odh-trusted-ca-bundle` (CAs públicas) + Service CA
   - NO tiene la anotación de inject (evita ser sobrescrito por CNO)

3. **CA Bundle Job** (PostSync Hook de ArgoCD)
   - Combina los CAs
   - Crea/actualiza `combined-ca-bundle`
   - Parchea el deployment para usar el bundle combinado

### ¿Por qué no modificar `odh-trusted-ca-bundle`?

El ConfigMap `odh-trusted-ca-bundle` tiene la anotación:
```yaml
config.openshift.io/inject-trusted-cabundle: "true"
```

Esto hace que el **Cluster Network Operator (CNO)** lo gestione y sobrescriba cualquier modificación manual. Por eso creamos un ConfigMap separado.

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

## Configuración de Values

### `gitops/llama-stack-values.yaml`

```yaml
providers:
  kubeflow:
    enabled: true
    pipelinesEndpoint: "https://ds-pipeline-dspa.data-science-project.svc.cluster.local:8888"
    sslVerify: false  # La verificación real se hace via CA bundle
    namespace: "data-science-project"
    # ... otras configuraciones
```

### `charts/dspa/values.yaml`

```yaml
route:
  enabled: false  # No necesaria - usamos servicio interno

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

```bash
# Verificar que el combined-ca-bundle existe
oc get configmap combined-ca-bundle -n llama-stack-example

# Verificar que incluye Service CA
oc get configmap combined-ca-bundle -n llama-stack-example \
  -o jsonpath='{.data.ca-bundle\.crt}' | grep -c "BEGIN CERTIFICATE"
# Debería mostrar al menos 2

# Verificar que el pod usa el bundle correcto
oc get deployment llama-stack-example -n llama-stack-example -o yaml | \
  grep -A5 "volumes:" | grep "configMap"
```

### Error: Connection Timeout a DSPA

```bash
# Verificar NetworkPolicy existe
oc get networkpolicy allow-llama-stack-to-dspa -n data-science-project

# Probar conectividad desde llama-stack pod
POD=$(oc get pod -n llama-stack-example -l app=llama-stack -o name | head -1)
oc exec -n llama-stack-example $POD -- \
  curl -s "https://ds-pipeline-dspa.data-science-project.svc.cluster.local:8888/apis/v2beta1/healthz"
```

### Error: Connection Reset by Peer

Esto indica que DSPA tiene OAuth habilitado:

```bash
# Verificar configuración de DSPA
oc get dspa dspa -n data-science-project -o yaml | grep enableOauth
# Debe ser: enableOauth: false
```

## Referencias

- [OpenShift Service CA Operator](https://docs.openshift.com/container-platform/latest/security/certificate_types_descriptions/service-ca-certificates.html)
- [OpenShift Network Policy](https://docs.openshift.com/container-platform/latest/networking/network_policy/about-network-policy.html)
- [RHOAI DataSciencePipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/)

