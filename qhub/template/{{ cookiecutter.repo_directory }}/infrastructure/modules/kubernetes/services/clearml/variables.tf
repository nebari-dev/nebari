variable "namespace" {
  description = "namespace to deploy clearml"
  type        = string
  default     = "dev"
}

variable "node_selector" {
  description = "Node to deploy on"
  default = {
    "app" = "clearml"
  }
}

variable "elasticsearch_image" {
  description = "Elasticsearch docker image"
  type        = string
  default     = "balast/elasticsearch:6_50"
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "tls" {
  description = "TLS configuration"
}

variable "enable-forward-auth" {
  type    = bool
  default = true
}
