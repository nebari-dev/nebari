variable "name" {
  description = "Prefix name to assign to ingress kubernetes resources"
  type        = string
}

variable "environment" {
  description = "Kubernetes namespace to deploy ingress resources"
  type        = string
}
