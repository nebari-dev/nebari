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

variable "minio-helm-chart-version" {
  description = "version to deploy for the minio helm chart"
  type        = string
  default     = "6.7.4"
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

variable "grafana-loki-minio-overrides" {
  description = "Grafana Loki minio helm chart overrides"
  type        = list(string)
  default     = []
}

variable "minio-release-name" {
  description = "Grafana Loki minio release name"
  type        = string
  default     = "nebari-loki-minio"
}

variable "minio-port" {
  description = "Grafana Loki minio port"
  type        = number
  default     = 9000
}

variable "buckets" {
  description = "Minio buckets"
  type        = list(string)
  default = [
    "chunks",
    "ruler",
    "admin",
    "loki"
  ]
}

variable "minio-storage" {
  description = "Minio storage"
  type        = string
  default     = "50Gi"
}

variable "minio-enabled" {
  description = "Deploy minio along with loki or not"
  type        = bool
  default     = true
}

variable "node-group" {
  description = "Node key value pair for bound resources"
  type = object({
    key   = string
    value = string
  })
}
