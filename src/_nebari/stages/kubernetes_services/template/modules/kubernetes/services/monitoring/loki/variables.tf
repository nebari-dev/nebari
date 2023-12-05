variable "namespace" {
  description = "deploy monitoring services on this namespace"
  type        = string
  default     = "dev"
}


variable "loki-helm-chart-version" {
  description = "version to deploy for the loki helm chart"
  type        = string
}
