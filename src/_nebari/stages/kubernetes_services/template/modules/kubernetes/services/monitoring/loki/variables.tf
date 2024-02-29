variable "namespace" {
  description = "deploy monitoring services on this namespace"
  type        = string
  default     = "dev"
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

variable "grafana-loki-overrides" {
  description = "Grafana Loki helm chart overrides"
  type        = list(string)
  default     = []
}

variable "grafana-promtail-overrides" {
  description = "Grafana Promtail helm chart overrides"
  type        = list(string)
  default     = []
}
