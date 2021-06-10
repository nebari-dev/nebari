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
