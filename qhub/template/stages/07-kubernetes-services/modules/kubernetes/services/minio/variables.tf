variable "name" {
  description = "Name prefix to deploy conda-store server"
  type        = string
  default     = "qhub"
}


variable "namespace" {
  description = "Namespace to deploy conda-store server"
  type        = string
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
