variable "name" {
  description = "helm deployment name"
  type        = string
  default     = "dev"
}

variable "namespace" {
  description = "deploy helm chart on this namespace"
  type        = string
  default     = "dev"
}

variable "repository" {
  description = "helm chart repository"
  type        = string
}

variable "chart" {
  description = "helm chart name in helm chart repository"
  type        = string
}

variable "chart_version" {
  description = "Helm chart version"
  type        = string
}

variable "overrides" {
  description = "Overrides for the helm chart values"
  type        = any
  default     = {}
}
