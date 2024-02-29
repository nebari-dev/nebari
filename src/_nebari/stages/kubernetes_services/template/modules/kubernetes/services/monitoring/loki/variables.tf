variable "namespace" {
  description = "deploy monitoring services on this namespace"
  type        = string
  default     = "dev"
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "loki-helm-chart-version" {
  description = "version to deploy for the loki helm chart"
  type        = string
  default     = "5.43.3"
}

variable "promtail-helm-chart-version" {
  description = "version to deploy for the promtail helm chart"
  type        = string
  default     = "6.15.5"
}

variable "overrides" {
  description = "Grafana Loki helm chart overrides"
  type        = list(string)
  default     = []
}
