variable "namespace" {
  description = "deploy monitoring services on this namespace"
  type        = string
  default     = "dev"
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "tls" {
  description = "TLS configuration"
}
