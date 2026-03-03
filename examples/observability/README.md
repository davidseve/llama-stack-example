# LlamaStack Observability

Complete observability stack for LlamaStack: **metrics**, **traces**, and **logs**.

## Architecture

```
                        ┌─────────────────────────────────────────┐
                        │           LlamaStack Pod                │
                        │  OTEL Python auto-instrumentation       │
                        └─────────────┬───────────────────────────┘
                                      │
                              OTLP push (metrics + traces)
                                      │
                                      ▼
                        ┌─────────────────────────────────┐
                        │     OTEL Collector              │
                        │  (charts/otel-collector)        │
                        │                                 │
                        │  otlp receiver                  │
                        │    ├── traces pipeline ──► otlp exporter ──► Tempo
                        │    └── metrics pipeline ──► prometheus exporter
                        │                                 │
                        └───────────┬─────────────────────┘
                                    │ /metrics (port 8889)
                                    │
                              Prometheus scrape
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │   Prometheus (UWM)      │
                        │   thanos-querier:9091   │
                        └───────────┬─────────────┘
                                    │
                                    ▼
                        ┌───────────────────────────────────────┐
                        │            Grafana                    │
                        │  (charts/grafana)                     │
                        │                                       │
                        │  DS: UWM Prometheus → token metrics   │
                        │  DS: Tempo          → traces          │
                        │                                       │
                        │  Dashboard: LlamaStack Metrics        │
                        │  Dashboard: LlamaStack Traces         │
                        └───────────────────────────────────────┘
```

## Quick Start

### Option 1: Full GitOps deployment (recommended)

```bash
# Deploy everything: operators, OTEL collector, Tempo, Grafana, LlamaStack telemetry
./examples/observability/run_example.sh --all
```

### Option 2: Step by step

```bash
# 1. Deploy via GitOps
./examples/observability/run_example.sh --deploy

# 2. Generate traffic + validate
./examples/observability/run_example.sh --test
```

### Option 3: Individual scripts

```bash
# Deploy only
./examples/observability/scripts/deploy_gitops.sh

# Generate 10 chat completions with llama-4-scout
./examples/observability/scripts/generate_traffic.sh

# Validate all components
./examples/observability/scripts/validate_all.sh
```

## Prerequisites

### Cluster requirements

| Component | How it's deployed | Chart |
|---|---|---|
| Grafana Operator | OLM Subscription via GitOps | `charts/operators` |
| Tempo Operator | OLM Subscription via GitOps | `charts/operators` |
| OpenTelemetry Operator | OLM Subscription via GitOps | `charts/operators` |
| User Workload Monitoring | ConfigMap via GitOps | `charts/operators` |

All operators are deployed automatically by the `operators` ArgoCD Application (sync wave -30).

### User requirements

- `oc` CLI logged in with cluster-admin privileges
- `examples/.env` configured with `REMOTE_BASE_URL` and `INFERENCE_MODEL_ID`

## Helm Charts

| Chart | Purpose | Sync Wave |
|---|---|---|
| `charts/operators` | OLM Subscriptions (Grafana, Tempo, OpenTelemetry operators) + UWM enablement | -30 |
| `charts/llama-stack` | LlamaStack with OTEL telemetry env vars (when `telemetry.enabled=true`) | 10 |
| `charts/otel-collector` | OpenTelemetryCollector CR (receives OTLP, exports to Tempo + Prometheus) | 12 |
| `charts/tempo` | TempoMonolithic CR (trace storage + Jaeger UI) | 15 |
| `charts/grafana` | Grafana CR + datasources + dashboards | 20 |

## GitOps Configuration

All observability components are controlled via `gitops/appOfApps.yaml`:

```yaml
applications:
  operators:
    enabled: true
    grafana: true
    tempo: true
    opentelemetry: true
    uwm: true
  otelCollector:
    enabled: true
  tempo:
    enabled: true
  grafana:
    enabled: true
```

LlamaStack telemetry is configured in `gitops/llama-stack-values.yaml`:

```yaml
providers:
  telemetry:
    enabled: true
    serviceName: "llama-stack-example"
    sinks: "otel"
    otlpEndpoint: "http://llama-stack-collector-collector:4318"
```

## Data Flow

1. **LlamaStack** generates metrics (token counters) and traces (inference spans) via the OTEL Python SDK
2. All telemetry is pushed via **OTLP HTTP** to the **OTEL Collector** (`llama-stack-collector-collector:4318`)
3. The collector **splits the signal**:
   - **Traces** are exported via OTLP to **Tempo** (`tempo-tempo:4317`)
   - **Metrics** are exposed as `/metrics` in Prometheus format on port 8889
4. **Prometheus** (User Workload Monitoring) scrapes the collector's `/metrics` endpoint via a `ServiceMonitor`
5. **Grafana** queries:
   - Prometheus (via thanos-querier) for metrics dashboards
   - Tempo for trace dashboards

## Testing Each Pillar

### Metrics

After generating traffic:

```bash
# Query Prometheus for LlamaStack token metrics
oc exec -n openshift-monitoring prometheus-k8s-0 -c prometheus -- \
  curl -s 'http://localhost:9090/api/v1/query?query=tokens_total{service_name="llama-stack-example"}'
```

In Grafana, open the **LlamaStack Metrics Dashboard** to see:
- Total/prompt/completion token counts
- Token processing rate over time
- Per-model token usage summary

### Traces

After generating traffic:

```bash
# Query Tempo directly
oc exec -n llama-stack-example deploy/tempo-tempo -- \
  curl -s "http://localhost:3200/api/search?limit=5"
```

Or open the **Jaeger UI** route for visual trace exploration:

```bash
oc get route tempo-jaegerui -n llama-stack-example -o jsonpath='https://{.spec.host}'
```

In Grafana, open the **LlamaStack Traces Dashboard** to see traces filtered by service name.

### Logs

LlamaStack logs are available via standard `oc logs`:

```bash
oc logs -n llama-stack-example deploy/llama-stack-example --tail=100
```

If LokiStack is installed, query centralized logs:

```bash
oc port-forward svc/logging-loki-gateway-http 3100:8080 -n openshift-logging &
curl -s -G "http://localhost:3100/api/logs/v1/application/loki/api/v1/query_range" \
  --data-urlencode 'query={kubernetes_namespace_name="llama-stack-example"} |= "llama-stack"' \
  --data-urlencode 'limit=10' \
  -H "Authorization: Bearer $(oc whoami -t)"
```

## Validation Script Output

Running `scripts/validate_all.sh` checks 8 categories:

```
[1/8] Operators        - CSVs for grafana-operator, tempo-product, opentelemetry-product
[2/8] UWM              - Running pods in openshift-user-workload-monitoring
[3/8] OTEL Collector   - Pod + service in namespace
[4/8] Tempo            - Pod + Jaeger UI route
[5/8] Grafana          - Pod + route accessibility + datasources + dashboards
[6/8] Metrics          - tokens_total query in Prometheus + ServiceMonitor
[7/8] Traces           - Search Tempo API for traces
[8/8] Logs             - Pod logs + OTEL env vars on LlamaStack pod
```

## Troubleshooting

| Issue | Check |
|---|---|
| Operator CSV not Succeeded | `oc get csv -A \| grep <operator>` -- check Events for install errors |
| UWM not starting | Verify `cluster-monitoring-config` ConfigMap: `oc get cm cluster-monitoring-config -n openshift-monitoring -o yaml` |
| OTEL Collector pod not starting | Check OpenTelemetry operator logs: `oc logs -n openshift-opentelemetry-operator deploy/opentelemetry-operator-controller-manager` |
| No metrics in Prometheus | 1. Check OTEL Collector pod logs for export errors 2. Check ServiceMonitor: `oc get servicemonitor -n llama-stack-example` 3. Verify UWM is scraping: check `prometheus-user-workload-*` pod targets |
| No traces in Tempo | 1. Check OTEL Collector pod logs 2. Verify Tempo pod: `oc get pods -l app.kubernetes.io/name=tempo` 3. Check LlamaStack `OTEL_EXPORTER_OTLP_ENDPOINT` env var |
| Grafana dashboards empty | 1. Check datasource connectivity (Grafana UI > Connections > Data sources > Save & Test) 2. Verify `servicePattern` matches `OTEL_SERVICE_NAME` 3. Wait 60s for metric export interval |
| ArgoCD sync stuck | Check Application status: `oc get application -n openshift-gitops`. For CRD-dependent resources, ensure `SkipDryRunOnMissingResource=true` |

## Known Limitations

- **vLLM dashboard**: Disabled by default (`vllm.enabled=false`) since llama-4-scout uses an external MAAS endpoint. Enable when using a local vLLM InferenceService.
- **RHOAI Prometheus datasource**: Disabled by default (`rhoaiPrometheus.enabled=false`). Enable in environments with the RHOAI monitoring stack in `redhat-ods-monitoring`.
- **LlamaStack streaming metrics**: LlamaStack telemetry only tracks non-streaming inference requests ([#3981](https://github.com/llamastack/llama-stack/issues/3981)).
