#!/usr/bin/env bash
#
# MCP remote-access example: one cluster, MCP uses kubeconfig (token), in-cluster SA has no permissions.
# Prereqs: oc logged in to the cluster, namespace exists (or set NAMESPACE).
# Usage: from repo root: ./examples/mcp-remote-access/run_example.sh
#
set -e

EXAMPLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$EXAMPLE_DIR/../.." && pwd)"
NAMESPACE="${NAMESPACE:-llama-stack-example}"
RELEASE_NAME="${RELEASE_NAME:-kubernetes-mcp}"
CLUSTER_API_URL="${CLUSTER_API_URL:-$(oc whoami --show-server 2>/dev/null || echo "")}"
KUBECONFIG_GENERATED="$EXAMPLE_DIR/.kubeconfig.generated"

echo "=== MCP remote-access example ==="
echo "Namespace: $NAMESPACE  Release: $RELEASE_NAME  Cluster API: $CLUSTER_API_URL"
echo ""

# 1) Check oc login
oc whoami >/dev/null 2>&1 || { echo "ERROR: oc whoami failed. Log in to the cluster first." >&2; exit 1; }
[[ -n "$CLUSTER_API_URL" ]] || { echo "ERROR: Could not detect cluster API URL. Set CLUSTER_API_URL or log in with oc." >&2; exit 1; }

# 2) Ensure namespace exists
oc get namespace "$NAMESPACE" >/dev/null 2>&1 || oc create namespace "$NAMESPACE"

# 3) Apply manifests (ClusterRole no-permissions, mcp-remote SA + view role + binding + token secret)
echo "Applying manifests..."
oc apply -f "$EXAMPLE_DIR/manifests/01-clusterrole-no-permissions.yaml"
oc apply -f "$EXAMPLE_DIR/manifests/02-serviceaccount.yaml"
oc apply -f "$EXAMPLE_DIR/manifests/03-clusterrole-view.yaml"
oc apply -f "$EXAMPLE_DIR/manifests/04-clusterrolebinding.yaml"
oc apply -f "$EXAMPLE_DIR/manifests/05-token-secret.yaml"

# 4) Wait for token in Secret
echo "Waiting for token in mcp-remote-token Secret..."
for i in $(seq 1 30); do
  TOKEN=$(oc get secret mcp-remote-token -n default -o jsonpath='{.data.token}' 2>/dev/null | base64 -d 2>/dev/null || true)
  [[ -n "$TOKEN" ]] && break
  sleep 2
done
[[ -n "$TOKEN" ]] || { echo "ERROR: mcp-remote-token not populated in time" >&2; exit 1; }

# 5) Fill kubeconfig template (only host and token)
echo "Building kubeconfig from template..."
sed -e "s|__CLUSTER_SERVER__|$CLUSTER_API_URL|g" -e "s|__TOKEN__|$TOKEN|g" "$EXAMPLE_DIR/kubeconfig.template.yaml" > "$KUBECONFIG_GENERATED"
trap "rm -f '$KUBECONFIG_GENERATED'" EXIT

# 6) Create or replace Secret in namespace
oc get secret kubernetes-mcp-server-kubeconfig -n "$NAMESPACE" >/dev/null 2>&1 && oc delete secret kubernetes-mcp-server-kubeconfig -n "$NAMESPACE"
oc create secret generic kubernetes-mcp-server-kubeconfig --from-file=kubeconfig="$KUBECONFIG_GENERATED" -n "$NAMESPACE"

# 7) Helm upgrade --install with kubeconfig and mcp-no-permissions
echo "Installing/upgrading MCP chart..."
helm upgrade --install "$RELEASE_NAME" "$REPO_ROOT/charts/kubernetes-mcp-server" -n "$NAMESPACE" \
  -f "$EXAMPLE_DIR/values-override.yaml" \
  --set global.namespace="$NAMESPACE"

# 8) Wait for deployment and route
oc rollout status deployment/"$RELEASE_NAME-kubernetes-mcp-server" -n "$NAMESPACE" --timeout=120s 2>/dev/null || oc rollout status deployment/kubernetes-mcp-server -n "$NAMESPACE" --timeout=120s 2>/dev/null || true
echo "Waiting for route..."
ROUTE_NAME="$RELEASE_NAME-kubernetes-mcp-server"
for i in $(seq 1 30); do
  ROUTE_HOST=$(oc get route "$ROUTE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || oc get route -n "$NAMESPACE" -o jsonpath='{.items[0].spec.host}' 2>/dev/null || true)
  [[ -n "$ROUTE_HOST" ]] && break
  sleep 2
done
[[ -n "$ROUTE_HOST" ]] || { echo "ERROR: No route found in $NAMESPACE" >&2; exit 1; }
MCP_BASE_URL="https://$ROUTE_HOST"
echo "MCP Route: $MCP_BASE_URL"

# 9) Run validation from outside (test calls validate internally; only ONE SSE connection)
echo ""
echo "Running validation (from outside cluster)..."
"$EXAMPLE_DIR/scripts/test-mcp-remote-access.sh" "$MCP_BASE_URL" || { echo "Test failed" >&2; exit 1; }

echo ""
echo "=== Done: MCP remote-access example passed ==="
