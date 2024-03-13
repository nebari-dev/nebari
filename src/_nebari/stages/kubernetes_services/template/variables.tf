# Variables that are shared between multiple kubernetes services

variable "name" {
  description = "Prefix name to assign to kubernetes resources"
  type        = string
}

variable "environment" {
  description = "Kubernetes namespace to create resources within"
  type        = string
}

variable "endpoint" {
  description = "Endpoint for services"
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm id for creating clients"
  type        = string
}

variable "node_groups" {
  description = "Node group selectors for kubernetes resources"
  type = map(object({
    key   = string
    value = string
  }))
}

variable "jupyterhub-logout-redirect-url" {
  description = "Next redirect destination following a Keycloak logout"
  type        = string
  default     = ""
}

variable "conda-store-default-namespace" {
  description = "Default conda-store namespace name"
  type        = string
}

variable "argo-workflows-enabled" {
  description = "Enable Argo Workflows"
  type        = bool
}

variable "jupyterlab-pioneer-enabled" {
  description = "Enable JupyterLab Pioneer for telemetry"
  type        = bool
}

variable "jupyterlab-pioneer-log-format" {
  description = "Logging format for JupyterLab Pioneer"
  type        = string
}

variable "jhub-apps-enabled" {
  description = "Enable JupyterHub Apps"
  type        = bool
}

variable "cloud-provider" {
  description = "Name of cloud provider."
  type        = string
}

variable "grafana-loki-overrides" {
  description = "Helm chart overrides for loki"
  type        = list(string)
  default     = []
}

variable "grafana-promtail-overrides" {
  description = "Helm chart overrides for promtail"
  type        = list(string)
  default     = []
}

variable "grafana-loki-minio-overrides" {
  description = "Grafana Loki minio helm chart overrides"
  type        = list(string)
  default     = []
}

variable "minio-enabled" {
  description = "Deploy minio along with loki or not"
  type        = bool
  default     = true
}
