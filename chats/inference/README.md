# Inference Chart - Deployment Guide

This document describes how to deploy the `inference` Helm chart using `helm template` and `oc apply` on OpenShift.

## 📋 Prerequisites

Before starting, make sure you have installed:

- **OpenShift CLI (`oc`)** - v4.10+
- **Helm** - v3.8+
- Access to an OpenShift cluster with administrator permissions
- Access to GPU nodes (for the inference model)

## 🚀 Deployment with helm template + oc apply

### Basic deployment

```bash
# Deploy with default values
helm template llama-stack-example . | oc apply -f -
```

### Verify deployment

```bash
# Verify created resources
oc get all -n llama-stack-example

# Verify ServingRuntime
oc get servingruntime -n llama-stack-example

# Verify InferenceService
oc get inferenceservice -n llama-stack-example

# View detailed status
oc describe inferenceservice llama-stack-example -n llama-stack-example
```

