# Error Report: RAGAS Remote Evaluation with LLS 0.5.x

**Date:** 2026-02-27
**Reporter:** David Severia
**Repository:** https://github.com/davidseve/llama-stack-example
**Branch:** `ragas-remote-v0.6` (commit `f0d43cc`)

---

## Environment

| Component | Version / Image |
|---|---|
| OpenShift | 4.20.6 (Kubernetes v1.33.5) |
| RHOAI Operator | 3.2.0 (`rhods-operator.3.2.0`) |
| LlamaStack Operator | `registry.redhat.io/rhoai/odh-llama-stack-k8s-operator-rhel9@sha256:5d36b0f49a03a0cf22f512809e5c9a4fdf0131cf1db8f0812d01e494d2d1f141` |
| LlamaStack Server Image | `docker.io/llamastack/distribution-starter:0.5.1` (llama-stack 0.5.1) |
| RAGAS Provider (desired) | `llama-stack-provider-ragas[remote]>=0.6.0` |
| DSPA | Deployed in `data-science-project` namespace |

---

## Objective

Test RAGAS remote evaluation (via Kubeflow Pipelines) using `llama-stack-provider-ragas>=0.6.0` with LlamaStack 0.5.x, deployed via the LlamaStack K8s Operator and the `LlamaStackDistribution` CRD.

---

## Error 1: External provider not installed in upstream image

### Description

The upstream image `docker.io/llamastack/distribution-starter:0.5.1` does **not** include `llama-stack-provider-ragas`. When the `run.yaml` references this provider via the `module` field, the server fails to start.

### Configuration (run.yaml excerpt)

```yaml
eval:
  - provider_id: trustyai_ragas_remote
    provider_type: remote::trustyai_ragas
    module: llama_stack_provider_ragas.remote
    config:
      embedding_model: sentence-transformers/ibm-granite/granite-embedding-125m-english
      kubeflow_config:
        results_s3_endpoint: http://minio.data-science-project.svc.cluster.local:9000
        results_s3_prefix: s3://mlpipeline/ragas-results
        results_s3_path_style: true
        s3_credentials_secret_name: minio-credentials
        pipelines_endpoint: http://ds-pipeline-dspa.data-science-project.svc.cluster.local:8888
        namespace: data-science-project
        llama_stack_url: http://llama-stack-example-service.llama-stack-example.svc.cluster.local:8321
        pipelines_api_token: ${env.KUBEFLOW_PIPELINES_TOKEN:=}
      kvstore:
        namespace: ragas_remote
        backend: kv_default
```

### Error logs

```
Detected llama-stack version: 0.5.1
Using uvicorn CLI command
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/llama_stack/core/distribution.py", line 240, in get_external_providers_from_module
    module = importlib.import_module(f"{package_name}.provider")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  ...
ModuleNotFoundError: No module named 'llama_stack_provider_ragas'

The above exception was the direct cause of the following exception:
  ...
ValueError: get_provider_spec not found. If specifying an external provider via `module` in the Provider spec, the Provider must have the `provider.get_provider_spec` module available
```

### Root cause

The `distribution-starter:0.5.1` image does not include `llama-stack-provider-ragas`. LLS 0.5.x dynamically imports external provider modules specified via the `module` field in `run.yaml`, but **does not install** them automatically.

### Workaround applied

Override the container `command`/`args` in the `LlamaStackDistribution` CRD to run `pip install` before starting the server:

```yaml
# In the LlamaStackDistribution containerSpec:
command:
  - /bin/sh
  - -c
args:
  - |
    pip install --quiet --no-cache-dir llama-stack-provider-ragas[remote]>=0.6.0 && \
    exec uvicorn llama_stack.core.server.server:create_app --host 0.0.0.0 --port "8321" --workers "1" --factory
```

---

## Error 2: KUBEFLOW_BASE_IMAGE operator default overrides run.yaml base_image (only visible after workaround 1)

### Description

After installing the RAGAS provider (workaround 1), the remote evaluation creates Kubeflow Pipeline runs. The KFP pipeline pods use a base image that the user configures via the `base_image` field in the RAGAS provider's `kubeflow_config` section of `run.yaml`:

```yaml
kubeflow_config:
  base_image: python:3.12-slim   # <-- user's desired image
```

However, the LlamaStack operator injects a `KUBEFLOW_BASE_IMAGE` environment variable into the server pod with a default value pointing to an outdated/non-existent `ragas-runner:latest` image. The RAGAS provider reads `KUBEFLOW_BASE_IMAGE` from the environment, and this operator-injected value **takes precedence over** the `base_image` configured in `run.yaml`.

### Error logs (from KFP pipeline pod)

```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: '/opt/app-root/lib/python3.12/site-packages/google/_async_resumable_media'
Check the permissions.
```

### Root cause

The operator's default `KUBEFLOW_BASE_IMAGE` env var overrides the user's `base_image` config and points to a UBI9 image where `/opt/app-root/lib/python3.12/site-packages/` is owned by root, causing `pip install` (run as non-root inside KFP pods via `packages_to_install`) to fail with permission errors.

### Workaround applied

Explicitly set `KUBEFLOW_BASE_IMAGE` as an environment variable in the `LlamaStackDistribution` CRD to match the user's desired `base_image`:

```yaml
- name: KUBEFLOW_BASE_IMAGE
  value: "python:3.12-slim"
```

### Expected behavior

The `base_image` field in `run.yaml` should be the source of truth. Either the operator should not inject `KUBEFLOW_BASE_IMAGE` (letting the provider use the config value), or the operator should read the value from the user's `run.yaml` config.

---

## Error 3: Missing AWS_DEFAULT_REGION in minio-credentials secret (only visible after workaround 1 & 2)

### Description

The KFP pipeline pods expect `AWS_DEFAULT_REGION` from the `minio-credentials` Kubernetes secret. If the secret only has `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, the pod fails with `CreateContainerConfigError`.

### Error (from `oc describe pod`)

```
Warning  Failed  kubelet  Error: couldn't find key AWS_DEFAULT_REGION in Secret data-science-project/minio-credentials
```

### Workaround applied

Add `AWS_DEFAULT_REGION: us-east-1` to the `minio-credentials` secret in the `data-science-project` namespace.

---

## Error 4: LLS server cannot read results from S3/MinIO (only visible after workarounds 1, 2 & 3)

### Description

After the KFP pipeline completes successfully, the RAGAS provider in the LLS server tries to read evaluation results from MinIO using `pd.read_json()` with `s3fs`/`boto3`. The server pod needs `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` environment variables to authenticate with MinIO, but they are not set by default.

### Error logs (from LLS server pod)

```
llama_stack_provider_ragas.errors.RagasEvaluationError: Run was successful, but failed to fetch results: Failed to fetch results from s3://mlpipeline/ragas-results/<job-id>/results.jsonl: Forbidden
```

### Workaround applied

Add AWS credentials as environment variables to the LLS server pod (either via Helm secret or `oc set env`).

---

## Questions for Engineering

1. **External provider installation**: The `distribution-starter` image doesn't include external providers. What is the recommended way to install `llama-stack-provider-ragas` in the LLS server pod? Is there a planned mechanism in the `LlamaStackDistribution` CRD (e.g., an `externalProviders` field)?

2. **KUBEFLOW_BASE_IMAGE**: The operator injects a default `KUBEFLOW_BASE_IMAGE` that is outdated. Can this default be updated to a working image (e.g., `python:3.12-slim`), or should the `base_image` field in the RAGAS provider config be the source of truth?

3. **AWS_DEFAULT_REGION in minio-credentials**: The RAGAS provider's KFP pipeline expects `AWS_DEFAULT_REGION` in the credentials secret. Should the provider handle the case where this key is missing (default to `us-east-1`)?

4. **S3 credentials for result fetching**: The LLS server needs S3 credentials to fetch results from MinIO. Should these be automatically derived from the `s3_credentials_secret_name` config, or is the user expected to mount them separately in the server pod?

5. **RHOAI image with LLS 0.5.x**: Is there a planned RHOAI image that includes LLS >=0.5.0 and pre-installed external providers? The current RHOAI images (`rhoai-v3.3-latest`) still ship LLS 0.4.2.1.

---

## Summary of Required Workarounds

| # | Issue | Workaround |
|---|---|---|
| 1 | External provider not installed in image | `pip install` via custom `command`/`args` in CRD |
| 2 | KUBEFLOW_BASE_IMAGE stale default | Explicit env var in CRD containerSpec |
| 3 | AWS_DEFAULT_REGION missing from secret | Manual secret patch |
| 4 | S3 credentials not available in LLS pod | Manual env var injection |

With all 4 workarounds applied, **RAGAS remote evaluation works successfully** (10/10 batches completed, metrics returned).
