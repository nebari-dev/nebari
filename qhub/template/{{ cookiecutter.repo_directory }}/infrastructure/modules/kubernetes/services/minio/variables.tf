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
