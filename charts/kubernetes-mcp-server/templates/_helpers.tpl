{{/*
Expand the name of the chart.
*/}}
{{- define "kubernetes-mcp-server.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "kubernetes-mcp-server.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "kubernetes-mcp-server.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "kubernetes-mcp-server.labels" -}}
helm.sh/chart: {{ include "kubernetes-mcp-server.chart" . }}
{{ include "kubernetes-mcp-server.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "kubernetes-mcp-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kubernetes-mcp-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "kubernetes-mcp-server.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kubernetes-mcp-server.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the security context constraint to use
*/}}
{{- define "kubernetes-mcp-server.sccName" -}}
{{- if .Values.openshift.scc.create }}
{{- default (include "kubernetes-mcp-server.fullname" .) .Values.openshift.scc.name }}
{{- else }}
{{- .Values.openshift.scc.name }}
{{- end }}
{{- end }}

{{/*
OpenShift Route host
*/}}
{{- define "kubernetes-mcp-server.routeHost" -}}
{{- if .Values.openshift.route.host }}
{{- .Values.openshift.route.host }}
{{- else }}
{{- $shortName := .Release.Name | trunc 15 | trimSuffix "-" }}
{{- $namespace := include "kubernetes-mcp-server.namespace" . | trunc 15 | trimSuffix "-" }}
{{- printf "mcp-%s-%s.apps.your-cluster.com" $shortName $namespace }}
{{- end }}
{{- end }}

{{/*
Determine namespace to use
*/}}
{{- define "kubernetes-mcp-server.namespace" -}}
{{- if .Values.global.namespace }}
{{- .Values.global.namespace }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}
