# LlamaStack Observability

Complete observability stack for LlamaStack: **metrics**, **traces**, and **logs**.

## Architecture

```
                        ┌─────────────────────────────────────────┐
                        │           LlamaStack Pod                │
                        │  OTEL Python auto-instrumentation       │
                        └─────────────┬───────────────────────────┘
                                      │
                              OTLP push (traces)
                                      │
                                      ▼
                        ┌─────────────────────────────────┐
                        │     OTEL Collector              │
                        │  (charts/otel-collector)        │
                        │                                 │
                        │  otlp receiver                  │
                        │    ├── traces ──► otlp exporter ──► Tempo
                        │    │      └──► spanmetrics connector
                        │    │                  │
                        │    └── metrics ◄──────┘
                        │         └──► prometheus exporter
                        └───────────┬─────────────────────┘
                                    │ /metrics (port 8889)
                                    │
                              Prometheus scrape (ServiceMonitor)
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
                        │  DS: UWM Prometheus → span metrics    │
                        │  DS: Tempo          → traces          │
                        │                                       │
                        │  Dashboard: LlamaStack Metrics        │
                        │  Dashboard: LlamaStack Traces         │
                        └───────────────────────────────────────┘
```

## Deployment

The entire observability stack is deployed **via GitOps** using the appOfApps pattern.
No manual deployment steps are required.

Apply the root ArgoCD Application to deploy everything:

```bash
oc apply -f gitops/appOfApps.yaml
```

This automatically deploys (in order via sync waves):

| Sync Wave | Component | Chart |
|---|---|---|
| -30 | Operators (Grafana, Tempo, OpenTelemetry) + UWM | `charts/operators` |
| 10 | LlamaStack with OTEL telemetry | `charts/llama-stack` |
| 12 | OTEL Collector (with spanmetrics connector) | `charts/otel-collector` |
| 15 | Tempo (trace storage) | `charts/tempo` |
| 20 | Grafana (datasources + dashboards) | `charts/grafana` |

### GitOps Configuration

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

## Testing

```bash
# Generate traffic + validate all components
./examples/observability/run_example.sh --all

# Or step by step:
./examples/observability/run_example.sh --traffic     # Send requests to /v1/chat/completions + /v1/responses
./examples/observability/run_example.sh --validate    # Check operators, collector, Tempo, Grafana, metrics, traces

# Or individual scripts:
./examples/observability/scripts/generate_traffic.sh
./examples/observability/scripts/validate_all.sh
```

### Prerequisites

- `oc` CLI logged in with cluster-admin privileges
- `examples/.env` configured with `REMOTE_BASE_URL` and `INFERENCE_MODEL_ID`

## Data Flow

1. **LlamaStack** generates traces (inference spans) via the OTEL Python SDK
2. Traces are pushed via **OTLP HTTP** to the **OTEL Collector** (`llama-stack-collector-collector:4318`)
3. The collector processes the signal:
   - **Traces** are exported via OTLP to **Tempo** (`tempo-tempo:4317`)
   - **spanmetrics connector** derives metrics from traces (`traces_span_metrics_calls_total`, `traces_span_metrics_duration_milliseconds_*`)
   - **Metrics** are exposed as `/metrics` in Prometheus format on port 8889
4. **Prometheus** (User Workload Monitoring) scrapes the collector's `/metrics` endpoint via a `ServiceMonitor`
5. **Grafana** queries:
   - Prometheus (via thanos-querier) for the **LlamaStack Metrics Dashboard** (request rate, latency percentiles, error rate, endpoint performance)
   - Tempo for the **LlamaStack Traces Dashboard** (distributed traces with duration color-coding)

## Testing Each Pillar

### Metrics

After generating traffic:

```bash
# Query span-derived metrics from UWM Prometheus
oc exec -n openshift-user-workload-monitoring prometheus-user-workload-0 -c prometheus -- \
  curl -s 'http://localhost:9090/api/v1/query?query=traces_span_metrics_calls_total{service_name="llama-stack-example"}'
```

In Grafana, open the **LlamaStack Metrics Dashboard** to see:
- Total requests, error rate, avg latency, request rate
- Request rate over time by endpoint (`/v1/chat/completions`, `/v1/responses`)
- Latency percentiles (p50, p95, p99)
- Endpoint performance summary table
- OTEL Collector health (spans received/exported/failed)

### Traces

After generating traffic:

```bash
# Query Tempo from within the cluster
oc exec -n llama-stack-example deploy/llama-stack-example -- \
  python3 -c "import urllib.request,json; d=json.loads(urllib.request.urlopen('http://tempo-tempo:3200/api/search?limit=10').read()); [print(f'{t[\"rootTraceName\"]:40s} {t[\"durationMs\"]:>6}ms') for t in d['traces']]"
```

In Grafana, open **Explore > Tempo** to search and inspect individual traces (waterfall view, node graph), or the **LlamaStack Traces Dashboard** for an overview with color-coded duration.

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
[1/8] Operators        - CSVs for grafana-operator, tempo-operator, opentelemetry-operator
[2/8] UWM              - Running pods in openshift-user-workload-monitoring
[3/8] OTEL Collector   - Pod + service in namespace
[4/8] Tempo            - Pod + service
[5/8] Grafana          - Pod + route + datasources + dashboards
[6/8] Metrics          - traces_span_metrics_calls_total per endpoint (/v1/chat/completions, /v1/responses)
[7/8] Traces           - Tempo traces per endpoint (/v1/chat/completions, /v1/responses)
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
| Grafana dashboards empty | 1. Check datasource connectivity (Grafana UI > Connections > Data sources > Save & Test) 2. Verify `servicePattern` matches `OTEL_SERVICE_NAME` 3. Wait 60s for metric propagation |
| ArgoCD sync stuck | Check Application status: `oc get application -n openshift-gitops`. For CRD-dependent resources, ensure `SkipDryRunOnMissingResource=true` |

## Known Limitations

- **vLLM dashboard**: Disabled by default (`vllm.enabled=false`) since llama-4-scout uses an external MAAS endpoint. Enable when using a local vLLM InferenceService.
- **RHOAI Prometheus datasource**: Disabled by default (`rhoaiPrometheus.enabled=false`). Enable in environments with the RHOAI monitoring stack in `redhat-ods-monitoring`.
- **Metrics are derived from traces**: LlamaStack only pushes traces via OTLP. The `spanmetrics` connector in the OTEL Collector generates `traces_span_metrics_calls_total` and `traces_span_metrics_duration_milliseconds_*` from trace spans.
