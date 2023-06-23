variable "name" {
  description = "Name prefix to deploy conda-store server"
  type        = string
  default     = "nebari"
}


variable "namespace" {
  description = "Namespace to deploy conda-store server"
  type        = string
}


variable "storage" {
  description = "Storage size for minio objects"
  type        = string
  default     = "10Gi"
}

variable "buckets" {
  description = "Default available buckets"
  type        = list(string)
  default     = []
}


variable "overrides" {
  description = "Minio helm chart list of overrides"
  type        = list(string)
  default     = []
}


variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}
