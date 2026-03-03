{{/*
Expand the name of the chart.
*/}}
{{- define "tempo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "tempo.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Tempo service name - follows the operator convention: {name}-{name}-local
Used by Grafana datasource and OTEL collector to connect to Tempo.
*/}}
{{- define "tempo.serviceName" -}}
{{ .Values.tempo.name }}-{{ .Values.tempo.name }}-local
{{- end }}
