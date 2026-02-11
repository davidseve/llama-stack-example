# MCP remote-access example (single cluster)

This example proves that the Kubernetes MCP server uses **only** the kubeconfig (remote identity) to call the Kubernetes API, not the in-cluster ServiceAccount.

## How it works

- The MCP pod runs in the cluster with a ServiceAccount bound to a **ClusterRole with no rules** (`mcp-no-permissions`), so in-cluster identity has no API access.
- A kubeconfig is mounted from a Secret, built from **kubeconfig.template.yaml** by substituting:
  - `__CLUSTER_SERVER__` → cluster API URL (auto-detected from `oc whoami --show-server`, e.g. `https://api.example.com:6443`)
  - `__TOKEN__` → token from the `mcp-remote` ServiceAccount (read-only view on the same cluster).
- If the MCP lists namespaces when called from outside (via the Route), it is using only the kubeconfig.

## Prerequisites

- `oc` logged in to the target OpenShift cluster.
- `helm` installed.
- `python3` and `curl` for the validation scripts.

## Quick run

From the **repository root**:

```bash
./examples/mcp-remote-access/run_example.sh
```

Optional environment variables:

- `NAMESPACE` – namespace for the MCP (default: `llama-stack-example`).
- `RELEASE_NAME` – Helm release name (default: `kubernetes-mcp`).
- `CLUSTER_API_URL` – cluster API URL for the kubeconfig (default: auto-detected via `oc whoami --show-server`).

The script will:

1. Apply RBAC and token manifests in the cluster.
2. Build the kubeconfig from **kubeconfig.template.yaml** (only host and token are filled).
3. Create the kubeconfig Secret and install/upgrade the MCP Helm chart with `kubeconfigSecret` and `rbac.clusterRole=mcp-no-permissions`.
4. Wait for the Route and run the validation scripts from outside.

## Files

- **kubeconfig.template.yaml** – Kubeconfig template; placeholders `__CLUSTER_SERVER__` and `__TOKEN__` are replaced by the script.
- **manifests/** – ClusterRole (no permissions), ServiceAccount `mcp-remote`, ClusterRole view, ClusterRoleBinding, token Secret.
- **scripts/validate-mcp-server.sh** – Checks HTTP 200 and lists namespaces via MCP.
- **scripts/mcp_list_namespaces.py** – Calls MCP tool `namespaces_list`.
- **scripts/test-mcp-remote-access.sh** – Asserts that validation passes (HTTP 200 + namespaces listed).

The generated kubeconfig file (`.kubeconfig.generated`) is temporary and not committed; it is removed after creating the Secret.
