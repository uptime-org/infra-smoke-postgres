{{/*
Service name - use the chart name for uniqueness
*/}}
{{- define "service.name" -}}
{{ .Chart.Name }}
{{- end }}

{{/*
Service fullname - use chart name to ensure uniqueness in umbrella deployments
*/}}
{{- define "service.fullname" -}}
{{ .Chart.Name }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "service.labels" -}}
helm.sh/chart: {{ include "service.chart" . }}
{{ include "service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/team: {{ .Values.service.team }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "service.name" . }}
app.kubernetes.io/instance: {{ include "service.name" . }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "service.namespace" -}}
{{- default .Release.Namespace .Values.global.namespace }}
{{- end }}

{{/*
Generate comma-separated hostnames for external-dns
*/}}
{{- define "service.hostnames" -}}
{{- $global := .Values.global -}}
{{- range $index, $domain := .Values.dns.domains -}}
{{- if $index }},{{ end -}}
{{ $domain }}.{{ $global.domain }}
{{- end -}}
{{- end }}
