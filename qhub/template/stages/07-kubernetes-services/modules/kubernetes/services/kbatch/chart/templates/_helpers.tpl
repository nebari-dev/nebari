{{/*
Expand the name of the chart.
*/}}
{{- define "kbatch-proxy.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "kbatch-proxy.fullname" -}}
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
{{- define "kbatch-proxy.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "kbatch-proxy.labels" -}}
helm.sh/chart: {{ include "kbatch-proxy.chart" . }}
{{ include "kbatch-proxy.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "kbatch-proxy.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kbatch-proxy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "kbatch-proxy.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kbatch-proxy.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{- /*
  kbatch-proxy.extraFiles.data:
    Renders content for a k8s Secret's data field, coming from extraFiles with
    binaryData entries. From zero-to-jupyterhub-k8s
*/}}
{{- define "kbatch-proxy.extraFiles.data.withNewLineSuffix" -}}
    {{- range $file_key, $file_details := . }}
        {{- include "kbatch-proxy.extraFiles.validate-file" (list $file_key $file_details) }}
        {{- if $file_details.binaryData }}
            {{- $file_key | quote }}: {{ $file_details.binaryData | nospace | quote }}{{ println }}
        {{- end }}
    {{- end }}
{{- end }}
{{- define "kbatch-proxy.extraFiles.data" -}}
    {{- include "kbatch-proxy.extraFiles.data.withNewLineSuffix" . | trimSuffix "\n" }}
{{- end }}

{{- /*
  kbatch-proxy.extraFiles.stringData:
    Renders content for a k8s Secret's stringData field, coming from extraFiles
    with either data or stringData entries.
*/}}
{{- define "kbatch-proxy.extraFiles.stringData.withNewLineSuffix" -}}
    {{- range $file_key, $file_details := . }}
        {{- include "kbatch-proxy.extraFiles.validate-file" (list $file_key $file_details) }}
        {{- $file_name := $file_details.mountPath | base }}
        {{- if $file_details.stringData }}
            {{- $file_key | quote }}: |
              {{- $file_details.stringData | trimSuffix "\n" | nindent 2 }}{{ println }}
        {{- end }}
        {{- if $file_details.data }}
            {{- $file_key | quote }}: |
              {{- if or (eq (ext $file_name) ".yaml") (eq (ext $file_name) ".yml") }}
              {{- $file_details.data | toYaml | nindent 2 }}{{ println }}
              {{- else if eq (ext $file_name) ".json" }}
              {{- $file_details.data | toJson | nindent 2 }}{{ println }}
              {{- else if eq (ext $file_name) ".toml" }}
              {{- $file_details.data | toToml | trimSuffix "\n" | nindent 2 }}{{ println }}
              {{- else }}
              {{- print "\n\nextraFiles entries with 'data' (" $file_key " > " $file_details.mountPath ") needs to have a filename extension of .yaml, .yml, .json, or .toml!" | fail }}
              {{- end }}
        {{- end }}
    {{- end }}
{{- end }}
{{- define "kbatch-proxy.extraFiles.stringData" -}}
    {{- include "kbatch-proxy.extraFiles.stringData.withNewLineSuffix" . | trimSuffix "\n" }}
{{- end }}

{{- define "kbatch-proxy.extraFiles.validate-file" -}}
    {{- $file_key := index . 0 }}
    {{- $file_details := index . 1 }}

    {{- /* Use of mountPath. */}}
    {{- if not ($file_details.mountPath) }}
        {{- print "\n\nextraFiles entries (" $file_key ") must contain the field 'mountPath'." | fail }}
    {{- end }}

    {{- /* Use one of stringData, binaryData, data. */}}
    {{- $field_count := 0 }}
    {{- if $file_details.data }}
        {{- $field_count = add1 $field_count }}
    {{- end }}
    {{- if $file_details.stringData }}
        {{- $field_count = add1 $field_count }}
    {{- end }}
    {{- if $file_details.binaryData }}
        {{- $field_count = add1 $field_count }}
    {{- end }}
    {{- if ne $field_count 1 }}
        {{- print "\n\nextraFiles entries (" $file_key ") must only contain one of the fields: 'data', 'stringData', and 'binaryData'." | fail }}
    {{- end }}
{{- end }}
